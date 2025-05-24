"""Test SymlinkAwarePathResolver functionality."""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
from aima_codegen.path_resolver import SymlinkAwarePathResolver


class TestSymlinkPathResolver:
    """Test symlink-aware path resolution."""

    def test_symlink_resolution(self):
        """Test resolving paths through symlinks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directory structure
            real_dir = Path(tmpdir) / "real_aima_codegen"
            real_dir.mkdir()
            (real_dir / "module.py").write_text("# test module")
            
            # Create symlink
            symlink_dir = Path(tmpdir) / "src"
            symlink_dir.symlink_to(real_dir)
            
            # Test resolver
            resolver = SymlinkAwarePathResolver(base_path=tmpdir)
            
            # Resolve through symlink
            resolved = resolver.resolve_path("src/module.py")
            assert resolved.exists()
            assert resolved.read_text() == "# test module"
            
            # Verify canonical path
            canonical = resolver.get_canonical_path("src/module.py")
            assert "real_aima_codegen" in str(canonical)
            assert "src" not in str(canonical)

    def test_nested_symlinks(self):
        """Test resolving nested symlinks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            real_dir = Path(tmpdir) / "real" / "nested" / "aima_codegen"
            real_dir.mkdir(parents=True)
            (real_dir / "test.py").write_text("# nested test")
            
            # Create multiple symlinks
            link1 = Path(tmpdir) / "link1"
            link1.symlink_to(Path(tmpdir) / "real")
            
            link2 = Path(tmpdir) / "link2"
            link2.symlink_to(link1 / "nested")
            
            resolver = SymlinkAwarePathResolver(base_path=tmpdir)
            
            # Resolve through multiple symlinks
            resolved = resolver.resolve_path("link2/aima_codegen/test.py")
            assert resolved.exists()
            assert resolved.read_text() == "# nested test"

    def test_module_import_path_resolution(self):
        """Test resolving module import paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create package structure
            pkg_dir = Path(tmpdir) / "aima_codegen"
            pkg_dir.mkdir()
            (pkg_dir / "__init__.py").write_text("")
            
            agents_dir = pkg_dir / "agents"
            agents_dir.mkdir()
            (agents_dir / "__init__.py").write_text("")
            (agents_dir / "base.py").write_text("class BaseAgent: pass")
            
            # Create symlink
            src_link = Path(tmpdir) / "src"
            src_link.symlink_to(pkg_dir)
            
            resolver = SymlinkAwarePathResolver(base_path=tmpdir)
            
            # Test module path resolution
            module_path = resolver.resolve_module_path("src.agents.base")
            assert module_path is not None
            assert module_path.exists()
            assert module_path.name == "base.py"

    def test_relative_path_resolution(self):
        """Test resolving relative paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create structure
            base = Path(tmpdir) / "project"
            base.mkdir()
            (base / "config.py").write_text("# config")
            
            sub_dir = base / "subdir"
            sub_dir.mkdir()
            (sub_dir / "module.py").write_text("# module")
            
            resolver = SymlinkAwarePathResolver(base_path=base)
            
            # Test relative resolution
            resolved = resolver.resolve_relative("../config.py", from_path="subdir/module.py")
            assert resolved.exists()
            assert resolved.read_text() == "# config"

    def test_safe_path_operations(self):
        """Test safe path operations prevent escaping base directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir) / "safe_base"
            base.mkdir()
            
            resolver = SymlinkAwarePathResolver(base_path=base)
            
            # Test path traversal protection
            with pytest.raises(ValueError):
                resolver.validate_safe_path("../../etc/passwd")
            
            # Valid paths should work
            resolver.validate_safe_path("subdir/file.py")
            resolver.validate_safe_path("./local.py") 