"""
API models module.

This module defines the data models used in the API.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, HttpUrl


class LLMConfig(BaseModel):
    """LLM configuration model."""
    
    base_url: HttpUrl = Field(..., description="Base URL for LLM API")
    api_key: str = Field(..., description="API key for LLM service")
    instruct_model: str = Field(..., description="Model name for instruction following")
    reasoning_model: str = Field(..., description="Model name for reasoning tasks")
    embeddings_model: str = Field(..., description="Model name for embeddings generation")


class GitHubRequest(BaseModel):
    """GitHub repository request model."""
    
    repo_url: HttpUrl = Field(..., description="GitHub repository URL")
    output_dir: Optional[str] = Field(None, description="Output directory for documentation")
    llm_config: Optional[LLMConfig] = Field(None, description="LLM configuration")


class ZipFileRequest(BaseModel):
    """Zip file request model."""
    
    file_path: str = Field(..., description="Path to zip file containing codebase")
    output_dir: Optional[str] = Field(None, description="Output directory for documentation")
    llm_config: Optional[LLMConfig] = Field(None, description="LLM configuration")


class DocumentationResponse(BaseModel):
    """Documentation response model."""
    
    task_id: str = Field(..., description="Task ID for tracking progress")
    status: str = Field(..., description="Task status")
    output_dir: Optional[str] = Field(None, description="Output directory for documentation")
    message: Optional[str] = Field(None, description="Additional information")


class TaskStatus(BaseModel):
    """Task status model."""
    
    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Task status")
    progress: float = Field(..., description="Task progress (0-100)")
    message: Optional[str] = Field(None, description="Additional information")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result")


class QueryRequest(BaseModel):
    """Query request model."""
    
    query: str = Field(..., description="Query text")
    task_id: str = Field(..., description="Task ID of the documentation task")
    max_results: Optional[int] = Field(5, description="Maximum number of results to return")


class QueryResponse(BaseModel):
    """Query response model."""
    
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    context: List[Dict[str, Any]] = Field(..., description="Context used for answer generation")


class QAPair(BaseModel):
    """Question-answer pair model."""
    
    question: str = Field(..., description="Question")
    answer: str = Field(..., description="Answer")


class QAListResponse(BaseModel):
    """Question-answer list response model."""
    
    task_id: str = Field(..., description="Task ID of the documentation task")
    qa_pairs: List[QAPair] = Field(..., description="List of question-answer pairs")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
