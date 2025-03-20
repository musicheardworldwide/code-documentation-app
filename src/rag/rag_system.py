"""
RAG system module with complete implementation.

This module implements Retrieval-Augmented Generation for code documentation.
"""

import os
import logging
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

class RAGSystem:
    """Implements Retrieval-Augmented Generation for code documentation."""
    
    def __init__(self, model_orchestrator=None, vector_db_path: Optional[str] = None):
        """
        Initialize RAG system.
        
        Args:
            model_orchestrator: Model orchestrator for LLM integration
            vector_db_path (str, optional): Path to vector database
        """
        self.model_orchestrator = model_orchestrator
        self.vector_db_path = vector_db_path or "vector_db"
        self.client = None
        self.collection = None
        self.is_indexed = False
        self._initialize_vector_db()
    
    def _initialize_vector_db(self):
        """Initialize vector database."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(self.vector_db_path, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(path=self.vector_db_path)
            
            # Check if collection exists
            try:
                self.collection = self.client.get_collection("code_documentation")
                self.is_indexed = self.collection.count() > 0
                logger.info(f"Vector database loaded with {self.collection.count()} documents")
            except Exception:
                # Create new collection
                self.collection = self.client.create_collection(
                    name="code_documentation",
                    metadata={"description": "Code documentation embeddings"}
                )
                logger.info("Created new vector database collection")
        except Exception as e:
            logger.error(f"Error initializing vector database: {e}")
            raise Exception(f"Failed to initialize vector database: {e}")
    
    def index_codebase(self, code_path: str, analysis_results: Dict[str, Any]) -> bool:
        """
        Index codebase for retrieval.
        
        Args:
            code_path (str): Path to code directory
            analysis_results (Dict[str, Any]): Code analysis results
            
        Returns:
            bool: True if indexing was successful, False otherwise
        """
        try:
            logger.info(f"Indexing codebase in {code_path}")
            
            if not self.model_orchestrator or not self.model_orchestrator.is_ready():
                logger.error("Model orchestrator is not ready")
                return False
            
            # Clear existing collection
            self.collection.delete(where={})
            
            # Process files
            files = analysis_results.get("files", [])
            logger.info(f"Processing {len(files)} files for indexing")
            
            # Process functions
            functions = analysis_results.get("functions", [])
            logger.info(f"Processing {len(functions)} functions for indexing")
            
            # Process classes
            classes = analysis_results.get("classes", [])
            logger.info(f"Processing {len(classes)} classes for indexing")
            
            # Create chunks for indexing
            chunks = []
            
            # Add file chunks
            for file_info in files:
                file_path = file_info.get("path", "")
                language = file_info.get("language", "unknown")
                
                # Skip if file is too large
                if file_info.get("size", 0) > 1024 * 1024:  # 1MB
                    logger.warning(f"Skipping large file: {file_path}")
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Create file chunk
                    chunks.append({
                        "id": f"file:{file_path}",
                        "content": content,
                        "metadata": {
                            "type": "file",
                            "path": file_path,
                            "language": language,
                            "size": file_info.get("size", 0)
                        }
                    })
                except Exception as e:
                    logger.error(f"Error reading file {file_path}: {e}")
            
            # Add function chunks
            for func in functions:
                func_name = func.get("name", "")
                file_path = func.get("file_path", "")
                body = func.get("body", "")
                
                # Create function chunk
                chunks.append({
                    "id": f"function:{file_path}:{func_name}",
                    "content": body,
                    "metadata": {
                        "type": "function",
                        "name": func_name,
                        "file_path": file_path,
                        "params": func.get("params", []),
                        "docstring": func.get("docstring", "")
                    }
                })
            
            # Add class chunks
            for cls in classes:
                class_name = cls.get("name", "")
                file_path = cls.get("file_path", "")
                body = cls.get("body", "")
                
                # Create class chunk
                chunks.append({
                    "id": f"class:{file_path}:{class_name}",
                    "content": body,
                    "metadata": {
                        "type": "class",
                        "name": class_name,
                        "file_path": file_path,
                        "bases": cls.get("bases", []),
                        "docstring": cls.get("docstring", "")
                    }
                })
                
                # Add method chunks
                for method in cls.get("methods", []):
                    method_name = method.get("name", "")
                    method_body = method.get("body", "")
                    
                    # Create method chunk
                    chunks.append({
                        "id": f"method:{file_path}:{class_name}.{method_name}",
                        "content": method_body,
                        "metadata": {
                            "type": "method",
                            "name": f"{class_name}.{method_name}",
                            "class_name": class_name,
                            "file_path": file_path,
                            "params": method.get("params", []),
                            "docstring": method.get("docstring", "")
                        }
                    })
            
            # Process chunks in batches to avoid memory issues
            batch_size = 50
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]
                
                # Generate embeddings for batch
                ids = []
                documents = []
                metadatas = []
                embeddings = []
                
                for chunk in batch:
                    # Generate embedding
                    try:
                        embedding = self.model_orchestrator.generate_embeddings(chunk["content"])
                        
                        ids.append(chunk["id"])
                        documents.append(chunk["content"])
                        metadatas.append(chunk["metadata"])
                        embeddings.append(embedding)
                    except Exception as e:
                        logger.error(f"Error generating embedding for {chunk['id']}: {e}")
                
                # Add to collection
                if ids:
                    self.collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas,
                        embeddings=embeddings
                    )
                
                logger.info(f"Indexed batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")
            
            self.is_indexed = True
            logger.info(f"Indexing completed with {self.collection.count()} documents")
            return True
        except Exception as e:
            logger.error(f"Error indexing codebase: {e}")
            self.is_indexed = False
            return False
    
    def generate_answer(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Generate answer for query using RAG.
        
        Args:
            query (str): Query text
            max_results (int, optional): Maximum number of results
            
        Returns:
            Dict[str, Any]: Generated answer with context
        """
        if not self.is_indexed:
            raise Exception("Codebase is not indexed")
        
        if not self.model_orchestrator or not self.model_orchestrator.is_ready():
            raise Exception("Model orchestrator is not ready")
        
        try:
            # Generate query embedding
            query_embedding = self.model_orchestrator.generate_embeddings(query)
            
            # Query collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # Extract results
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            
            # Prepare context
            context = []
            for i in range(len(documents)):
                context.append({
                    "content": documents[i],
                    "metadata": metadatas[i],
                    "distance": distances[i]
                })
            
            # Generate answer
            context_text = "\n\n".join([
                f"--- {ctx['metadata']['type'].upper()}: {ctx['metadata'].get('name', ctx['metadata'].get('path', 'Unknown'))}\n{ctx['content']}"
                for ctx in context
            ])
            
            prompt = (
                f"Answer the following question about the codebase using the provided context:\n\n"
                f"Question: {query}\n\n"
                f"Context:\n{context_text}\n\n"
                f"Answer:"
            )
            
            system_message = (
                "You are an expert code documentation assistant. Your task is to answer questions about "
                "a codebase using the provided context. Focus on providing accurate, helpful information "
                "based solely on the context provided. If the context doesn't contain enough information "
                "to answer the question, acknowledge the limitations of the available information."
            )
            
            answer = self.model_orchestrator.ollama_client.generate(
                model=self.model_orchestrator.config['reasoning_model'],
                prompt=prompt,
                system=system_message,
                temperature=0.3
            )
            
            return {
                "query": query,
                "answer": answer.strip(),
                "context": context
            }
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise Exception(f"Failed to generate answer: {e}")
    
    def search_code(self, query: str, max_results: int = 10, filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search code using semantic similarity.
        
        Args:
            query (str): Query text
            max_results (int, optional): Maximum number of results
            filter_type (str, optional): Filter by type (file, function, class, method)
            
        Returns:
            List[Dict[str, Any]]: Search results
        """
        if not self.is_indexed:
            raise Exception("Codebase is not indexed")
        
        if not self.model_orchestrator or not self.model_orchestrator.is_ready():
            raise Exception("Model orchestrator is not ready")
        
        try:
            # Generate query embedding
            query_embedding = self.model_orchestrator.generate_embeddings(query)
            
            # Prepare filter
            where_filter = {}
            if filter_type:
                where_filter = {"type": filter_type}
            
            # Query collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results,
                where=where_filter if where_filter else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Extract results
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            
            # Prepare search results
            search_results = []
            for i in range(len(documents)):
                search_results.append({
                    "content": documents[i],
                    "metadata": metadatas[i],
                    "distance": distances[i]
                })
            
            return search_results
        except Exception as e:
            logger.error(f"Error searching code: {e}")
            raise Exception(f"Failed to search code: {e}")
    
    def get_similar_code(self, code_snippet: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar code snippets.
        
        Args:
            code_snippet (str): Code snippet
            max_results (int, optional): Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: Similar code snippets
        """
        if not self.is_indexed:
            raise Exception("Codebase is not indexed")
        
        if not self.model_orchestrator or not self.model_orchestrator.is_ready():
            raise Exception("Model orchestrator is not ready")
        
        try:
            # Generate snippet embedding
            snippet_embedding = self.model_orchestrator.generate_embeddings(code_snippet)
            
            # Query collection
            results = self.collection.query(
                query_embeddings=[snippet_embedding],
                n_results=max_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # Extract results
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            
            # Prepare similar snippets
            similar_snippets = []
            for i in range(len(documents)):
                similar_snippets.append({
                    "content": documents[i],
                    "metadata": metadatas[i],
                    "distance": distances[i]
                })
            
            return similar_snippets
        except Exception as e:
            logger.error(f"Error finding similar code: {e}")
            raise Exception(f"Failed to find similar code: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get RAG system statistics.
        
        Returns:
            Dict[str, Any]: Statistics
        """
        try:
            # Get collection count
            count = self.collection.count() if self.collection else 0
            
            # Get type counts
            type_counts = {
                "file": 0,
                "function": 0,
                "class": 0,
                "method": 0
            }
            
            if self.collection:
                for type_name in type_counts.keys():
                    try:
                        type_counts[type_name] = self.collection.count(where={"type": type_name})
                    except Exception:
                        pass
            
            return {
                "total_documents": count,
                "is_indexed": self.is_indexed,
                "type_counts": type_counts,
                "vector_db_path": self.vector_db_path
            }
        except Exception as e:
            logger.error(f"Error getting RAG stats: {e}")
            return {
                "total_documents": 0,
                "is_indexed": self.is_indexed,
                "type_counts": {"file": 0, "function": 0, "class": 0, "method": 0},
                "vector_db_path": self.vector_db_path,
                "error": str(e)
            }
