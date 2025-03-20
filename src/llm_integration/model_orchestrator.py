"""
Model orchestrator module with Ollama integration.

This module orchestrates the different LLM models for code documentation using Ollama.
"""

import logging
import os
from typing import Dict, Any, Optional, List

from src.llm_integration.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class ModelOrchestrator:
    """Orchestrates different LLM models for code documentation using Ollama."""
    
    def __init__(self):
        """Initialize model orchestrator."""
        self.config = None
        self.is_configured = False
        self.ollama_client = None
    
    def update_configuration(self, config: Dict[str, Any]) -> bool:
        """
        Update model configuration.
        
        Args:
            config (Dict[str, Any]): Model configuration
            
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        try:
            # Validate configuration
            required_keys = ['base_url', 'api_key', 'instruct_model', 'reasoning_model', 'embeddings_model']
            for key in required_keys:
                if key not in config:
                    logger.error(f"Missing required configuration key: {key}")
                    return False
            
            # Store configuration
            self.config = config
            
            # Initialize Ollama client
            self.ollama_client = OllamaClient(base_url=config['base_url'])
            
            # Check connection
            if not self.ollama_client.check_connection():
                logger.error("Failed to connect to Ollama API")
                self.is_configured = False
                return False
            
            self.is_configured = True
            logger.info("Model configuration updated successfully")
            return True
        except Exception as e:
            logger.error(f"Error updating model configuration: {e}")
            self.is_configured = False
            return False
    
    def is_ready(self) -> bool:
        """
        Check if model orchestrator is ready.
        
        Returns:
            bool: True if ready, False otherwise
        """
        return self.is_configured and self.ollama_client is not None
    
    def generate_documentation(self, code_snippet: str, context: Optional[str] = None) -> str:
        """
        Generate documentation for code snippet.
        
        Args:
            code_snippet (str): Code snippet to document
            context (str, optional): Additional context
            
        Returns:
            str: Generated documentation
        """
        if not self.is_ready():
            raise Exception("Model orchestrator is not configured")
        
        try:
            # Prepare prompt
            prompt = f"Generate comprehensive documentation for the following code:\n\n```\n{code_snippet}\n```\n\n"
            if context:
                prompt += f"Additional context:\n{context}\n\n"
            prompt += "Documentation:"
            
            # Generate documentation using instruct model
            system_message = (
                "You are an expert code documentation generator. Your task is to create clear, "
                "comprehensive documentation for code snippets. Focus on explaining what the code does, "
                "its parameters, return values, and any important details about its functionality."
            )
            
            documentation = self.ollama_client.generate(
                model=self.config['instruct_model'],
                prompt=prompt,
                system=system_message,
                temperature=0.3
            )
            
            return documentation.strip()
        except Exception as e:
            logger.error(f"Error generating documentation: {e}")
            raise Exception(f"Failed to generate documentation: {e}")
    
    def analyze_code_relationships(self, code_components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze relationships between code components.
        
        Args:
            code_components (List[Dict[str, Any]]): Code components
            
        Returns:
            Dict[str, Any]: Relationship analysis
        """
        if not self.is_ready():
            raise Exception("Model orchestrator is not configured")
        
        try:
            # Prepare components summary
            components_summary = ""
            for i, component in enumerate(code_components[:20]):  # Limit to 20 components to avoid token limits
                component_type = component.get('type', 'component')
                name = component.get('name', f'Component {i}')
                content = component.get('content', '')
                
                # Truncate content if too long
                if len(content) > 500:
                    content = content[:500] + "..."
                
                components_summary += f"## {component_type.upper()}: {name}\n```\n{content}\n```\n\n"
            
            # Prepare prompt
            prompt = (
                "Analyze the relationships between the following code components:\n\n"
                f"{components_summary}\n\n"
                "Identify dependencies, inheritance relationships, and function calls between components. "
                "Format your response as JSON with the following structure:\n"
                "{\n"
                '  "relationships": [\n'
                '    {"source": "ComponentName1", "target": "ComponentName2", "type": "imports/calls/inherits", "description": "Description of relationship"}\n'
                "  ],\n"
                '  "insights": ["Insight 1", "Insight 2"]\n'
                "}"
            )
            
            # Generate analysis using reasoning model
            system_message = (
                "You are an expert code analyzer. Your task is to analyze relationships between code components "
                "and provide insights about the code structure. Focus on identifying dependencies, inheritance "
                "relationships, and function calls. Provide your analysis in the requested JSON format."
            )
            
            analysis_text = self.ollama_client.generate(
                model=self.config['reasoning_model'],
                prompt=prompt,
                system=system_message,
                temperature=0.2
            )
            
            # Parse JSON response
            try:
                # Find JSON in the response
                start_idx = analysis_text.find('{')
                end_idx = analysis_text.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = analysis_text[start_idx:end_idx]
                    analysis = json.loads(json_str)
                else:
                    # Fallback if JSON parsing fails
                    analysis = {
                        "relationships": [],
                        "insights": ["Failed to parse relationships from model output"]
                    }
            except Exception as json_error:
                logger.error(f"Error parsing relationship analysis JSON: {json_error}")
                analysis = {
                    "relationships": [],
                    "insights": ["Failed to parse relationships from model output"]
                }
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing code relationships: {e}")
            raise Exception(f"Failed to analyze code relationships: {e}")
    
    def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings for text.
        
        Args:
            text (str): Text to embed
            
        Returns:
            List[float]: Embeddings
        """
        if not self.is_ready():
            raise Exception("Model orchestrator is not configured")
        
        try:
            # Generate embeddings
            embeddings = self.ollama_client.embeddings(
                model=self.config['embeddings_model'],
                text=text
            )
            
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise Exception(f"Failed to generate embeddings: {e}")
    
    def generate_qa_pairs(self, code_analysis: Dict[str, Any], count: int = 50) -> List[Dict[str, str]]:
        """
        Generate Q&A pairs for development.
        
        Args:
            code_analysis (Dict[str, Any]): Code analysis results
            count (int, optional): Number of Q&A pairs to generate
            
        Returns:
            List[Dict[str, str]]: List of Q&A pairs
        """
        if not self.is_ready():
            raise Exception("Model orchestrator is not configured")
        
        try:
            # Prepare code analysis summary
            files_count = code_analysis.get('file_count', 0)
            functions_count = code_analysis.get('function_count', 0)
            classes_count = code_analysis.get('class_count', 0)
            
            # Get sample files, functions, and classes
            files = code_analysis.get('files', [])[:5]  # Limit to 5 samples
            functions = code_analysis.get('functions', [])[:10]  # Limit to 10 samples
            classes = code_analysis.get('classes', [])[:5]  # Limit to 5 samples
            
            # Format samples
            files_summary = "\n".join([f"- {file.get('path', 'Unknown file')}" for file in files])
            functions_summary = "\n".join([f"- {func.get('name', 'Unknown function')}" for func in functions])
            classes_summary = "\n".join([f"- {cls.get('name', 'Unknown class')}" for cls in classes])
            
            # Prepare prompt
            prompt = (
                f"Generate {count} question and answer pairs about development and feature changes for a codebase with the following characteristics:\n\n"
                f"- {files_count} files\n"
                f"- {functions_count} functions\n"
                f"- {classes_count} classes\n\n"
                "Sample files:\n"
                f"{files_summary}\n\n"
                "Sample functions:\n"
                f"{functions_summary}\n\n"
                "Sample classes:\n"
                f"{classes_summary}\n\n"
                "The questions should cover topics like:\n"
                "1. How to modify or extend existing features\n"
                "2. How to add new features\n"
                "3. Understanding the architecture and design patterns\n"
                "4. Best practices for working with this codebase\n"
                "5. Common development tasks and workflows\n\n"
                "Format each Q&A pair as:\n"
                "Q: [Question]\n"
                "A: [Answer]\n\n"
                "Generate comprehensive, detailed answers that would be helpful to developers."
            )
            
            # Generate Q&A pairs using reasoning model
            system_message = (
                "You are an expert software developer with deep knowledge of software architecture and development practices. "
                "Your task is to generate helpful question and answer pairs for developers who need to understand, modify, "
                "or extend a codebase. Focus on practical, actionable information that would help developers work effectively "
                "with the code."
            )
            
            qa_text = self.ollama_client.generate(
                model=self.config['reasoning_model'],
                prompt=prompt,
                system=system_message,
                temperature=0.7
            )
            
            # Parse Q&A pairs
            qa_pairs = []
            qa_blocks = qa_text.split("Q: ")
            
            for block in qa_blocks[1:]:  # Skip the first split which is empty
                try:
                    question_part, answer_part = block.split("A: ", 1)
                    question = question_part.strip()
                    answer = answer_part.strip()
                    
                    # Clean up answer if it contains another Q:
                    if "Q: " in answer:
                        answer = answer.split("Q: ")[0].strip()
                    
                    qa_pairs.append({
                        "question": question,
                        "answer": answer
                    })
                except Exception as parse_error:
                    logger.error(f"Error parsing Q&A pair: {parse_error}")
            
            # Ensure we have the requested number of pairs
            while len(qa_pairs) < count and len(qa_pairs) > 0:
                # Duplicate existing pairs if we don't have enough
                qa_pairs.append(qa_pairs[len(qa_pairs) % len(qa_pairs)])
            
            # Limit to requested count
            return qa_pairs[:count]
        except Exception as e:
            logger.error(f"Error generating Q&A pairs: {e}")
            raise Exception(f"Failed to generate Q&A pairs: {e}")
