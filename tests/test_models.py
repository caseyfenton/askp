#!/usr/bin/env python3

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import tempfile
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from askp.models import (
    get_model_info,
    list_models,
    get_model_capabilities
)

class TestModelFunctions(unittest.TestCase):
    def test_get_model_info_standard(self):
        """Test standard model info retrieval"""
        info = get_model_info("sonar")
        self.assertEqual(info["id"], "sonar")
        self.assertEqual(info["cost_per_million"], 1.00)
        self.assertTrue("description" in info)
        self.assertTrue("capabilities" in info)

    def test_get_model_info_reasoning(self):
        """Test reasoning model info retrieval"""
        info = get_model_info("sonar-pro")
        self.assertEqual(info["id"], "sonar-pro")
        self.assertEqual(info["cost_per_million"], 5.00)
        self.assertTrue("large-context" in info["capabilities"])

    def test_get_model_info_pro(self):
        """Test pro model info retrieval"""
        info = get_model_info("pplx")
        self.assertEqual(info["id"], "pplx-api")
        self.assertEqual(info["cost_per_million"], 1.50)
        self.assertTrue("high-throughput" in info["capabilities"])

    def test_get_model_info_expert(self):
        """Test expert model info retrieval"""
        info = get_model_info("gpt4")
        self.assertEqual(info["id"], "gpt4-omni")
        self.assertEqual(info["cost_per_million"], 12.00)
        self.assertTrue("expert-reasoning" in info["capabilities"])

    def test_get_model_info_default(self):
        """Test default model info retrieval"""
        info = get_model_info("nonexistent")
        self.assertEqual(info["id"], "sonar")
        self.assertEqual(info["cost_per_million"], 1.00)

    def test_list_models(self):
        """Test listing all models"""
        models = list_models()
        self.assertIn("sonar", models)
        self.assertIn("sonar-pro", models)
        self.assertIn("pplx", models)
        self.assertIn("gpt4", models)
        self.assertIn("claude", models)
        self.assertEqual(len(models), 5)

    def test_get_model_capabilities(self):
        """Test getting model capabilities"""
        capabilities = get_model_capabilities("sonar")
        self.assertIn("code-completion", capabilities)
        self.assertIn("documentation", capabilities)
        self.assertIn("real-time-search", capabilities)

if __name__ == "__main__":
    unittest.main()
