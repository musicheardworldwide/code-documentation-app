"""
Task manager module.

This module manages background tasks for code documentation generation.
"""

import os
import time
import logging
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.api.env_config import EnvConfig
from src.api.models import TaskStatus, QAPair
from src.ingestion.github_ingestion import GitHubIngestion
from src.ingestion.zip_ingestion import ZipIngestion
from src.analysis.code_analyzer import CodeAnalyzer
from src.llm_integration.model_orchestrator import ModelOrchestrator
from src.documentation.doc_generator import DocumentationGenerator
from src.rag.rag_system import RAGSystem

logger = logging.getLogger(__name__)

class TaskManager:
    """Manager for background tasks."""
    
    def __init__(self, env_config: EnvConfig):
        """
        Initialize task manager.
        
        Args:
            env_config (EnvConfig): Environment configuration
        """
        self.env_config = env_config
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
    
    def process_github_repo(
        self,
        task_id: str,
        repo_url: str,
        output_dir: str,
        llm_config: Optional[Dict[str, Any]] = None
    ):
        """
        Process GitHub repository in background.
        
        Args:
            task_id (str): Task ID
            repo_url (str): GitHub repository URL
            output_dir (str): Output directory
            llm_config (Dict[str, Any], optional): LLM configuration
        """
        try:
            # Initialize task
            self._init_task(task_id, output_dir)
            
            # Update task status
            self._update_task_status(task_id, "cloning", 5, "Cloning GitHub repository")
            
            # Clone repository
            github_ingestion = GitHubIngestion()
            code_path = github_ingestion.clone_repository(repo_url)
            
            # Process code
            self._process_code(task_id, code_path, output_dir, llm_config)
            
        except Exception as e:
            logger.error(f"Error processing GitHub repository: {e}")
            self._update_task_status(task_id, "failed", 0, f"Error: {str(e)}")
    
    def process_zip_file(
        self,
        task_id: str,
        file_path: str,
        output_dir: str,
        llm_config: Optional[Dict[str, Any]] = None
    ):
        """
        Process zip file in background.
        
        Args:
            task_id (str): Task ID
            file_path (str): Path to zip file
            output_dir (str): Output directory
            llm_config (Dict[str, Any], optional): LLM configuration
        """
        try:
            # Initialize task
            self._init_task(task_id, output_dir)
            
            # Update task status
            self._update_task_status(task_id, "extracting", 5, "Extracting zip file")
            
            # Extract zip file
            zip_ingestion = ZipIngestion()
            code_path = zip_ingestion.extract_zip(file_path)
            
            # Process code
            self._process_code(task_id, code_path, output_dir, llm_config)
            
        except Exception as e:
            logger.error(f"Error processing zip file: {e}")
            self._update_task_status(task_id, "failed", 0, f"Error: {str(e)}")
    
    def _process_code(
        self,
        task_id: str,
        code_path: str,
        output_dir: str,
        llm_config: Optional[Dict[str, Any]] = None
    ):
        """
        Process code and generate documentation.
        
        Args:
            task_id (str): Task ID
            code_path (str): Path to code
            output_dir (str): Output directory
            llm_config (Dict[str, Any], optional): LLM configuration
        """
        try:
            # Initialize LLM orchestrator
            orchestrator = self._init_llm_orchestrator(llm_config)
            
            # Update task status
            self._update_task_status(task_id, "analyzing", 20, "Analyzing code structure")
            
            # Analyze code
            analyzer = CodeAnalyzer()
            analysis_results = analyzer.analyze(code_path)
            
            # Update task status
            self._update_task_status(task_id, "identifying_dependencies", 40, "Identifying dependencies")
            
            # Identify dependencies
            dependency_results = analyzer.identify_dependencies(analysis_results)
            analysis_results['dependencies'] = dependency_results
            
            # Initialize RAG system if orchestrator is available
            rag_system = None
            if orchestrator:
                # Update task status
                self._update_task_status(task_id, "indexing", 60, "Indexing code for RAG")
                
                # Initialize RAG system
                rag_system = RAGSystem(orchestrator)
                rag_system.index_codebase(code_path, analysis_results)
            
            # Update task status
            self._update_task_status(task_id, "generating_documentation", 80, "Generating documentation")
            
            # Generate documentation
            doc_generator = DocumentationGenerator(orchestrator, rag_system)
            doc_path = doc_generator.generate(analysis_results, output_dir)
            
            # Store results
            with self.lock:
                self.tasks[task_id]["code_path"] = code_path
                self.tasks[task_id]["analysis_results"] = analysis_results
                self.tasks[task_id]["rag_system"] = rag_system
                self.tasks[task_id]["doc_path"] = doc_path
            
            # Update task status
            self._update_task_status(
                task_id,
                "completed",
                100,
                "Documentation generation completed",
                {
                    "file_count": analysis_results["file_count"],
                    "function_count": analysis_results["function_count"],
                    "class_count": analysis_results["class_count"],
                    "output_path": os.path.abspath(output_dir)
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing code: {e}")
            self._update_task_status(task_id, "failed", 0, f"Error: {str(e)}")
    
    def _init_llm_orchestrator(self, llm_config: Optional[Dict[str, Any]] = None) -> Optional[ModelOrchestrator]:
        """
        Initialize LLM orchestrator.
        
        Args:
            llm_config (Dict[str, Any], optional): LLM configuration
        
        Returns:
            Optional[ModelOrchestrator]: Initialized orchestrator or None if initialization fails
        """
        try:
            # Use provided LLM config or default from environment
            config = llm_config or self.env_config.get_llm_config()
            
            # Initialize orchestrator
            orchestrator = ModelOrchestrator()
            orchestrator.update_configuration(config)
            
            if not orchestrator.is_ready():
                logger.warning("LLM orchestrator initialization failed. Documentation will be generated without LLM enhancement.")
                return None
            
            return orchestrator
        except Exception as e:
            logger.error(f"LLM orchestrator initialization failed: {e}")
            return None
    
    def _init_task(self, task_id: str, output_dir: str):
        """
        Initialize task.
        
        Args:
            task_id (str): Task ID
            output_dir (str): Output directory
        """
        with self.lock:
            self.tasks[task_id] = {
                "status": "initialized",
                "progress": 0,
                "message": "Task initialized",
                "start_time": datetime.now(),
                "update_time": datetime.now(),
                "output_dir": output_dir,
                "result": None
            }
    
    def _update_task_status(
        self,
        task_id: str,
        status: str,
        progress: float,
        message: str,
        result: Optional[Dict[str, Any]] = None
    ):
        """
        Update task status.
        
        Args:
            task_id (str): Task ID
            status (str): Task status
            progress (float): Task progress (0-100)
            message (str): Status message
            result (Dict[str, Any], optional): Task result
        """
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id]["status"] = status
                self.tasks[task_id]["progress"] = progress
                self.tasks[task_id]["message"] = message
                self.tasks[task_id]["update_time"] = datetime.now()
                if result:
                    self.tasks[task_id]["result"] = result
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        Get task status.
        
        Args:
            task_id (str): Task ID
        
        Returns:
            Optional[TaskStatus]: Task status or None if task not found
        """
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                return TaskStatus(
                    task_id=task_id,
                    status=task["status"],
                    progress=task["progress"],
                    message=task["message"],
                    result=task["result"]
                )
            return None
    
    def query_documentation(
        self,
        task_id: str,
        query: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Query documentation using RAG.
        
        Args:
            task_id (str): Task ID
            query (str): Query text
            max_results (int, optional): Maximum number of results
        
        Returns:
            Dict[str, Any]: Query result
        """
        with self.lock:
            if task_id not in self.tasks:
                raise ValueError(f"Task {task_id} not found")
            
            task = self.tasks[task_id]
            if task["status"] != "completed":
                raise ValueError(f"Task {task_id} is not completed")
            
            rag_system = task.get("rag_system")
            if not rag_system:
                raise ValueError(f"RAG system not available for task {task_id}")
            
            # Generate answer using RAG
            result = rag_system.generate_answer(query, max_results)
            return result
    
    def get_qa_pairs(self, task_id: str) -> List[QAPair]:
        """
        Get Q&A pairs for a task.
        
        Args:
            task_id (str): Task ID
        
        Returns:
            List[QAPair]: List of Q&A pairs
        """
        with self.lock:
            if task_id not in self.tasks:
                raise ValueError(f"Task {task_id} not found")
            
            task = self.tasks[task_id]
            if task["status"] != "completed":
                raise ValueError(f"Task {task_id} is not completed")
            
            # Load Q&A pairs from file
            qa_file = os.path.join(task["output_dir"], "development_qa.md")
            if not os.path.exists(qa_file):
                return []
            
            # Parse Q&A pairs from markdown
            qa_pairs = []
            with open(qa_file, "r") as f:
                content = f.read()
                
                # Simple parsing of Q&A format
                sections = content.split("## Q")
                for section in sections[1:]:  # Skip header
                    try:
                        question_part = section.split("## A")[0].strip()
                        answer_part = section.split("## A")[1].strip()
                        
                        # Clean up question and answer
                        question = question_part.split("\n", 1)[0].strip()
                        answer = answer_part.split("\n\n")[0].strip()
                        
                        qa_pairs.append(QAPair(question=question, answer=answer))
                    except Exception as e:
                        logger.error(f"Error parsing Q&A pair: {e}")
            
            return qa_pairs
