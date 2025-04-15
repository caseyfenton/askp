#!/usr/bin/env python3
"""
Tests for BGRun integration with ASKP.
"""
import os
import unittest
from unittest.mock import patch, MagicMock
import sys
import tempfile
from pathlib import Path

# Add parent directory to path to import askp modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.askp.bgrun_integration import (
    is_bgrun_available,
    get_bgrun_path,
    notify_query_completed,
    notify_multi_query_completed,
    update_askp_status_widget
)


class TestBGRunIntegration(unittest.TestCase):
    """Tests for the BGRun integration functionality."""

    @patch('shutil.which')
    def test_is_bgrun_available(self, mock_which):
        """Test the is_bgrun_available function."""
        # Test when bgrun is available
        mock_which.return_value = '/usr/local/bin/bgrun'
        self.assertTrue(is_bgrun_available())
        
        # Test when bgrun is not available
        mock_which.return_value = None
        self.assertFalse(is_bgrun_available())
    
    @patch('shutil.which')
    @patch('os.access')
    @patch('pathlib.Path.exists')
    def test_get_bgrun_path(self, mock_exists, mock_access, mock_which):
        """Test the get_bgrun_path function."""
        # Test when bgrun is in PATH
        mock_which.return_value = '/usr/local/bin/bgrun'
        self.assertEqual(get_bgrun_path(), '/usr/local/bin/bgrun')
        
        # Test when bgrun is not in PATH but exists in standard location
        mock_which.return_value = None
        mock_exists.return_value = True
        mock_access.return_value = True
        self.assertIsNotNone(get_bgrun_path())
        
        # Test when bgrun cannot be found
        mock_exists.return_value = False
        self.assertIsNone(get_bgrun_path())
    
    @patch('subprocess.run')
    @patch('src.askp.bgrun_integration.get_bgrun_path')
    def test_notify_query_completed(self, mock_get_path, mock_run):
        """Test the notify_query_completed function."""
        # Setup
        mock_get_path.return_value = '/usr/local/bin/bgrun'
        mock_run.return_value = MagicMock(returncode=0)
        
        # Test successful notification
        result = notify_query_completed(
            "What is Python?", 
            "results.md", 
            "sonar-pro", 
            1000, 
            0.05
        )
        self.assertTrue(result)
        mock_run.assert_called_once()
        
        # Test when bgrun is not available
        mock_get_path.return_value = None
        result = notify_query_completed(
            "What is Python?", 
            "results.md", 
            "sonar-pro", 
            1000, 
            0.05
        )
        self.assertFalse(result)
    
    @patch('subprocess.run')
    @patch('src.askp.bgrun_integration.get_bgrun_path')
    def test_notify_multi_query_completed(self, mock_get_path, mock_run):
        """Test the notify_multi_query_completed function."""
        # Setup
        mock_get_path.return_value = '/usr/local/bin/bgrun'
        mock_run.return_value = MagicMock(returncode=0)
        
        # Test successful notification
        result = notify_multi_query_completed(
            5, 
            "combined_results.md", 
            5000, 
            0.25
        )
        self.assertTrue(result)
        mock_run.assert_called_once()
        
        # Test when bgrun is not available
        mock_get_path.return_value = None
        result = notify_multi_query_completed(
            5, 
            "combined_results.md", 
            5000, 
            0.25
        )
        self.assertFalse(result)
    
    @patch('subprocess.run')
    @patch('src.askp.bgrun_integration.get_bgrun_path')
    def test_update_askp_status_widget(self, mock_get_path, mock_run):
        """Test the update_askp_status_widget function."""
        # Setup
        mock_get_path.return_value = '/usr/local/bin/bgrun'
        mock_run.return_value = MagicMock(returncode=0)
        
        # Test successful widget update
        result = update_askp_status_widget(10, 0.50, 2.5)
        self.assertTrue(result)
        mock_run.assert_called_once()
        
        # Test when bgrun is not available
        mock_get_path.return_value = None
        result = update_askp_status_widget(10, 0.50, 2.5)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
