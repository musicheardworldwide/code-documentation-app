"""
File detection module.

This module provides functionality for detecting and filtering code files.
"""

import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class FileDetector:
    """Detects and filters code files."""
    
    # Extensions for code files
    CODE_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.go': 'go',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.rs': 'rust',
        '.scala': 'scala',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.less': 'less'
    }
    
    # Directories to exclude
    EXCLUDE_DIRS = [
        'node_modules',
        'venv',
        '.git',
        '.github',
        '__pycache__',
        'dist',
        'build',
        '.vscode',
        '.idea',
        'vendor',
        'env',
        '.env'
    ]
    
    def detect_code_files(self, directory: str) -> List[Dict[str, Any]]:
        """
        Detect code files in directory.
        
        Args:
            directory (str): Directory to scan
            
        Returns:
            List[Dict[str, Any]]: List of code files with metadata
        """
        code_files = []
        
        for root, dirs, files in os.walk(directory):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Check if file is a code file
                if self.is_code_file(file_path):
                    # Get language from extension
                    _, ext = os.path.splitext(file_path)
                    language = self.CODE_EXTENSIONS.get(ext.lower(), 'unknown')
                    
                    # Add file to list
                    code_files.append({
                        'path': file_path,
                        'language': language,
                        'size': os.path.getsize(file_path)
                    })
        
        return code_files
    
    def is_code_file(self, file_path: str) -> bool:
        """
        Check if file is a code file.
        
        Args:
            file_path (str): Path to file
            
        Returns:
            bool: True if file is a code file, False otherwise
        """
        # Check if file is in excluded directory
        for exclude_dir in self.EXCLUDE_DIRS:
            if f"/{exclude_dir}/" in file_path or file_path.startswith(f"{exclude_dir}/"):
                return False
        
        # Check extension
        _, ext = os.path.splitext(file_path)
        return ext.lower() in self.CODE_EXTENSIONS
