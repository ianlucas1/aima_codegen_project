"""Reviewer agent implementation with GitHub integration.
Implements automated code review and GitHub branch management.
"""
import logging
import subprocess
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json

from .base import BaseAgent
from ..models import Waypoint, LLMRequest
from ..exceptions import ToolingError

logger = logging.getLogger(__name__)

# Security patterns from REVIEWER.md
SECURITY_PATTERNS = {
    "sql_injection": [
        r"execute\s*\(\s*['\"].*%.*['\"]",  # String formatting in SQL
        r"cursor\.execute\s*\(\s*f['\"]",   # f-strings in SQL
        r"execute\s*\(\s*[\"'].*\+.*[\"']",  # String concatenation in SQL
    ],
    "path_traversal": [
        r"open\s*\(\s*.*\+.*\)",           # Path concatenation
        r"os\.path\.join\s*\(.*input",     # User input in paths
        r"open\s*\(\s*[^'\"]*input.*\)",   # Direct input in open
    ],
    "hardcoded_secrets": [
        r"password\s*=\s*['\"][^'\"]+['\"]",  # Hardcoded passwords
        r"api_key\s*=\s*['\"][^'\"]+['\"]",   # Hardcoded API keys
        r"secret\s*=\s*['\"][^'\"]+['\"]",    # Hardcoded secrets
        r"token\s*=\s*['\"][^'\"]+['\"]",     # Hardcoded tokens
    ],
    "command_injection": [
        r"os\.system\s*\(.*\+",              # Command injection via os.system
        r"subprocess\..*shell\s*=\s*True",   # Shell=True with user input
        r"eval\s*\(.*input",                 # eval with user input
        r"exec\s*\(.*input",                 # exec with user input
    ]
}

class ReviewerAgent(BaseAgent):
    """Reviews code changes and manages GitHub integration."""
    
    def __init__(self, llm_service, github_token: Optional[str] = None):
        super().__init__("Reviewer", llm_service)
        self.github_token = github_token
    
    def execute(self, context: Dict) -> Dict:
        """Execute code review and GitHub operations."""
        action = context.get("action", "review")
        decision_points = []
        
        # Track decision point: Action selection
        decision_points.append(self.track_decision_point(
            description="Review action selection",
            options=["review", "create_pr", "merge_pr"],
            chosen=action,
            reasoning=f"Executing {action} based on orchestrator request"
        ))
        
        if action == "review":
            return self._perform_code_review(context, decision_points)
        elif action == "create_pr":
            return self._create_pull_request(context)
        elif action == "merge_pr":
            return self._merge_pull_request(context)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
    
    def _perform_code_review(self, context: Dict, decision_points: List[Dict]) -> Dict:
        """Review code changes using LLM."""
        waypoint = context.get("waypoint")
        code_changes = context.get("code_changes", {})
        project_context = context.get("project_context", "")
        
        # Track decision point: Review strategy
        num_files = len(code_changes)
        total_lines = sum(len(content.split('\n')) for content in code_changes.values())
        strategy = "comprehensive" if total_lines > 100 else "focused"
        decision_points.append(self.track_decision_point(
            description="Review depth strategy",
            options=["comprehensive", "focused", "quick"],
            chosen=strategy,
            reasoning=f"Reviewing {num_files} files with {total_lines} total lines"
        ))
        
        # Perform security analysis first
        security_issues = self._analyze_security_patterns(code_changes)
        
        # Perform quality assessment
        quality_issues = self._assess_code_quality(code_changes)
        
        # Track decision point: Security vs quality priority
        has_security_issues = len(security_issues) > 0
        decision_points.append(self.track_decision_point(
            description="Review priority focus",
            options=["security-first", "quality-first", "balanced"],
            chosen="security-first" if has_security_issues else "quality-first",
            reasoning=f"Found {len(security_issues)} security issues and {len(quality_issues)} quality issues"
        ))
        
        # Build review prompt
        prompt = self._build_review_prompt(waypoint, code_changes, project_context, 
                                         security_issues, quality_issues)
        
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
        
        confidence_level = 0.85  # High confidence for code review
        result = None
        
        try:
            review_result = json.loads(response.content)
            
            # Merge our security and quality findings with LLM results
            all_comments = review_result.get("comments", [])
            all_comments.extend([{
                "file": issue["file"],
                "line": issue["line"],
                "issue": issue["description"],
                "severity": issue["severity"]
            } for issue in security_issues])
            
            all_suggestions = review_result.get("suggestions", [])
            all_suggestions.extend([issue["suggestion"] for issue in quality_issues if "suggestion" in issue])
            
            # Track decision point: Approval decision
            approved = review_result.get("approved", False) and len(security_issues) == 0
            decision_points.append(self.track_decision_point(
                description="Code approval decision",
                options=["approve", "request-changes", "comment-only"],
                chosen="approve" if approved else "request-changes",
                reasoning=f"LLM approved: {review_result.get('approved')}, Security issues: {len(security_issues)}"
            ))
            
            confidence_level = 0.9 if approved else 0.7
            
            result = {
                "success": True,
                "review": review_result,
                "approved": approved,
                "comments": all_comments,
                "suggestions": all_suggestions,
                "security_concerns": review_result.get("security_concerns", []) + [issue["description"] for issue in security_issues],
                "tokens_used": response.prompt_tokens + response.completion_tokens,
                "cost": response.cost
            }
        except json.JSONDecodeError:
            confidence_level = 0.3  # Low confidence due to parsing failure
            result = {
                "success": False,
                "error": "Failed to parse review response",
                "raw_content": response.content,
                "tokens_used": response.prompt_tokens + response.completion_tokens,
                "cost": response.cost
            }
        
        # Log comprehensive telemetry
        self.log_agent_telemetry(
            context=context,
            llm_response=response,
            result=result,
            decision_points=decision_points,
            confidence_level=confidence_level
        )
        
        # Generate post-task debrief
        debrief = self.generate_debrief(
            context=context,
            result=result,
            decision_points=decision_points,
            confidence_level=confidence_level
        )
        
        return result
    
    def _analyze_security_patterns(self, code_changes: Dict[str, str]) -> List[Dict]:
        """Analyze code for security anti-patterns."""
        issues = []
        
        for file_path, content in code_changes.items():
            lines = content.split('\n')
            for pattern_type, patterns in SECURITY_PATTERNS.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            "file": file_path,
                            "line": line_num,
                            "type": pattern_type,
                            "severity": "high",
                            "description": f"Potential {pattern_type.replace('_', ' ')} vulnerability",
                            "match": match.group(0)[:50] + "..." if len(match.group(0)) > 50 else match.group(0)
                        })
        
        return issues
    
    def _assess_code_quality(self, code_changes: Dict[str, str]) -> List[Dict]:
        """Assess overall code quality metrics."""
        suggestions = []
        
        for file_path, content in code_changes.items():
            # Function length check
            functions = self._extract_functions(content)
            for func_name, func_lines in functions:
                if func_lines > 50:
                    suggestions.append({
                        "file": file_path,
                        "function": func_name,
                        "issue": f"Function too long ({func_lines} lines)",
                        "suggestion": "Consider breaking into smaller functions",
                        "severity": "medium"
                    })
            
            # Complexity analysis (simplified McCabe complexity)
            complexity_score = self._calculate_complexity(content)
            if complexity_score > 10:
                suggestions.append({
                    "file": file_path,
                    "issue": f"High cyclomatic complexity ({complexity_score})",
                    "suggestion": "Simplify control flow and reduce nesting",
                    "severity": "medium"
                })
            
            # Documentation check
            missing_docs = self._find_missing_docstrings(content)
            for item in missing_docs:
                suggestions.append({
                    "file": file_path,
                    "item": item,
                    "issue": "Missing docstring",
                    "suggestion": "Add comprehensive docstring",
                    "severity": "low"
                })
        
        return suggestions
    
    def _extract_functions(self, content: str) -> List[Tuple[str, int]]:
        """Extract function names and their line counts."""
        functions = []
        lines = content.split('\n')
        
        in_function = False
        func_name = ""
        func_start = 0
        indent_level = 0
        
        for i, line in enumerate(lines):
            if re.match(r'^def\s+(\w+)\s*\(', line):
                if in_function:
                    # End previous function
                    functions.append((func_name, i - func_start))
                
                match = re.match(r'^def\s+(\w+)\s*\(', line)
                func_name = match.group(1)
                func_start = i
                in_function = True
                indent_level = len(line) - len(line.lstrip())
            elif in_function and line.strip() and (len(line) - len(line.lstrip())) <= indent_level:
                # Function ended
                functions.append((func_name, i - func_start))
                in_function = False
        
        if in_function:
            functions.append((func_name, len(lines) - func_start))
        
        return functions
    
    def _calculate_complexity(self, content: str) -> int:
        """Calculate simplified cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        # Count decision points
        patterns = [
            r'\bif\b', r'\belif\b', r'\bfor\b', r'\bwhile\b',
            r'\band\b', r'\bor\b', r'\btry\b', r'\bexcept\b'
        ]
        
        for pattern in patterns:
            complexity += len(re.findall(pattern, content))
        
        return complexity
    
    def _find_missing_docstrings(self, content: str) -> List[str]:
        """Find functions and classes missing docstrings."""
        missing = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if re.match(r'^(def|class)\s+(\w+)', line):
                match = re.match(r'^(def|class)\s+(\w+)', line)
                item_type = match.group(1)
                item_name = match.group(2)
                
                # Check next few lines for docstring
                has_docstring = False
                for j in range(i + 1, min(i + 5, len(lines))):
                    if '"""' in lines[j] or "'''" in lines[j]:
                        has_docstring = True
                        break
                    elif lines[j].strip() and not lines[j].strip().startswith('#'):
                        break
                
                if not has_docstring:
                    missing.append(f"{item_type} {item_name}")
        
        return missing
    
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
                           project_context: str, security_issues: List[Dict], 
                           quality_issues: List[Dict]) -> str:
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
        
        # Add security issues found by pattern matching
        if security_issues:
            prompt += "\n### SECURITY ISSUES DETECTED ###\n"
            for issue in security_issues:
                prompt += f"- {issue['file']} (line {issue['line']}): {issue['description']}\n"
        else:
            prompt += "\n### SECURITY ISSUES DETECTED ###\nNo security patterns detected.\n"
        
        # Add quality issues found
        if quality_issues:
            prompt += "\n### QUALITY ISSUES DETECTED ###\n"
            for issue in quality_issues:
                prompt += f"- {issue['file']}: {issue['issue']}\n"
        else:
            prompt += "\n### QUALITY ISSUES DETECTED ###\nNo quality issues detected.\n"
        
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