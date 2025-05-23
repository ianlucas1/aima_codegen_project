"""Virtual environment management.
Implements spec_v5.1.md Section 5.1.1 - Python Virtual Environment Management
"""
import os
import sys
import subprocess
import shutil
import logging
from pathlib import Path
from typing import Optional, Tuple
import hashlib

from .config import config
from .exceptions import ToolingError

logger = logging.getLogger(__name__)

class VEnvManager:
    """Manages project-specific Python virtual environments."""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.venv_path = project_path / ".venv"
        self.src_path = project_path / "src"
        self.requirements_path = self.src_path / "requirements.txt"
    
    def find_python(self) -> str:
        """Find suitable Python interpreter.
        Implements spec_v5.1.md Section 5.1.1 - Python Path Discovery
        """
        # Check config first
        config_python = config.get("VEnv", "python_path", "")
        if config_python and self._verify_python_version(config_python):
            return config_python
        
        # Search system PATH in order
        candidates = ["python3.12", "python3.11", "python3.10", "python3"]
        best_python = None
        best_version = None
        
        for candidate in candidates:
            python_path = shutil.which(candidate)
            if python_path:
                version = self._get_python_version(python_path)
                if version and version >= (3, 10):
                    if best_version is None or version > best_version:
                        best_python = python_path
                        best_version = version
        
        if best_python:
            return best_python
        
        # Fatal error if no suitable Python found
        raise RuntimeError(
            "FATAL_ERROR: Could not find a suitable Python interpreter (3.10+). "
            "Please set the path in config.ini or ensure it's in your PATH."
        )
    
    def _verify_python_version(self, python_path: str) -> bool:
        """Verify Python version meets requirements."""
        version = self._get_python_version(python_path)
        return version is not None and version >= (3, 10)
    
    def _get_python_version(self, python_path: str) -> Optional[Tuple[int, int, int]]:
        """Get Python version tuple from interpreter."""
        try:
            result = subprocess.run(
                [python_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Parse "Python 3.10.5" format
                version_str = result.stdout.strip().split()[1]
                parts = version_str.split('.')
                return (int(parts[0]), int(parts[1]), int(parts[2]))
        except Exception as e:
            logger.debug(f"Failed to get version for {python_path}: {e}")
        return None
    
    def create_venv(self, python_path: str):
        """Create virtual environment.
        Implements spec_v5.1.md Section 5.1.1 - VEnv Creation
        """
        logger.info(f"Creating virtual environment at {self.venv_path}")
        
        try:
            result = subprocess.run(
                [python_path, "-m", "venv", str(self.venv_path)],
                capture_output=True,
                text=True,
                check=False,
                timeout=60
            )
            
            if result.returncode != 0:
                raise ToolingError(
                    f"Failed to create virtual environment. "
                    f"Command: {' '.join([python_path, '-m', 'venv', str(self.venv_path)])} "
                    f"Exit code: {result.returncode} "
                    f"Stdout: {result.stdout} "
                    f"Stderr: {result.stderr}"
                )
            
            # Verify creation
            venv_python = self.get_venv_python()
            if not venv_python.exists():
                raise ToolingError(f"Virtual environment creation failed - Python not found at {venv_python}")
                
        except subprocess.TimeoutExpired:
            raise ToolingError("Virtual environment creation timed out after 60 seconds")
    
    def get_venv_python(self) -> Path:
        """Get path to Python interpreter in venv."""
        # macOS uses bin/python
        return self.venv_path / "bin" / "python"
    
    def install_requirements(self, requirements_hash: Optional[str] = None) -> str:
        """Install requirements and return new hash.
        Implements spec_v5.1.md Section 5.1.1 - Dependency Installation
        """
        if not self.requirements_path.exists():
            # Create empty requirements.txt if it doesn't exist
            self.requirements_path.write_text("")
            return self._compute_requirements_hash()
        
        current_hash = self._compute_requirements_hash()
        
        # Check if installation needed
        if requirements_hash and requirements_hash == current_hash:
            logger.debug("Requirements unchanged, skipping installation")
            return current_hash
        
        logger.info("Installing project requirements")
        venv_python = str(self.get_venv_python())
        pip_timeout = config.get("VEnv", "pip_timeout", 300)
        
        try:
            result = subprocess.run(
                [venv_python, "-m", "pip", "install", "-r", str(self.requirements_path)],
                capture_output=True,
                text=True,
                check=False,
                timeout=pip_timeout
            )
            
            if result.returncode != 0:
                raise ToolingError(
                    f"Failed to install requirements. "
                    f"Command: {venv_python} -m pip install -r {self.requirements_path} "
                    f"Exit code: {result.returncode} "
                    f"Stdout: {result.stdout} "
                    f"Stderr: {result.stderr}"
                )
                
        except subprocess.TimeoutExpired:
            raise ToolingError(f"pip install timed out after {pip_timeout} seconds")
        
        return current_hash
    
    def _compute_requirements_hash(self) -> str:
        """Compute SHA256 hash of requirements.txt."""
        if not self.requirements_path.exists():
            return ""
        content = self.requirements_path.read_text()
        return hashlib.sha256(content.encode()).hexdigest()
    
    def run_subprocess(self, cmd: list, timeout: int = 60) -> subprocess.CompletedProcess:
        """Run subprocess in venv context.
        Implements spec_v5.1.md Section 5.1.1 - subprocess execution requirements
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout,
                cwd=self.src_path  # Run in src directory
            )
            
            if result.returncode != 0:
                logger.error(
                    f"Command failed: {' '.join(cmd)} "
                    f"Exit code: {result.returncode} "
                    f"Stdout: {result.stdout} "
                    f"Stderr: {result.stderr}"
                )
            
            return result
            
        except subprocess.TimeoutExpired:
            raise ToolingError(f"Command timed out after {timeout} seconds: {' '.join(cmd)}")