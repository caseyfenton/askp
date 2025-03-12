"""Tests for the deep research feature."""
import json
import os
import pytest
from unittest.mock import patch, MagicMock
from src.askp.deep_research import generate_research_plan, create_research_queries

class TestDeepResearch:
    """Test suite for deep research functionality."""
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response for testing."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = """
        Here's a research plan:
        
        {
            "research_overview": "Test overview for research",
            "research_sections": [
                {"title": "Section 1: First query", "description": "First research query about the topic"},
                {"title": "Section 2: Second query", "description": "Second research query exploring another aspect"}
            ]
        }
        """
        return mock_response
    
    @patch("src.askp.cli.search_perplexity")
    def test_generate_research_plan(self, mock_search_perplexity, mock_openai_response):
        """Test generating a research plan."""
        mock_search_perplexity.return_value = {
            "content": """
            {
                "research_overview": "Test overview for research",
                "research_sections": [
                    {"title": "Section 1: First query", "description": "First research query about the topic"},
                    {"title": "Section 2: Second query", "description": "Second research query exploring another aspect"}
                ]
            }
            """
        }
        result = generate_research_plan("Test query", "test-model", 0.7, {"test_mode": True})
        assert "research_overview" in result
        assert "research_sections" in result
        assert len(result["research_sections"]) == 2
        assert "First research query" in result["research_sections"][0]["description"]
        assert "Second research query" in result["research_sections"][1]["description"]
        assert mock_search_perplexity.called
        
    @patch("src.askp.deep_research.generate_research_plan")
    def test_create_research_queries(self, mock_generate_plan):
        """Test creating research queries from a plan."""
        mock_generate_plan.return_value = {
            "research_overview": "Test overview",
            "research_sections": [
                {"title": "Section 1: First query", "description": "First query"},
                {"title": "Section 2: Second query", "description": "Second query"}
            ]
        }
        queries = create_research_queries("Test query", "test-model", 0.7)
        assert len(queries) == 3
        assert queries[0] == "Test query"
        assert queries[1] == "First query"
        assert queries[2] == "Second query"