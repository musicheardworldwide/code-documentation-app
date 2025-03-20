"""
API endpoints module.

This module defines the FastAPI endpoints for the code documentation application.
"""

import os
import uuid
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.api.env_config import EnvConfig
from src.api.models import (
    GitHubRequest, ZipFileRequest, DocumentationResponse, TaskStatus,
    QueryRequest, QueryResponse, QAListResponse, ErrorResponse
)
from src.api.task_manager import TaskManager

# Initialize environment configuration
env_config = EnvConfig()
api_config = env_config.get_api_config()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="Code Documentation API",
    description="API for generating comprehensive documentation for codebases",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=api_config["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiter middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Initialize task manager
task_manager = TaskManager(env_config)

# Logger
logger = logging.getLogger(__name__)


@app.get("/", tags=["Health"])
@limiter.limit(f"{api_config['rate_limit']}/minute")
async def root(request: Request):
    """
    Root endpoint for health check.
    
    Returns:
        Dict[str, str]: Health status
    """
    return {"status": "healthy", "message": "Code Documentation API is running"}


@app.post("/api/github", response_model=DocumentationResponse, tags=["Documentation"])
@limiter.limit(f"{api_config['rate_limit']}/hour")
async def process_github_repo(
    request: Request,
    github_request: GitHubRequest,
    background_tasks: BackgroundTasks
):
    """
    Process GitHub repository and generate documentation.
    
    Args:
        request (Request): FastAPI request
        github_request (GitHubRequest): GitHub repository request
        background_tasks (BackgroundTasks): FastAPI background tasks
    
    Returns:
        DocumentationResponse: Documentation task response
    """
    try:
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Create output directory if not provided
        output_dir = github_request.output_dir
        if not output_dir:
            output_dir = os.path.join(env_config.output_dir, f"github_{task_id}")
            os.makedirs(output_dir, exist_ok=True)
        
        # Start background task
        background_tasks.add_task(
            task_manager.process_github_repo,
            task_id=task_id,
            repo_url=str(github_request.repo_url),
            output_dir=output_dir,
            llm_config=github_request.llm_config.dict() if github_request.llm_config else None
        )
        
        return DocumentationResponse(
            task_id=task_id,
            status="processing",
            output_dir=output_dir,
            message="GitHub repository processing started"
        )
    except Exception as e:
        logger.error(f"Error processing GitHub repository: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Failed to process GitHub repository",
                details={"message": str(e)}
            ).dict()
        )


@app.post("/api/zip", response_model=DocumentationResponse, tags=["Documentation"])
@limiter.limit(f"{api_config['rate_limit']}/hour")
async def process_zip_file(
    request: Request,
    zip_request: ZipFileRequest,
    background_tasks: BackgroundTasks
):
    """
    Process zip file and generate documentation.
    
    Args:
        request (Request): FastAPI request
        zip_request (ZipFileRequest): Zip file request
        background_tasks (BackgroundTasks): FastAPI background tasks
    
    Returns:
        DocumentationResponse: Documentation task response
    """
    try:
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Create output directory if not provided
        output_dir = zip_request.output_dir
        if not output_dir:
            output_dir = os.path.join(env_config.output_dir, f"zip_{task_id}")
            os.makedirs(output_dir, exist_ok=True)
        
        # Start background task
        background_tasks.add_task(
            task_manager.process_zip_file,
            task_id=task_id,
            file_path=zip_request.file_path,
            output_dir=output_dir,
            llm_config=zip_request.llm_config.dict() if zip_request.llm_config else None
        )
        
        return DocumentationResponse(
            task_id=task_id,
            status="processing",
            output_dir=output_dir,
            message="Zip file processing started"
        )
    except Exception as e:
        logger.error(f"Error processing zip file: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Failed to process zip file",
                details={"message": str(e)}
            ).dict()
        )


@app.get("/api/tasks/{task_id}", response_model=TaskStatus, tags=["Tasks"])
@limiter.limit(f"{api_config['rate_limit']}/minute")
async def get_task_status(request: Request, task_id: str):
    """
    Get task status.
    
    Args:
        request (Request): FastAPI request
        task_id (str): Task ID
    
    Returns:
        TaskStatus: Task status
    """
    try:
        status = task_manager.get_task_status(task_id)
        if not status:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    error="Task not found",
                    details={"task_id": task_id}
                ).dict()
            )
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Failed to get task status",
                details={"message": str(e)}
            ).dict()
        )


@app.post("/api/query", response_model=QueryResponse, tags=["RAG"])
@limiter.limit(f"{api_config['rate_limit']}/minute")
async def query_documentation(request: Request, query_request: QueryRequest):
    """
    Query documentation using RAG.
    
    Args:
        request (Request): FastAPI request
        query_request (QueryRequest): Query request
    
    Returns:
        QueryResponse: Query response
    """
    try:
        # Check if task exists
        status = task_manager.get_task_status(query_request.task_id)
        if not status:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    error="Task not found",
                    details={"task_id": query_request.task_id}
                ).dict()
            )
        
        # Check if task is completed
        if status.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error="Task not completed",
                    details={"task_id": query_request.task_id, "status": status.status}
                ).dict()
            )
        
        # Query documentation
        result = task_manager.query_documentation(
            task_id=query_request.task_id,
            query=query_request.query,
            max_results=query_request.max_results
        )
        
        return QueryResponse(
            query=query_request.query,
            answer=result["answer"],
            context=result["context"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying documentation: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Failed to query documentation",
                details={"message": str(e)}
            ).dict()
        )


@app.get("/api/qa/{task_id}", response_model=QAListResponse, tags=["Q&A"])
@limiter.limit(f"{api_config['rate_limit']}/minute")
async def get_qa_pairs(request: Request, task_id: str):
    """
    Get Q&A pairs for a task.
    
    Args:
        request (Request): FastAPI request
        task_id (str): Task ID
    
    Returns:
        QAListResponse: Q&A pairs response
    """
    try:
        # Check if task exists
        status = task_manager.get_task_status(task_id)
        if not status:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    error="Task not found",
                    details={"task_id": task_id}
                ).dict()
            )
        
        # Check if task is completed
        if status.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error="Task not completed",
                    details={"task_id": task_id, "status": status.status}
                ).dict()
            )
        
        # Get Q&A pairs
        qa_pairs = task_manager.get_qa_pairs(task_id)
        
        return QAListResponse(
            task_id=task_id,
            qa_pairs=qa_pairs
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Q&A pairs: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Failed to get Q&A pairs",
                details={"message": str(e)}
            ).dict()
        )
