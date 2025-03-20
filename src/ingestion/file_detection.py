"""
File detection module with complete implementation.

This module provides functionality for detecting and filtering code files.
"""

import os
import logging
import mimetypes
from typing import Dict, Any, List, Optional, Set

logger = logging.getLogger(__name__)

class FileDetector:
    """Detects and filters code files."""
    
    def __init__(self):
        """Initialize file detector."""
        # Initialize mimetypes
        mimetypes.init()
        
        # Define code file extensions by language
        self.code_extensions = {
            'python': ['.py', '.pyx', '.pyi', '.ipynb'],
            'javascript': ['.js', '.jsx', '.mjs', '.cjs'],
            'typescript': ['.ts', '.tsx'],
            'java': ['.java', '.jar', '.class'],
            'c': ['.c', '.h'],
            'cpp': ['.cpp', '.cc', '.cxx', '.hpp', '.hxx', '.h'],
            'csharp': ['.cs'],
            'go': ['.go'],
            'ruby': ['.rb', '.erb'],
            'php': ['.php', '.phtml', '.php5', '.php7'],
            'swift': ['.swift'],
            'rust': ['.rs'],
            'kotlin': ['.kt', '.kts'],
            'scala': ['.scala'],
            'html': ['.html', '.htm', '.xhtml'],
            'css': ['.css', '.scss', '.sass', '.less'],
            'shell': ['.sh', '.bash', '.zsh', '.fish'],
            'sql': ['.sql'],
            'markdown': ['.md', '.markdown'],
            'json': ['.json'],
            'yaml': ['.yml', '.yaml'],
            'xml': ['.xml'],
            'dockerfile': ['Dockerfile'],
            'makefile': ['Makefile', 'makefile'],
            'terraform': ['.tf', '.tfvars'],
            'powershell': ['.ps1', '.psm1', '.psd1'],
            'r': ['.r', '.R'],
            'perl': ['.pl', '.pm'],
            'lua': ['.lua'],
            'haskell': ['.hs', '.lhs'],
            'elixir': ['.ex', '.exs'],
            'erlang': ['.erl', '.hrl'],
            'clojure': ['.clj', '.cljs', '.cljc'],
            'groovy': ['.groovy', '.gradle'],
            'dart': ['.dart'],
            'julia': ['.jl'],
            'fortran': ['.f', '.f90', '.f95', '.f03', '.f08'],
            'assembly': ['.asm', '.s'],
            'vb': ['.vb', '.vbs'],
            'objectivec': ['.m', '.mm'],
            'cobol': ['.cob', '.cbl'],
            'lisp': ['.lisp', '.lsp', '.l'],
            'prolog': ['.pl', '.pro'],
            'scheme': ['.scm', '.ss'],
            'ada': ['.ada', '.adb', '.ads'],
            'ocaml': ['.ml', '.mli'],
            'matlab': ['.m', '.mat'],
            'pascal': ['.pas', '.p'],
            'fsharp': ['.fs', '.fsi', '.fsx'],
            'crystal': ['.cr'],
            'nim': ['.nim'],
            'zig': ['.zig'],
            'solidity': ['.sol'],
            'webassembly': ['.wasm', '.wat'],
            'graphql': ['.graphql', '.gql'],
            'protobuf': ['.proto'],
            'toml': ['.toml'],
            'ini': ['.ini'],
            'bat': ['.bat', '.cmd'],
            'vue': ['.vue'],
            'svelte': ['.svelte'],
            'elm': ['.elm'],
            'purescript': ['.purs'],
            'reason': ['.re', '.rei'],
            'coffeescript': ['.coffee'],
            'handlebars': ['.hbs', '.handlebars'],
            'pug': ['.pug', '.jade'],
            'stylus': ['.styl'],
            'haml': ['.haml'],
            'ejs': ['.ejs'],
            'twig': ['.twig'],
            'mustache': ['.mustache'],
            'velocity': ['.vm'],
            'thrift': ['.thrift'],
            'cuda': ['.cu', '.cuh'],
            'opencl': ['.cl'],
            'glsl': ['.glsl', '.vert', '.frag'],
            'hlsl': ['.hlsl', '.fx'],
            'metal': ['.metal'],
            'wgsl': ['.wgsl'],
            'bicep': ['.bicep'],
            'hcl': ['.hcl'],
            'dhall': ['.dhall'],
            'nix': ['.nix'],
            'idris': ['.idr'],
            'agda': ['.agda'],
            'coq': ['.v'],
            'lean': ['.lean'],
            'isabelle': ['.thy'],
            'alloy': ['.als'],
            'tla': ['.tla'],
            'z3': ['.z3'],
            'smt': ['.smt2'],
            'verilog': ['.v', '.sv'],
            'vhdl': ['.vhd', '.vhdl'],
            'systemc': ['.sc', '.cpp'],
            'chisel': ['.scala'],
            'bluespec': ['.bsv'],
            'other': []
        }
        
        # Define binary file extensions to exclude
        self.binary_extensions = [
            '.exe', '.dll', '.so', '.dylib', '.obj', '.o', '.a', '.lib',
            '.bin', '.dat', '.db', '.sqlite', '.sqlite3', '.db3',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.ico',
            '.mp3', '.mp4', '.wav', '.avi', '.mov', '.mkv', '.flv',
            '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.pyc', '.pyo', '.pyd', '.class', '.jar', '.war', '.ear',
            '.ttf', '.otf', '.woff', '.woff2', '.eot'
        ]
        
        # Define directories to exclude
        self.exclude_dirs = [
            '.git', '.svn', '.hg', '.bzr', 'CVS',
            'node_modules', 'venv', 'env', '.env', '.venv',
            '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache',
            'dist', 'build', 'target', 'out', 'bin', 'obj',
            '.idea', '.vscode', '.vs', '.gradle', '.m2',
            'vendor', 'bower_components', 'jspm_packages',
            '.next', '.nuxt', '.output', '.cache', '.parcel-cache',
            '.yarn', '.pnpm-store'
        ]
    
    def detect_code_files(self, directory_path: str, max_size: int = 1024 * 1024) -> List[Dict[str, Any]]:
        """
        Detect code files in directory.
        
        Args:
            directory_path (str): Directory path
            max_size (int, optional): Maximum file size in bytes
            
        Returns:
            List[Dict[str, Any]]: List of code files
        """
        try:
            logger.info(f"Detecting code files in: {directory_path}")
            
            if not os.path.exists(directory_path):
                raise FileNotFoundError(f"Directory not found: {directory_path}")
            
            if not os.path.isdir(directory_path):
                raise NotADirectoryError(f"Not a directory: {directory_path}")
            
            code_files = []
            
            for root, dirs, files in os.walk(directory_path):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Skip if not a file
                    if not os.path.isfile(file_path):
                        continue
                    
                    # Skip if too large
                    file_size = os.path.getsize(file_path)
                    if file_size > max_size:
                        logger.debug(f"Skipping large file: {file_path} ({file_size} bytes)")
                        continue
                    
                    # Skip binary files
                    if self._is_binary_file(file_path):
                        continue
                    
                    # Detect language
                    language = self._detect_language(file_path)
                    if language:
                        code_files.append({
                            "path": file_path,
                            "language": language,
                            "size": file_size,
                            "relative_path": os.path.relpath(file_path, directory_path)
                        })
            
            logger.info(f"Detected {len(code_files)} code files")
            return code_files
        except Exception as e:
            logger.error(f"Error detecting code files: {e}")
            raise Exception(f"Failed to detect code files: {e}")
    
    def filter_files(self, files: List[Dict[str, Any]], languages: Optional[List[str]] = None, 
                    exclude_patterns: Optional[List[str]] = None, max_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Filter code files.
        
        Args:
            files (List[Dict[str, Any]]): List of code files
            languages (List[str], optional): List of languages to include
            exclude_patterns (List[str], optional): List of patterns to exclude
            max_size (int, optional): Maximum file size in bytes
            
        Returns:
            List[Dict[str, Any]]: Filtered list of code files
        """
        try:
            logger.info(f"Filtering {len(files)} code files")
            
            filtered_files = files.copy()
            
            # Filter by language
            if languages:
                filtered_files = [f for f in filtered_files if f.get("language") in languages]
            
            # Filter by exclude patterns
            if exclude_patterns:
                for pattern in exclude_patterns:
                    filtered_files = [f for f in filtered_files if pattern not in f.get("path")]
            
            # Filter by size
            if max_size:
                filtered_files = [f for f in filtered_files if f.get("size", 0) <= max_size]
            
            logger.info(f"Filtered to {len(filtered_files)} code files")
            return filtered_files
        except Exception as e:
            logger.error(f"Error filtering code files: {e}")
            raise Exception(f"Failed to filter code files: {e}")
    
    def _detect_language(self, file_path: str) -> Optional[str]:
        """
        Detect programming language of file.
        
        Args:
            file_path (str): File path
            
        Returns:
            Optional[str]: Detected language or None
        """
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()
        
        # Check if file name matches any language
        for language, extensions in self.code_extensions.items():
            if file_name in extensions or file_ext in extensions:
                return language
        
        # Check if file has a shebang
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
                if first_line.startswith('#!'):
                    if 'python' in first_line:
                        return 'python'
                    elif 'node' in first_line or 'javascript' in first_line:
                        return 'javascript'
                    elif 'bash' in first_line or 'sh' in first_line:
                        return 'shell'
                    elif 'ruby' in first_line:
                        return 'ruby'
                    elif 'perl' in first_line:
                        return 'perl'
                    elif 'php' in first_line:
                        return 'php'
        except Exception:
            pass
        
        # Check mimetype
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            if mime_type.startswith('text/'):
                return 'other'
            
            # Map mime types to languages
            mime_to_lang = {
                'application/javascript': 'javascript',
                'application/json': 'json',
                'application/xml': 'xml',
                'text/html': 'html',
                'text/css': 'css',
                'text/x-python': 'python',
                'text/x-java': 'java',
                'text/x-c': 'c',
                'text/x-c++': 'cpp',
                'text/x-csharp': 'csharp',
                'text/x-go': 'go',
                'text/x-ruby': 'ruby',
                'text/x-php': 'php',
                'text/x-swift': 'swift',
                'text/x-rust': 'rust',
                'text/x-kotlin': 'kotlin',
                'text/x-scala': 'scala',
                'text/markdown': 'markdown',
                'text/x-yaml': 'yaml',
                'text/x-shellscript': 'shell'
            }
            
            if mime_type in mime_to_lang:
                return mime_to_lang[mime_type]
        
        # Try to detect if it's a text file
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.read(1024)  # Read a small chunk
                return 'other'  # If we got here, it's probably a text file
        except Exception:
            return None  # Not a text file
    
    def _is_binary_file(self, file_path: str) -> bool:
        """
        Check if file is binary.
        
        Args:
            file_path (str): File path
            
        Returns:
            bool: True if binary, False otherwise
        """
        # Check extension
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext in self.binary_extensions:
            return True
        
        # Check content (read first few bytes)
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                # Count null bytes
                null_count = chunk.count(b'\x00')
                # If more than 10% are null bytes, it's probably binary
                return null_count > len(chunk) / 10
        except Exception:
            # If we can't read the file, assume it's binary
            return True
