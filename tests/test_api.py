"""
Test script for the API endpoints.

This module tests the API endpoints for the code documentation application.
"""

import os
import sys
import unittest
import tempfile
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.endpoints import app
from src.api.task_manager import TaskManager
from src.api.env_config import EnvConfig


class TestAPIEndpoints(unittest.TestCase):
    """Tests for the API endpoints."""
    
    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")
    
    @patch('src.api.task_manager.TaskManager.process_github_repo')
    def test_process_github_repo(self, mock_process):
        """Test processing GitHub repository."""
        # Setup mock
        mock_process.return_value = None
        
        # Test endpoint
        response = self.client.post(
            "/api/github",
            json={
                "repo_url": "https://github.com/username/repo",
                "output_dir": "/tmp/output",
                "llm_config": {
                    "base_url": "https://api.example.com",
                    "api_key": "test_api_key",
                    "instruct_model": "test_instruct",
                    "reasoning_model": "test_reasoning",
                    "embeddings_model": "test_embeddings"
                }
            }
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertIn("task_id", response.json())
        self.assertEqual(response.json()["status"], "processing")
        
        # Verify background task was called
        mock_process.assert_called_once()
    
    @patch('src.api.task_manager.TaskManager.process_zip_file')
    def test_process_zip_file(self, mock_process):
        """Test processing zip file."""
        # Setup mock
        mock_process.return_value = None
        
        # Test endpoint
        response = self.client.post(
            "/api/zip",
            json={
                "file_path": "/path/to/codebase.zip",
                "output_dir": "/tmp/output",
                "llm_config": {
                    "base_url": "https://api.example.com",
                    "api_key": "test_api_key",
                    "instruct_model": "test_instruct",
                    "reasoning_model": "test_reasoning",
                    "embeddings_model": "test_embeddings"
                }
            }
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertIn("task_id", response.json())
        self.assertEqual(response.json()["status"], "processing")
        
        # Verify background task was called
        mock_process.assert_called_once()
    
    @patch('src.api.task_manager.TaskManager.get_task_status')
    def test_get_task_status(self, mock_get_status):
        """Test getting task status."""
        # Setup mock
        mock_get_status.return_value = {
            "task_id": "test_task_id",
            "status": "completed",
            "progress": 100,
            "message": "Task completed",
            "result": {
                "file_count": 10,
                "function_count": 20,
                "class_count": 5,
                "output_path": "/tmp/output"
            }
        }
        
        # Test endpoint
        response = self.client.get("/api/tasks/test_task_id")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["task_id"], "test_task_id")
        self.assertEqual(response.json()["status"], "completed")
        self.assertEqual(response.json()["progress"], 100)
        
        # Verify task manager was called
        mock_get_status.assert_called_once_with("test_task_id")
    
    @patch('src.api.task_manager.TaskManager.get_task_status')
    @patch('src.api.task_manager.TaskManager.query_documentation')
    def test_query_documentation(self, mock_query, mock_get_status):
        """Test querying documentation."""
        # Setup mocks
        mock_get_status.return_value = {
            "task_id": "test_task_id",
            "status": "completed",
            "progress": 100,
            "message": "Task completed",
            "result": None
        }
        
        mock_query.return_value = {
            "answer": "This is the answer to your query.",
            "context": [
                {
                    "content": "def function1(): pass",
                    "metadata": {"file_path": "/path/to/file1.py"},
                    "distance": 0.1
                }
            ]
        }
        
        # Test endpoint
        response = self.client.post(
            "/api/query",
            json={
                "query": "How does function1 work?",
                "task_id": "test_task_id",
                "max_results": 5
            }
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["query"], "How does function1 work?")
        self.assertEqual(response.json()["answer"], "This is the answer to your query.")
        self.assertEqual(len(response.json()["context"]), 1)
        
        # Verify task manager was called
        mock_get_status.assert_called_once_with("test_task_id")
        mock_query.assert_called_once_with(
            task_id="test_task_id",
            query="How does function1 work?",
            max_results=5
        )
    
    @patch('src.api.task_manager.TaskManager.get_task_status')
    @patch('src.api.task_manager.TaskManager.get_qa_pairs')
    def test_get_qa_pairs(self, mock_get_qa, mock_get_status):
        """Test getting Q&A pairs."""
        # Setup mocks
        mock_get_status.return_value = {
            "task_id": "test_task_id",
            "status": "completed",
            "progress": 100,
            "message": "Task completed",
            "result": None
        }
        
        mock_get_qa.return_value = [
            {"question": "How does function1 work?", "answer": "Function1 works by..."},
            {"question": "What is the purpose of class2?", "answer": "Class2 is used for..."}
        ]
        
        # Test endpoint
        response = self.client.get("/api/qa/test_task_id")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["task_id"], "test_task_id")
        self.assertEqual(len(response.json()["qa_pairs"]), 2)
        
        # Verify task manager was called
        mock_get_status.assert_called_once_with("test_task_id")
        mock_get_qa.assert_called_once_with("test_task_id")


class TestEnvConfig(unittest.TestCase):
    """Tests for the environment configuration."""
    
    def test_env_config_defaults(self):
        """Test environment configuration defaults."""
        # Create environment configuration
        env_config = EnvConfig()
        
        # Verify defaults
        self.assertEqual(env_config.llm_base_url, "https://api.example.com")
        self.assertEqual(env_config.api_host, "0.0.0.0")
        self.assertEqual(env_config.api_port, 8000)
    
    def test_env_config_from_env(self):
        """Test environment configuration from environment variables."""
        # Set environment variables
        os.environ["LLM_BASE_URL"] = "https://custom-api.example.com"
        os.environ["API_PORT"] = "9000"
        
        # Create environment configuration
        env_config = EnvConfig()
        
        # Verify values from environment
        self.assertEqual(env_config.llm_base_url, "https://custom-api.example.com")
        self.assertEqual(env_config.api_port, 9000)
        
        # Reset environment variables
        os.environ.pop("LLM_BASE_URL")
        os.environ.pop("API_PORT")
    
    def test_get_llm_config(self):
        """Test getting LLM configuration."""
        # Create environment configuration
        env_config = EnvConfig()
        
        # Get LLM configuration
        llm_config = env_config.get_llm_config()
        
        # Verify configuration
        self.assertIn("base_url", llm_config)
        self.assertIn("api_key", llm_config)
        self.assertIn("instruct_model", llm_config)
        self.assertIn("reasoning_model", llm_config)
        self.assertIn("embeddings_model", llm_config)
    
    def test_get_api_config(self):
        """Test getting API configuration."""
        # Create environment configuration
        env_config = EnvConfig()
        
        # Get API configuration
        api_config = env_config.get_api_config()
        
        # Verify configuration
        self.assertIn("host", api_config)
        self.assertIn("port", api_config)
        self.assertIn("workers", api_config)
        self.assertIn("debug", api_config)
        self.assertIn("cors_origins", api_config)
        self.assertIn("rate_limit", api_config)


if __name__ == "__main__":
    unittest.main()
