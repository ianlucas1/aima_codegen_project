"""GitHub integration for AIMA CodeGen.
Provides GitHub API integration for automated PR management.
"""
import os
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
import subprocess

try:
    import requests
except ImportError:
    requests = None

from ..config import config
from ..exceptions import ToolingError

logger = logging.getLogger(__name__)

class GitHubIntegration:
    """Manages GitHub integration for code review and PR management."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or self._get_github_token()
        self.api_base = "https://api.github.com"
        self.session = None
        if requests and self.token:
            self.session = requests.Session()
            self.session.headers.update({
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            })
    
    def _get_github_token(self) -> Optional[str]:
        """Get GitHub token from environment or config."""
        # Check environment variable first
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            return token
        
        # Check config
        token = config.get("GitHub", "token")
        if token:
            return token
        
        # Check keychain
        try:
            import keyring
            service_name = config.get("Security", "keychain_service_name", "AIMA_CodeGen_Keys")
            token = keyring.get_password(service_name, "github")
            if token:
                return token
        except Exception:
            pass
        
        return None
    
    def create_pull_request(self, repo: str, title: str, body: str, 
                          head: str, base: str = "main") -> Dict:
        """Create a pull request via GitHub API."""
        if not self.session:
            raise ToolingError("GitHub token not configured")
        
        url = f"{self.api_base}/repos/{repo}/pulls"
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }
        
        response = self.session.post(url, json=data)
        
        if response.status_code == 201:
            pr_data = response.json()
            return {
                "success": True,
                "number": pr_data["number"],
                "url": pr_data["html_url"],
                "id": pr_data["id"]
            }
        else:
            return {
                "success": False,
                "error": response.json().get("message", "Unknown error"),
                "status_code": response.status_code
            }
    
    def get_pull_request(self, repo: str, pr_number: int) -> Dict:
        """Get pull request details."""
        if not self.session:
            raise ToolingError("GitHub token not configured")
        
        url = f"{self.api_base}/repos/{repo}/pulls/{pr_number}"
        response = self.session.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise ToolingError(f"Failed to get PR: {response.status_code}")
    
    def merge_pull_request(self, repo: str, pr_number: int, 
                         merge_method: str = "merge") -> Dict:
        """Merge a pull request."""
        if not self.session:
            raise ToolingError("GitHub token not configured")
        
        url = f"{self.api_base}/repos/{repo}/pulls/{pr_number}/merge"
        data = {
            "merge_method": merge_method  # "merge", "squash", or "rebase"
        }
        
        response = self.session.put(url, json=data)
        
        if response.status_code == 200:
            return {
                "success": True,
                "sha": response.json()["sha"],
                "message": response.json()["message"]
            }
        else:
            return {
                "success": False,
                "error": response.json().get("message", "Unknown error"),
                "status_code": response.status_code
            }
    
    def create_issue_comment(self, repo: str, issue_number: int, body: str) -> Dict:
        """Add a comment to an issue or PR."""
        if not self.session:
            raise ToolingError("GitHub token not configured")
        
        url = f"{self.api_base}/repos/{repo}/issues/{issue_number}/comments"
        data = {"body": body}
        
        response = self.session.post(url, json=data)
        
        if response.status_code == 201:
            return {"success": True, "id": response.json()["id"]}
        else:
            return {"success": False, "error": response.json().get("message")}
    
    def get_pr_files(self, repo: str, pr_number: int) -> List[Dict]:
        """Get list of files changed in a PR."""
        if not self.session:
            raise ToolingError("GitHub token not configured")
        
        url = f"{self.api_base}/repos/{repo}/pulls/{pr_number}/files"
        response = self.session.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise ToolingError(f"Failed to get PR files: {response.status_code}")
    
    def setup_webhook(self, repo: str, url: str, events: List[str]) -> Dict:
        """Set up a webhook for PR events."""
        if not self.session:
            raise ToolingError("GitHub token not configured")
        
        webhook_url = f"{self.api_base}/repos/{repo}/hooks"
        data = {
            "name": "web",
            "active": True,
            "events": events,
            "config": {
                "url": url,
                "content_type": "json"
            }
        }
        
        response = self.session.post(webhook_url, json=data)
        
        if response.status_code == 201:
            return {"success": True, "id": response.json()["id"]}
        else:
            return {"success": False, "error": response.json().get("message")}


class GitOperations:
    """Local git operations helper."""
    
    @staticmethod
    def init_repo(project_path: Path) -> bool:
        """Initialize git repository if not exists."""
        git_dir = project_path / ".git"
        if not git_dir.exists():
            try:
                subprocess.run(["git", "init"], cwd=project_path, check=True)
                return True
            except subprocess.CalledProcessError:
                return False
        return True
    
    @staticmethod
    def create_branch(project_path: Path, branch_name: str) -> bool:
        """Create and checkout a new branch."""
        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name], 
                cwd=project_path, 
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    @staticmethod
    def commit_changes(project_path: Path, message: str, files: List[str] = None) -> bool:
        """Stage and commit changes."""
        try:
            # Stage files
            if files:
                subprocess.run(["git", "add"] + files, cwd=project_path, check=True)
            else:
                subprocess.run(["git", "add", "."], cwd=project_path, check=True)
            
            # Commit
            subprocess.run(
                ["git", "commit", "-m", message], 
                cwd=project_path, 
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    @staticmethod
    def push_branch(project_path: Path, branch_name: str, remote: str = "origin") -> bool:
        """Push branch to remote."""
        try:
            subprocess.run(
                ["git", "push", remote, branch_name],
                cwd=project_path,
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    @staticmethod
    def get_current_branch(project_path: Path) -> Optional[str]:
        """Get current branch name."""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
    
    @staticmethod
    def get_remote_url(project_path: Path, remote: str = "origin") -> Optional[str]:
        """Get remote repository URL."""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", remote],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None