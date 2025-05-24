import os
import sys
from pathlib import Path
from typing import Optional

class SymlinkAwarePathResolver:
    """Handles path resolution in symlinked AIMA CodeGen environments"""
    
    def __init__(self, base_path: str):
        """Initialize with a base path."""
        self.base_path = Path(base_path)
        self.project_root = self.base_path
        self.logical_root = self._get_logical_path(self.project_root)
        self.physical_root = self.project_root.resolve()
        self.is_symlinked = self.logical_root != self.physical_root
    
    def resolve_path(self, path: str) -> Path:
        """Resolve a path, handling symlinks correctly."""
        # Convert to Path object
        path_obj = Path(path)
        
        # If absolute path, use as is
        if path_obj.is_absolute():
            return path_obj.resolve()
        
        # Otherwise, resolve relative to base_path
        full_path = self.base_path / path
        
        # Follow symlinks and return the resolved path
        if full_path.exists():
            return full_path.resolve()
        
        # If doesn't exist yet, just return the path object
        return full_path
    
    def get_canonical_path(self, path: str) -> Path:
        """Get the canonical (fully resolved) path."""
        path_obj = Path(path)
        
        # If absolute, resolve directly
        if path_obj.is_absolute():
            return path_obj.resolve()
        
        # Otherwise resolve relative to base
        full_path = self.base_path / path
        return full_path.resolve()
    
    def resolve_module_path(self, module: str) -> Optional[Path]:
        """Resolve a Python module path to a file path."""
        # Convert module notation to path
        # e.g., "src.agents.base" -> "src/agents/base.py"
        parts = module.split('.')
        
        # Try to find the module file
        possible_paths = [
            self.base_path / Path(*parts).with_suffix('.py'),
            self.base_path / Path(*parts) / '__init__.py'
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def resolve_relative(self, path: str, from_path: str) -> Path:
        """Resolve a relative path from another path."""
        # Get the directory of the from_path
        from_path_obj = self.base_path / from_path
        from_dir = from_path_obj.parent if from_path_obj.is_file() else from_path_obj
        
        # Resolve the relative path
        resolved = (from_dir / path).resolve()
        return resolved
    
    def validate_safe_path(self, path: str) -> None:
        """Ensure the path doesn't escape the base directory."""
        path_obj = Path(path)
        
        # If absolute path, check if it's under base
        if path_obj.is_absolute():
            try:
                path_obj.relative_to(self.base_path)
            except ValueError:
                raise ValueError(f"Path {path} is outside base directory")
        else:
            # For relative paths, resolve and check
            full_path = (self.base_path / path).resolve()
            try:
                full_path.relative_to(self.base_path.resolve())
            except ValueError:
                raise ValueError(f"Path {path} escapes base directory")
    
    def setup_python_path(self):
        """Configure Python path for symlinked environment."""
        paths_to_add = [str(self.logical_root), str(self.physical_root)]
        
        if self.is_symlinked:
            aima_logical = self.logical_root / 'aima_codegen'
            aima_physical = self.physical_root / 'aima_codegen' 
            paths_to_add.extend([str(aima_logical), str(aima_physical)])
        
        for path in paths_to_add:
            if path not in sys.path:
                sys.path.insert(0, path)
    
    def _get_logical_path(self, path: Path) -> Path:
        """Get logical path preserving symlinks."""
        pwd = os.environ.get('PWD')
        if pwd:
            try:
                pwd_path = Path(pwd)
                if pwd_path.samefile(Path.cwd()):
                    return pwd_path / path.relative_to(Path.cwd())
            except (ValueError, OSError):
                pass
        # Fallback to absolute without resolving symlinks
        return path.absolute()
    
    # Keep the existing methods for backward compatibility
    def _find_project_root(self) -> Path:
        """Find project root by looking for aima_codegen directory."""
        current = Path.cwd()
        # Check if we're already in aima_codegen
        if current.name == 'aima_codegen' or (current / 'aima_codegen').exists():
            return current
        # Search up the directory tree
        for parent in current.parents:
            if (parent / 'aima_codegen').exists():
                return parent
        raise ValueError("Cannot find aima_codegen directory")
    
    def get_test_file_path(self, source_file: Path) -> Path:
        """Generate test file path maintaining symlink structure."""
        # Work with logical paths to maintain project structure
        if self.is_symlinked:
            logical_source = self._get_logical_path(source_file)
            relative_source = logical_source.relative_to(self.logical_root)
        else:
            relative_source = source_file.relative_to(self.physical_root)
        # Generate test path
        if relative_source.parts and relative_source.parts[0] == 'aima_codegen':
            # Remove aima_codegen from path for test organization
            test_relative = Path(*relative_source.parts[1:])
        else:
            test_relative = relative_source
        test_name = f"test_{test_relative.stem}.py"
        test_path = self.project_root / 'tests' / test_relative.parent / test_name
        return test_path
    
    def normalize_import_path(self, file_path: Path) -> str:
        """Convert file path to Python import path."""
        if self.is_symlinked:
            relative = self._get_logical_path(file_path).relative_to(self.logical_root)
        else:
            relative = file_path.relative_to(self.physical_root)
        parts = list(relative.parts)
        if parts[-1].endswith('.py'):
            parts[-1] = parts[-1][:-3]
        return '.'.join(parts) 