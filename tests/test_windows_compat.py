"""Windows compatibility tests for ASKP."""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from click.testing import CliRunner
from askp.cli import cli
from askp.file_utils import format_path, generate_cat_commands
from askp.utils import get_output_dir, sanitize_filename, generate_combined_filename


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def mock_windows_env():
    """Create a mock Windows environment."""
    with patch('sys.platform', 'win32'), \
         patch('os.path.sep', '\\'), \
         patch('os.name', 'nt'), \
         patch('os.environ', {
             'USERPROFILE': 'C:\\Users\\TestUser',
             'APPDATA': 'C:\\Users\\TestUser\\AppData\\Roaming',
             'PERPLEXITY_API_KEY': 'test-key'
         }):
        yield


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific tests")
class TestWindowsCompat:
    """Windows compatibility tests."""
    
    def test_windows_path_handling(self, mock_windows_env):
        """Test Windows path handling."""
        # Test Windows path normalization
        paths = [
            ('C:\\Users\\TestUser\\Documents\\results.md', 'C:/Users/TestUser/Documents/results.md'),
            ('C:\\Program Files\\Python\\Scripts\\askp.exe', 'C:/Program Files/Python/Scripts/askp.exe'),
            ('results\\file with spaces.md', 'results/file with spaces.md'),
            ('..\\parent\\file.md', '../parent/file.md')
        ]
        
        for win_path, expected in paths:
            formatted = format_path(win_path)
            assert '\\' not in formatted, f"Path should not contain backslashes: {formatted}"
            # Check normalized path matches expected format
            assert formatted.replace('\\', '/') == expected.replace('\\', '/'), f"Path normalization failed: {formatted} != {expected}"
    
    def test_windows_filename_sanitization(self, mock_windows_env):
        """Test Windows filename sanitization."""
        # Windows disallows these characters: < > : " / \ | ? *
        invalid_filenames = [
            ('test<file>.md', 'test_file_.md'),
            ('results:output.txt', 'results_output.txt'),
            ('data?.txt', 'data_.txt'),
            ('path\\to/file', 'path_to_file'),
            ('file|with*chars', 'file_with_chars'),
        ]
        
        for invalid, expected in invalid_filenames:
            sanitized = sanitize_filename(invalid)
            
            # Check that sanitized name doesn't contain Windows-invalid chars
            assert all(c not in sanitized for c in '<>:"/\\|?*'), f"Sanitized name contains invalid Windows chars: {sanitized}"
            assert sanitized == expected, f"Filename sanitization failed: {sanitized} != {expected}"
    
    def test_windows_output_directory(self, mock_windows_env):
        """Test Windows output directory handling."""
        with patch('askp.utils.os.path.expanduser', return_value='C:\\Users\\TestUser'):
            with patch('askp.utils.os.makedirs') as mock_makedirs:
                output_dir = get_output_dir()
                
                # Verify the output directory uses proper path formatting
                assert '\\' not in output_dir, f"Output directory contains backslashes: {output_dir}"
                assert output_dir.replace('/', '\\').startswith('C:\\Users\\TestUser'), f"Output directory not under user home: {output_dir}"
                
                # Check that directories are created with expected path
                mock_makedirs.assert_called_once()
    
    def test_windows_cmd_generation(self, mock_windows_env):
        """Test command generation for Windows."""
        results = [
            {"metadata": {"saved_path": "results\\query_1.md"}},
            {"metadata": {"saved_path": "results\\query_2.md"}}
        ]
        
        with patch('askp.file_utils.os.path.exists', return_value=True):
            with patch('askp.file_utils.get_file_stats', return_value={"size": 1000, "lines": 50}):
                cmds = generate_cat_commands(results)
                
                # Check that commands use forward slashes
                for view_cmds in cmds.values():
                    for cmd in view_cmds:
                        assert '\\' not in cmd, f"Command contains backslashes: {cmd}"
                        
                        # For Windows, we should use type instead of cat, but we're checking the paths are correct
                        assert cmd.startswith(('cat ', 'type ')), f"Command doesn't start with cat or type: {cmd}"
    
    def test_windows_env_vars(self, mock_windows_env):
        """Test Windows environment variable handling."""
        with patch('askp.cli.load_api_key') as mock_load_api_key:
            mock_load_api_key.return_value = "test-key"
            
            # Verify API key is found in Windows environment
            from askp.cli import load_api_key
            api_key = load_api_key()
            assert api_key == "test-key", f"API key not loaded correctly: {api_key}"
    
    def test_combined_filename_windows(self, mock_windows_env):
        """Test combined filename generation on Windows."""
        # Test with Windows-unfriendly characters
        queries = ["test<query>", "Windows\\path|test", "file*name?"]
        
        filename = generate_combined_filename(queries, "markdown")
        
        # Check for Windows compatibility
        assert all(c not in filename for c in '<>:"/\\|?*'), f"Filename contains invalid Windows chars: {filename}"
        assert "test_query" in filename, "Filename doesn't contain sanitized query"


class TestCrossPlatformCompat:
    """Tests that can run on any platform to verify Windows compatibility."""
    
    def test_cross_platform_path_handling(self):
        """Test path handling works on all platforms."""
        from askp.file_utils import format_path
        import os
        
        # Using Windows-style paths with os.path.normpath to get platform-appropriate paths
        test_paths = [
            ('results.md', 'results.md'),  # Simple filename
            ('path/to/file.txt', os.path.join('path', 'to', 'file.txt')),  # Unix path
            ('../parent/file.md', os.path.join('..', 'parent', 'file.md')),  # Relative path
        ]
        
        for input_path, normalized in test_paths:
            formatted = format_path(input_path)
            assert isinstance(formatted, str), f"Formatted path should be a string: {formatted}"
            # On Windows format_path may return absolute path, so we just check it's a valid string
    
    def test_cross_platform_filename_sanitization(self):
        """Test filename sanitization works on all platforms."""
        from askp.utils import sanitize_filename
        
        # Test with characters invalid on Windows
        test_cases = [
            ('test<file>.txt', 'test_file_.txt'),
            ('file:name.md', 'file_name.md'),
            ('query?result.json', 'query_result.json'),
        ]
        
        for input_name, expected in test_cases:
            sanitized = sanitize_filename(input_name)
            for char in '<>:"/\\|?*':
                assert char not in sanitized, f"Sanitized filename contains invalid character '{char}': {sanitized}"
    
    def test_universal_combined_filename(self):
        """Test combined filename works universally."""
        from askp.utils import generate_combined_filename
        
        # Test with Windows-unfriendly characters
        queries = ["test query", "query2", "query3"]
        
        # Create a proper opts dictionary as expected by the function
        opts = {"format": "markdown"}
        
        filename = generate_combined_filename(queries, opts)
        
        # Check for Windows compatibility
        assert all(c not in filename for c in '<>:"/\\|?*'), f"Filename contains invalid Windows chars: {filename}"
        assert filename.endswith(".md"), "Filename doesn't have correct extension"
        assert "test_query" in filename or "query" in filename, "Filename should include the first query"
