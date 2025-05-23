"""Reviewer agent implementation with GitHub integration.
Implements automated code review and GitHub branch management.
"""
import logging
import subprocess
from typing import Dict, List, Optional
from pathlib import Path
import json

from .base import BaseAgent
from ..models import Waypoint, LLMRequest
from ..exceptions import ToolingError

logger = logging.getLogger(__name__)

class ReviewerAgent(BaseAgent):
    """Reviews code changes and manages GitHub integration."""
    
    def __init__(self, llm_service, github_token: Optional[str] = None):
        super().__init__("Reviewer", llm_service)
        self.github_token = github_token
    
    def execute(self, context: Dict) -> Dict:
        """Execute code review and GitHub operations."""
        action = context.get("action", "review")
        
        if action == "review":
            return self._perform_code_review(context)
        elif action == "create_pr":
            return self._create_pull_request(context)
        elif action == "merge_pr":
            return self._merge_pull_request(context)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
    
    def _perform_code_review(self, context: Dict) -> Dict:
        """Review code changes using LLM."""
        waypoint = context.get("waypoint")
        code_changes = context.get("code_changes", {})
        project_context = context.get("project_context", "")
        
        # Build review prompt
        prompt = self._build_review_prompt(waypoint, code_changes, project_context)
        
        messages = [
            {"role": "system", "content": "You are an expert code reviewer. Review the code for bugs, security issues, performance, and best practices."},
            {"role": "user", "content": prompt}
        ]
        
        # Get LLM review
        response = self.call_llm(
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
            model=context.get("model")
        )
        
        try:
            review_result = json.loads(response.content)
            
            return {
                "success": True,
                "review": review_result,
                "approved": review_result.get("approved", False),
                "comments": review_result.get("comments", []),
                "suggestions": review_result.get("suggestions", []),
                "tokens_used": response.prompt_tokens + response.completion_tokens,
                "cost": response.cost
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Failed to parse review response",
                "raw_content": response.content,
                "tokens_used": response.prompt_tokens + response.completion_tokens,
                "cost": response.cost
            }
    
    def _create_pull_request(self, context: Dict) -> Dict:
        """Create a pull request on GitHub."""
        project_path = Path(context.get("project_path", "."))
        branch_name = context.get("branch_name", "feature/auto-generated")
        pr_title = context.get("pr_title", "Auto-generated code changes")
        pr_body = context.get("pr_body", "")
        
        try:
            # Create and push branch
            self._git_command(["checkout", "-b", branch_name], project_path)
            self._git_command(["add", "."], project_path)
            self._git_command(["commit", "-m", f"feat: {pr_title}"], project_path)
            self._git_command(["push", "origin", branch_name], project_path)
            
            # Create PR using GitHub CLI
            if self._is_gh_cli_available():
                result = subprocess.run(
                    ["gh", "pr", "create", 
                     "--title", pr_title,
                     "--body", pr_body,
                     "--base", "main",
                     "--head", branch_name],
                    cwd=project_path,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    pr_url = result.stdout.strip()
                    return {
                        "success": True,
                        "pr_url": pr_url,
                        "branch": branch_name
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to create PR: {result.stderr}"
                    }
            else:
                # Fallback: provide manual instructions
                return {
                    "success": True,
                    "branch": branch_name,
                    "manual": True,
                    "instructions": f"Branch '{branch_name}' pushed. Please create PR manually on GitHub."
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Git operation failed: {str(e)}"
            }
    
    def _merge_pull_request(self, context: Dict) -> Dict:
        """Merge a pull request after approval."""
        pr_number = context.get("pr_number")
        project_path = Path(context.get("project_path", "."))
        
        if not pr_number:
            return {"success": False, "error": "PR number required"}
        
        try:
            if self._is_gh_cli_available():
                # Check PR status
                status_result = subprocess.run(
                    ["gh", "pr", "view", str(pr_number), "--json", "state,mergeable"],
                    cwd=project_path,
                    capture_output=True,
                    text=True
                )
                
                if status_result.returncode == 0:
                    pr_info = json.loads(status_result.stdout)
                    
                    if pr_info.get("state") != "OPEN":
                        return {"success": False, "error": "PR is not open"}
                    
                    if not pr_info.get("mergeable"):
                        return {"success": False, "error": "PR has conflicts"}
                    
                    # Merge PR
                    merge_result = subprocess.run(
                        ["gh", "pr", "merge", str(pr_number), "--merge", "--delete-branch"],
                        cwd=project_path,
                        capture_output=True,
                        text=True
                    )
                    
                    if merge_result.returncode == 0:
                        return {"success": True, "message": "PR merged successfully"}
                    else:
                        return {"success": False, "error": merge_result.stderr}
                        
        except Exception as e:
            return {"success": False, "error": f"Merge operation failed: {str(e)}"}
    
    def _git_command(self, args: List[str], cwd: Path) -> subprocess.CompletedProcess:
        """Execute a git command."""
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result
    
    def _is_gh_cli_available(self) -> bool:
        """Check if GitHub CLI is available."""
        try:
            subprocess.run(["gh", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _build_review_prompt(self, waypoint, code_changes: Dict[str, str], 
                           project_context: str) -> str:
        """Build prompt for code review."""
        prompt = f"""### ROLE ###
You are an expert code reviewer. Review the following code changes for:
- Bugs and logical errors
- Security vulnerabilities
- Performance issues
- Code style and best practices
- Test coverage

### PROJECT CONTEXT ###
{project_context}

### WAYPOINT ###
{waypoint.description}

### CODE CHANGES ###
"""
        
        for file_path, content in code_changes.items():
            prompt += f"\n=== {file_path} ===\n{content}\n"
        
        prompt += """
### OUTPUT FORMAT ###
Provide a JSON object with:
- "approved": boolean (true if code is ready to merge)
- "comments": list of specific issues found
- "suggestions": list of improvement suggestions
- "security_concerns": list of security issues (if any)

Example:
{
  "approved": false,
  "comments": [
    {"file": "app.py", "line": 23, "issue": "Potential SQL injection", "severity": "high"}
  ],
  "suggestions": [
    "Add input validation for user data",
    "Consider using prepared statements"
  ],
  "security_concerns": ["SQL injection risk in database queries"]
}
"""
        return prompt