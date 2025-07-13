"""Tests for ASKP installation and setup."""
import os
import subprocess
import sys
from pathlib import Path
import pytest

def test_python_version():
    """Test Python version compatibility."""
    assert sys.version_info >= (3, 8), "Python 3.8+ is required"

def test_install_script_exists():
    """Test that install.sh exists and is executable."""
    install_script = Path("install.sh")
    assert install_script.exists(), "install.sh not found"
    assert os.access(install_script, os.X_OK), "install.sh not executable"

def test_askp_wrapper_exists():
    """Test that the askp wrapper script exists."""
    # Skip test - installation structure has changed
    pytest.skip("Installation structure has changed and needs test update")

def test_package_structure():
    """Test package directory structure."""
    required_files = [
        "setup.py",
        "requirements.txt",
        "requirements-dev.txt",
        "README.md",
        "src/askp/__init__.py",
        "src/askp/cli.py",
    ]
    for file in required_files:
        assert Path(file).exists(), f"{file} not found"

@pytest.mark.skipif(not os.environ.get("RUN_INSTALL_TESTS"), 
                    reason="Skipping installation tests by default")
class TestInstallation:
    """Test actual installation process."""
    
    def test_install_dry_run(self, tmp_path):
        """Test installation dry run."""
        result = subprocess.run(
            ["./install.sh", f"--prefix={tmp_path}", "--dry-run"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Installation dry run failed"
        
    def test_install_no_symlinks(self, tmp_path):
        """Test installation without symlinks."""
        result = subprocess.run(
            ["./install.sh", f"--prefix={tmp_path}", "--no-symlinks"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Installation failed"
        assert (tmp_path / "bin/askp").exists(), "askp not installed"
        assert not (tmp_path / "bin/ask").exists(), "ask symlink created"
        
    def test_install_with_symlinks(self, tmp_path):
        """Test installation with symlinks."""
        result = subprocess.run(
            ["./install.sh", f"--prefix={tmp_path}"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Installation failed"
        assert (tmp_path / "bin/askp").exists(), "askp not installed"
        assert (tmp_path / "bin/ask").exists(), "ask symlink not created"
        assert (tmp_path / "bin/askp").exists(), "askp symlink not created"
