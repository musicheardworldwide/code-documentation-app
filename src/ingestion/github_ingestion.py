"""
GitHub ingestion module with complete implementation.

This module provides functionality for cloning and analyzing GitHub repositories.
"""

import os
import logging
import tempfile
import shutil
from typing import Dict, Any, Optional
import git

logger = logging.getLogger(__name__)

class GitHubIngestion:
    """Handles ingestion of GitHub repositories."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize GitHub ingestion.
        
        Args:
            temp_dir (str, optional): Temporary directory for cloning repositories
        """
        self.temp_dir = temp_dir or os.path.join(tempfile.gettempdir(), "code_documentation", "github")
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def clone_repository(self, repo_url: str, branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Clone GitHub repository.
        
        Args:
            repo_url (str): GitHub repository URL
            branch (str, optional): Branch to clone
            
        Returns:
            Dict[str, Any]: Repository information
        """
        try:
            logger.info(f"Cloning repository: {repo_url}")
            
            # Extract repository name from URL
            repo_name = repo_url.split("/")[-1]
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]
            
            # Create unique directory for this repository
            repo_dir = os.path.join(self.temp_dir, repo_name)
            
            # Remove directory if it already exists
            if os.path.exists(repo_dir):
                shutil.rmtree(repo_dir)
            
            # Clone repository
            if branch:
                repo = git.Repo.clone_from(repo_url, repo_dir, branch=branch)
            else:
                repo = git.Repo.clone_from(repo_url, repo_dir)
            
            # Get repository information
            repo_info = {
                "name": repo_name,
                "url": repo_url,
                "path": repo_dir,
                "branch": branch or repo.active_branch.name,
                "commit": repo.head.commit.hexsha,
                "commit_message": repo.head.commit.message.strip(),
                "commit_date": repo.head.commit.committed_datetime.isoformat(),
                "author": f"{repo.head.commit.author.name} <{repo.head.commit.author.email}>",
                "size": self._get_directory_size(repo_dir)
            }
            
            logger.info(f"Repository cloned successfully: {repo_dir}")
            return repo_info
        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            raise Exception(f"Failed to clone repository: {e}")
    
    def analyze_repository(self, repo_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze repository structure.
        
        Args:
            repo_info (Dict[str, Any]): Repository information
            
        Returns:
            Dict[str, Any]: Repository analysis
        """
        try:
            logger.info(f"Analyzing repository structure: {repo_info['path']}")
            
            repo_path = repo_info["path"]
            
            # Get file count
            file_count = 0
            for root, _, files in os.walk(repo_path):
                # Skip .git directory
                if ".git" in root:
                    continue
                file_count += len(files)
            
            # Get directory count
            dir_count = 0
            for root, dirs, _ in os.walk(repo_path):
                # Skip .git directory
                if ".git" in root:
                    continue
                # Remove .git from dirs to avoid counting it
                if ".git" in dirs:
                    dirs.remove(".git")
                dir_count += len(dirs)
            
            # Detect common project files
            has_readme = os.path.exists(os.path.join(repo_path, "README.md")) or os.path.exists(os.path.join(repo_path, "README"))
            has_license = os.path.exists(os.path.join(repo_path, "LICENSE")) or os.path.exists(os.path.join(repo_path, "LICENSE.md"))
            has_gitignore = os.path.exists(os.path.join(repo_path, ".gitignore"))
            has_package_json = os.path.exists(os.path.join(repo_path, "package.json"))
            has_requirements_txt = os.path.exists(os.path.join(repo_path, "requirements.txt"))
            has_setup_py = os.path.exists(os.path.join(repo_path, "setup.py"))
            has_dockerfile = os.path.exists(os.path.join(repo_path, "Dockerfile"))
            has_docker_compose = os.path.exists(os.path.join(repo_path, "docker-compose.yml")) or os.path.exists(os.path.join(repo_path, "docker-compose.yaml"))
            
            # Detect programming languages
            languages = self._detect_languages(repo_path)
            
            # Create repository analysis
            repo_analysis = {
                "file_count": file_count,
                "directory_count": dir_count,
                "has_readme": has_readme,
                "has_license": has_license,
                "has_gitignore": has_gitignore,
                "has_package_json": has_package_json,
                "has_requirements_txt": has_requirements_txt,
                "has_setup_py": has_setup_py,
                "has_dockerfile": has_dockerfile,
                "has_docker_compose": has_docker_compose,
                "languages": languages
            }
            
            logger.info(f"Repository analysis completed: {repo_info['path']}")
            return repo_analysis
        except Exception as e:
            logger.error(f"Error analyzing repository: {e}")
            raise Exception(f"Failed to analyze repository: {e}")
    
    def cleanup(self, repo_info: Optional[Dict[str, Any]] = None):
        """
        Clean up temporary files.
        
        Args:
            repo_info (Dict[str, Any], optional): Repository information
        """
        try:
            if repo_info and "path" in repo_info:
                # Remove specific repository
                repo_path = repo_info["path"]
                if os.path.exists(repo_path):
                    logger.info(f"Removing repository: {repo_path}")
                    shutil.rmtree(repo_path)
            else:
                # Remove all repositories
                logger.info(f"Removing all repositories in: {self.temp_dir}")
                if os.path.exists(self.temp_dir):
                    shutil.rmtree(self.temp_dir)
                    os.makedirs(self.temp_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Error cleaning up: {e}")
    
    def _get_directory_size(self, path: str) -> int:
        """
        Get directory size in bytes.
        
        Args:
            path (str): Directory path
            
        Returns:
            int: Directory size in bytes
        """
        total_size = 0
        for root, _, files in os.walk(path):
            # Skip .git directory
            if ".git" in root:
                continue
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
        return total_size
    
    def _detect_languages(self, repo_path: str) -> Dict[str, int]:
        """
        Detect programming languages in repository.
        
        Args:
            repo_path (str): Repository path
            
        Returns:
            Dict[str, int]: Language counts
        """
        language_extensions = {
            "python": [".py", ".pyx", ".pyi"],
            "javascript": [".js", ".jsx", ".mjs"],
            "typescript": [".ts", ".tsx"],
            "java": [".java"],
            "c": [".c", ".h"],
            "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".hxx"],
            "csharp": [".cs"],
            "go": [".go"],
            "ruby": [".rb"],
            "php": [".php"],
            "swift": [".swift"],
            "rust": [".rs"],
            "kotlin": [".kt", ".kts"],
            "scala": [".scala"],
            "html": [".html", ".htm"],
            "css": [".css"],
            "shell": [".sh", ".bash"],
            "sql": [".sql"],
            "markdown": [".md", ".markdown"],
            "json": [".json"],
            "yaml": [".yml", ".yaml"],
            "xml": [".xml"],
            "dockerfile": ["Dockerfile"],
            "other": []
        }
        
        language_counts = {lang: 0 for lang in language_extensions}
        
        for root, _, files in os.walk(repo_path):
            # Skip .git directory
            if ".git" in root:
                continue
            
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path):
                    # Check if file matches any language
                    matched = False
                    for lang, extensions in language_extensions.items():
                        if file in extensions or any(file.endswith(ext) for ext in extensions):
                            language_counts[lang] += 1
                            matched = True
                            break
                    
                    # Count as other if no match
                    if not matched:
                        language_counts["other"] += 1
        
        # Remove languages with zero count
        return {lang: count for lang, count in language_counts.items() if count > 0}
