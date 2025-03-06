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
        mock_response.choices[0].message.content = json.dumps({
            "overview": "Test overview",
            "research_queries": [
                "Section 1 query",
                "Section 2 query"
            ]
        })
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
        assert "overview" in result
        assert "research_queries" in result
        assert len(result["research_queries"]) == 2
        assert "Section 1 query" in result["research_queries"][0]
        
        # Verify API call
        mock_client.chat.completions.create.assert_called_once()
        
    @patch("src.askp.deep_research.generate_research_plan")
    def test_create_research_queries(self, mock_generate_plan):
        """Test creating research queries from a plan."""
        # Setup mock
        mock_generate_plan.return_value = {
            "overview": "Test overview",
            "research_queries": [
                "Section 1 query",
                "Section 2 query"
            ]
        }
        
        # Call function
        queries = create_research_queries("Test query", "test-model", 0.7)
        
        # Assertions
        assert len(queries) == 3  # Original query + 2 section queries
        assert queries[0] == "Test query"
        assert queries[1] == "Section 1 query"
        assert queries[2] == "Section 2 query"
