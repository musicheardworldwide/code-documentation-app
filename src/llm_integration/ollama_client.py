"""
LLM integration with Ollama.

This module provides integration with Ollama for LLM capabilities.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama client.
        
        Args:
            base_url (str): Base URL for Ollama API
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def generate(
        self, 
        model: str, 
        prompt: str, 
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text using Ollama.
        
        Args:
            model (str): Model name
            prompt (str): Prompt text
            system (str, optional): System message
            temperature (float): Sampling temperature
            max_tokens (int, optional): Maximum tokens to generate
            
        Returns:
            str: Generated text
        """
        try:
            url = f"{self.base_url}/api/generate"
            
            payload = {
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
            }
            
            if system:
                payload["system"] = system
                
            if max_tokens:
                payload["max_tokens"] = max_tokens
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            # Ollama streams responses, collect all parts
            full_response = ""
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'response' in data:
                        full_response += data['response']
                    
                    # Check if done
                    if data.get('done', False):
                        break
            
            return full_response
        except Exception as e:
            logger.error(f"Error generating text with Ollama: {e}")
            raise Exception(f"Failed to generate text with Ollama: {e}")
    
    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Chat with Ollama.
        
        Args:
            model (str): Model name
            messages (List[Dict[str, str]]): Chat messages
            temperature (float): Sampling temperature
            max_tokens (int, optional): Maximum tokens to generate
            
        Returns:
            str: Generated response
        """
        try:
            url = f"{self.base_url}/api/chat"
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
            
            if max_tokens:
                payload["max_tokens"] = max_tokens
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data['message']['content']
        except Exception as e:
            logger.error(f"Error chatting with Ollama: {e}")
            raise Exception(f"Failed to chat with Ollama: {e}")
    
    def embeddings(self, model: str, text: str) -> List[float]:
        """
        Generate embeddings using Ollama.
        
        Args:
            model (str): Model name
            text (str): Text to embed
            
        Returns:
            List[float]: Embeddings
        """
        try:
            url = f"{self.base_url}/api/embeddings"
            
            payload = {
                "model": model,
                "prompt": text
            }
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data['embedding']
        except Exception as e:
            logger.error(f"Error generating embeddings with Ollama: {e}")
            raise Exception(f"Failed to generate embeddings with Ollama: {e}")
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models.
        
        Returns:
            List[Dict[str, Any]]: List of models
        """
        try:
            url = f"{self.base_url}/api/tags"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            return data['models']
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            raise Exception(f"Failed to list models: {e}")
    
    def check_connection(self) -> bool:
        """
        Check connection to Ollama.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            self.list_models()
            return True
        except Exception:
            return False
