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
        # Create a properly formatted JSON response that the function will parse
        mock_response.choices[0].message.content = """
        Here's a research plan:
        
        {
            "overview": "Test overview for research",
            "research_queries": [
                "First research query about the topic",
                "Second research query exploring another aspect"
            ]
        }
        """
        return mock_response
    
    @patch("src.askp.deep_research.OpenAI")
    def test_generate_research_plan(self, mock_openai_class, mock_openai_response):
        """Test generating a research plan."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_class.return_value = mock_client
        
        # Call function
        result = generate_research_plan("Test query", "test-model", 0.7)
        
        # Assertions
        assert "research_overview" in result
        assert "research_sections" in result
        assert len(result["research_sections"]) == 2
        assert "First research query" in result["research_sections"][0]["description"]
        assert "Second research query" in result["research_sections"][1]["description"]
        
        # Verify API call
        mock_client.chat.completions.create.assert_called_once()
        
    @patch("src.askp.deep_research.generate_research_plan")
    def test_create_research_queries(self, mock_generate_plan):
        """Test creating research queries from a plan."""
        # Setup mock
        mock_generate_plan.return_value = {
            "research_overview": "Test overview",
            "research_sections": [
                {"title": "Section 1: First query", "description": "First query"},
                {"title": "Section 2: Second query", "description": "Second query"}
            ]
        }
        
        # Call function
        queries = create_research_queries("Test query", "test-model", 0.7)
        
        # Assertions
        assert len(queries) == 3  # Original query + 2 section queries
        assert queries[0] == "Test query"
        assert queries[1] == "First query"
        assert queries[2] == "Second query"
