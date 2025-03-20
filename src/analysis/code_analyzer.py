"""
Code analyzer module with complete implementation.

This module provides functionality for analyzing code structure and dependencies.
"""

import os
import re
import ast
import logging
import json
from typing import Dict, Any, List, Optional, Set, Tuple
import networkx as nx
from collections import defaultdict

logger = logging.getLogger(__name__)

class CodeAnalyzer:
    """Analyzes code structure and dependencies."""
    
    def __init__(self):
        """Initialize code analyzer."""
        self.supported_languages = {
            'python': self._analyze_python,
            'javascript': self._analyze_javascript,
            'typescript': self._analyze_typescript,
            'java': self._analyze_java,
            'cpp': self._analyze_cpp,
            'c': self._analyze_c
        }
    
    def analyze(self, code_path: str) -> Dict[str, Any]:
        """
        Analyze code structure.
        
        Args:
            code_path (str): Path to code directory
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        try:
            logger.info(f"Analyzing code structure in {code_path}")
            
            # Find all code files
            from src.ingestion.file_detection import FileDetector
            file_detector = FileDetector()
            code_files = file_detector.detect_code_files(code_path)
            
            # Initialize results
            results = {
                "file_count": len(code_files),
                "function_count": 0,
                "class_count": 0,
                "code_path": code_path,
                "files": [],
                "functions": [],
                "classes": []
            }
            
            # Analyze each file
            for file_info in code_files:
                file_path = file_info['path']
                language = file_info['language']
                
                # Skip files that are too large (>1MB)
                if file_info['size'] > 1024 * 1024:
                    logger.warning(f"Skipping large file: {file_path} ({file_info['size']} bytes)")
                    continue
                
                # Read file content
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except Exception as e:
                    logger.error(f"Error reading file {file_path}: {e}")
                    continue
                
                # Analyze file based on language
                file_analysis = {
                    "path": file_path,
                    "language": language,
                    "size": file_info['size'],
                    "functions": [],
                    "classes": []
                }
                
                # Use language-specific analyzer if available
                if language in self.supported_languages:
                    try:
                        analyzer_func = self.supported_languages[language]
                        analyzer_func(content, file_analysis)
                    except Exception as e:
                        logger.error(f"Error analyzing {language} file {file_path}: {e}")
                else:
                    # Use generic analyzer for unsupported languages
                    self._analyze_generic(content, file_analysis)
                
                # Update counts
                results["function_count"] += len(file_analysis["functions"])
                results["class_count"] += len(file_analysis["classes"])
                
                # Add file analysis to results
                results["files"].append(file_analysis)
                
                # Add functions and classes to global lists
                for func in file_analysis["functions"]:
                    func["file_path"] = file_path
                    results["functions"].append(func)
                
                for cls in file_analysis["classes"]:
                    cls["file_path"] = file_path
                    results["classes"].append(cls)
            
            return results
        except Exception as e:
            logger.error(f"Error analyzing code structure: {e}")
            raise Exception(f"Failed to analyze code structure: {e}")
    
    def identify_dependencies(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify dependencies between code components.
        
        Args:
            analysis_results (Dict[str, Any]): Analysis results
            
        Returns:
            Dict[str, Any]: Dependency results
        """
        try:
            logger.info("Identifying dependencies between code components")
            
            # Create dependency graph
            dependency_graph = nx.DiGraph()
            
            # Track imports
            import_dependencies = []
            
            # Process each file
            for file_info in analysis_results.get("files", []):
                file_path = file_info["path"]
                language = file_info["language"]
                
                # Add file node
                file_node = f"file:{file_path}"
                dependency_graph.add_node(file_node, type="file", name=os.path.basename(file_path))
                
                # Process imports based on language
                if language == "python":
                    self._process_python_imports(file_path, dependency_graph, import_dependencies)
                elif language in ["javascript", "typescript"]:
                    self._process_js_imports(file_path, dependency_graph, import_dependencies)
                
                # Add function and class nodes
                for func in file_info.get("functions", []):
                    func_node = f"function:{file_path}:{func['name']}"
                    dependency_graph.add_node(func_node, type="function", name=func["name"])
                    dependency_graph.add_edge(file_node, func_node, type="contains")
                
                for cls in file_info.get("classes", []):
                    class_node = f"class:{file_path}:{cls['name']}"
                    dependency_graph.add_node(class_node, type="class", name=cls["name"])
                    dependency_graph.add_edge(file_node, class_node, type="contains")
                    
                    # Add class methods
                    for method in cls.get("methods", []):
                        method_node = f"method:{file_path}:{cls['name']}.{method['name']}"
                        dependency_graph.add_node(method_node, type="method", name=f"{cls['name']}.{method['name']}")
                        dependency_graph.add_edge(class_node, method_node, type="contains")
            
            # Process function calls and references
            function_dependencies = self._identify_function_dependencies(analysis_results, dependency_graph)
            
            # Process class inheritance
            class_dependencies = self._identify_class_dependencies(analysis_results, dependency_graph)
            
            # Generate dependency visualization
            self._generate_dependency_visualization(dependency_graph, analysis_results["code_path"])
            
            return {
                "import_dependencies": import_dependencies,
                "function_dependencies": function_dependencies,
                "class_dependencies": class_dependencies,
                "graph": dependency_graph
            }
        except Exception as e:
            logger.error(f"Error identifying dependencies: {e}")
            raise Exception(f"Failed to identify dependencies: {e}")
    
    def _analyze_python(self, content: str, file_analysis: Dict[str, Any]):
        """
        Analyze Python code.
        
        Args:
            content (str): File content
            file_analysis (Dict[str, Any]): File analysis to update
        """
        try:
            # Parse Python code
            tree = ast.parse(content)
            
            # Extract imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append({"module": name.name, "alias": name.asname})
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for name in node.names:
                        imports.append({"module": f"{module}.{name.name}" if module else name.name, "alias": name.asname})
            
            file_analysis["imports"] = imports
            
            # Extract functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Skip if inside a class
                    if any(isinstance(parent, ast.ClassDef) for parent in ast.iter_fields(node)):
                        continue
                    
                    # Get function parameters
                    params = []
                    for arg in node.args.args:
                        params.append(arg.arg)
                    
                    # Get function docstring
                    docstring = ast.get_docstring(node) or ""
                    
                    # Get function body
                    body_lines = content.splitlines()[node.lineno-1:node.end_lineno]
                    body = "\n".join(body_lines)
                    
                    file_analysis["functions"].append({
                        "name": node.name,
                        "params": params,
                        "docstring": docstring,
                        "body": body,
                        "line_start": node.lineno,
                        "line_end": node.end_lineno
                    })
            
            # Extract classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Get base classes
                    bases = []
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            bases.append(base.id)
                        elif isinstance(base, ast.Attribute):
                            bases.append(f"{base.value.id}.{base.attr}" if hasattr(base.value, 'id') else base.attr)
                    
                    # Get class docstring
                    docstring = ast.get_docstring(node) or ""
                    
                    # Get class methods
                    methods = []
                    for child in node.body:
                        if isinstance(child, ast.FunctionDef):
                            # Get method parameters
                            params = []
                            for arg in child.args.args:
                                if arg.arg != 'self':  # Skip 'self' parameter
                                    params.append(arg.arg)
                            
                            # Get method docstring
                            method_docstring = ast.get_docstring(child) or ""
                            
                            # Get method body
                            body_lines = content.splitlines()[child.lineno-1:child.end_lineno]
                            body = "\n".join(body_lines)
                            
                            methods.append({
                                "name": child.name,
                                "params": params,
                                "docstring": method_docstring,
                                "body": body,
                                "line_start": child.lineno,
                                "line_end": child.end_lineno
                            })
                    
                    # Get class body
                    body_lines = content.splitlines()[node.lineno-1:node.end_lineno]
                    body = "\n".join(body_lines)
                    
                    file_analysis["classes"].append({
                        "name": node.name,
                        "bases": bases,
                        "docstring": docstring,
                        "methods": methods,
                        "body": body,
                        "line_start": node.lineno,
                        "line_end": node.end_lineno
                    })
        except SyntaxError as e:
            logger.error(f"Python syntax error: {e}")
            # Fall back to generic analysis
            self._analyze_generic(content, file_analysis)
    
    def _analyze_javascript(self, content: str, file_analysis: Dict[str, Any]):
        """
        Analyze JavaScript code.
        
        Args:
            content (str): File content
            file_analysis (Dict[str, Any]): File analysis to update
        """
        # Extract imports
        import_regex = r'(?:import|require)\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)|import\s+(?:\*\s+as\s+([a-zA-Z0-9_$]+)|{\s*([^}]+)\s*}|([a-zA-Z0-9_$]+))\s+from\s+[\'"]([^\'"]+)[\'"]'
        imports = []
        
        for match in re.finditer(import_regex, content):
            if match.group(1):  # require or dynamic import
                imports.append({"module": match.group(1), "alias": None})
            elif match.group(5):  # ES6 import
                module = match.group(5)
                if match.group(2):  # import * as name
                    imports.append({"module": module, "alias": match.group(2)})
                elif match.group(3):  # import { name1, name2 }
                    imports.append({"module": module, "alias": match.group(3)})
                elif match.group(4):  # import name
                    imports.append({"module": module, "alias": match.group(4)})
        
        file_analysis["imports"] = imports
        
        # Extract functions
        function_regex = r'(?:function\s+([a-zA-Z0-9_$]+)\s*\(([^)]*)\)|(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*function\s*\([^)]*\))'
        
        for match in re.finditer(function_regex, content):
            # Determine function name
            name = match.group(1) or match.group(3) or match.group(4)
            if not name:
                continue
            
            # Get function parameters
            params = []
            if match.group(2):
                params = [p.strip() for p in match.group(2).split(',') if p.strip()]
            
            # Get function body (simplified)
            line_start = content[:match.start()].count('\n') + 1
            
            # Find opening brace
            open_brace_pos = content.find('{', match.end())
            if open_brace_pos == -1:
                continue
            
            # Find closing brace (naive implementation)
            brace_count = 1
            close_brace_pos = open_brace_pos + 1
            while brace_count > 0 and close_brace_pos < len(content):
                if content[close_brace_pos] == '{':
                    brace_count += 1
                elif content[close_brace_pos] == '}':
                    brace_count -= 1
                close_brace_pos += 1
            
            if close_brace_pos >= len(content):
                close_brace_pos = len(content) - 1
            
            body = content[match.start():close_brace_pos]
            line_end = content[:close_brace_pos].count('\n') + 1
            
            # Extract docstring (JSDoc)
            docstring = ""
            jsdoc_match = re.search(r'/\*\*([\s\S]*?)\*/', content[:match.start()])
            if jsdoc_match and jsdoc_match.end() + 5 >= match.start():
                docstring = jsdoc_match.group(1).strip()
            
            file_analysis["functions"].append({
                "name": name,
                "params": params,
                "docstring": docstring,
                "body": body,
                "line_start": line_start,
                "line_end": line_end
            })
        
        # Extract classes
        class_regex = r'class\s+([a-zA-Z0-9_$]+)(?:\s+extends\s+([a-zA-Z0-9_$.]+))?\s*{'
        
        for match in re.finditer(class_regex, content):
            class_name = match.group(1)
            base_class = match.group(2)
            
            # Get class body (simplified)
            line_start = content[:match.start()].count('\n') + 1
            
            # Find closing brace (naive implementation)
            open_brace_pos = content.find('{', match.end())
            brace_count = 1
            close_brace_pos = open_brace_pos + 1
            while brace_count > 0 and close_brace_pos < len(content):
                if content[close_brace_pos] == '{':
                    brace_count += 1
                elif content[close_brace_pos] == '}':
                    brace_count -= 1
                close_brace_pos += 1
            
            if close_brace_pos >= len(content):
                close_brace_pos = len(content) - 1
            
            class_body = content[match.start():close_brace_pos]
            line_end = content[:close_brace_pos].count('\n') + 1
            
            # Extract docstring (JSDoc)
            docstring = ""
            jsdoc_match = re.search(r'/\*\*([\s\S]*?)\*/', content[:match.start()])
            if jsdoc_match and jsdoc_match.end() + 5 >= match.start():
                docstring = jsdoc_match.group(1).strip()
            
            # Extract methods
            methods = []
            method_regex = r'(?:async\s+)?(?:constructor|[a-zA-Z0-9_$]+)\s*\(([^)]*)\)'
            class_content = content[open_brace_pos:close_brace_pos]
            
            for method_match in re.finditer(method_regex, class_content):
                method_name = method_match.group(0).split('(')[0].strip()
                
                # Get method parameters
                params = []
                if method_match.group(1):
                    params = [p.strip() for p in method_match.group(1).split(',') if p.strip()]
                
                # Get method body (simplified)
                method_start = open_brace_pos + method_match.start()
                method_line_start = content[:method_start].count('\n') + 1
                
                # Find opening brace
                method_open_brace_pos = content.find('{', method_start + method_match.end())
                if method_open_brace_pos == -1:
                    continue
                
                # Find closing brace (naive implementation)
                method_brace_count = 1
                method_close_brace_pos = method_open_brace_pos + 1
                while method_brace_count > 0 and method_close_brace_pos < close_brace_pos:
                    if content[method_close_brace_pos] == '{':
                        method_brace_count += 1
                    elif content[method_close_brace_pos] == '}':
                        method_brace_count -= 1
                    method_close_brace_pos += 1
                
                if method_close_brace_pos >= close_brace_pos:
                    method_close_brace_pos = close_brace_pos - 1
                
                method_body = content[method_start:method_close_brace_pos]
                method_line_end = content[:method_close_brace_pos].count('\n') + 1
                
                # Extract method docstring (JSDoc)
                method_docstring = ""
                method_jsdoc_match = re.search(r'/\*\*([\s\S]*?)\*/', class_content[:method_match.start()])
                if method_jsdoc_match and method_jsdoc_match.end() + 5 >= method_match.start():
                    method_docstring = method_jsdoc_match.group(1).strip()
                
                methods.append({
                    "name": method_name,
                    "params": params,
                    "docstring": method_docstring,
                    "body": method_body,
                    "line_start": method_line_start,
                    "line_end": method_line_end
                })
            
            file_analysis["classes"].append({
                "name": class_name,
                "bases": [base_class] if base_class else [],
                "docstring": docstring,
                "methods": methods,
                "body": class_body,
                "line_start": line_start,
                "line_end": line_end
            })
    
    def _analyze_typescript(self, content: str, file_analysis: Dict[str, Any]):
        """
        Analyze TypeScript code.
        
        Args:
            content (str): File content
            file_analysis (Dict[str, Any]): File analysis to update
        """
        # TypeScript analysis is similar to JavaScript but with type annotations
        # For simplicity, we'll reuse the JavaScript analyzer
        self._analyze_javascript(content, file_analysis)
        
        # Extract interfaces
        interface_regex = r'interface\s+([a-zA-Z0-9_$]+)(?:\s+extends\s+([a-zA-Z0-9_$.]+))?\s*{'
        interfaces = []
        
        for match in re.finditer(interface_regex, content):
            interface_name = match.group(1)
            extends = match.group(2)
            
            # Get interface body (simplified)
            line_start = content[:match.start()].count('\n') + 1
            
            # Find closing brace (naive implementation)
            open_brace_pos = content.find('{', match.end())
            brace_count = 1
            close_brace_pos = open_brace_pos + 1
            while brace_count > 0 and close_brace_pos < len(content):
                if content[close_brace_pos] == '{':
                    brace_count += 1
                elif content[close_brace_pos] == '}':
                    brace_count -= 1
                close_brace_pos += 1
            
            if close_brace_pos >= len(content):
                close_brace_pos = len(content) - 1
            
            interface_body = content[match.start():close_brace_pos]
            line_end = content[:close_brace_pos].count('\n') + 1
            
            # Extract docstring (JSDoc)
            docstring = ""
            jsdoc_match = re.search(r'/\*\*([\s\S]*?)\*/', content[:match.start()])
            if jsdoc_match and jsdoc_match.end() + 5 >= match.start():
                docstring = jsdoc_match.group(1).strip()
            
            interfaces.append({
                "name": interface_name,
                "extends": [extends] if extends else [],
                "docstring": docstring,
                "body": interface_body,
                "line_start": line_start,
                "line_end": line_end
            })
        
        file_analysis["interfaces"] = interfaces
    
    def _analyze_java(self, content: str, file_analysis: Dict[str, Any]):
        """
        Analyze Java code.
        
        Args:
            content (str): File content
            file_analysis (Dict[str, Any]): File analysis to update
        """
        # Extract imports
        import_regex = r'import\s+([a-zA-Z0-9_.]+(?:\.[*])?)(?:\s+as\s+([a-zA-Z0-9_]+))?;'
        imports = []
        
        for match in re.finditer(import_regex, content):
            imports.append({"module": match.group(1), "alias": match.group(2)})
        
        file_analysis["imports"] = imports
        
        # Extract package
        package_match = re.search(r'package\s+([a-zA-Z0-9_.]+);', content)
        if package_match:
            file_analysis["package"] = package_match.group(1)
        
        # Extract classes
        class_regex = r'(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+([a-zA-Z0-9_$]+)(?:\s+extends\s+([a-zA-Z0-9_$.]+))?(?:\s+implements\s+([a-zA-Z0-9_$.,\s]+))?'
        
        for match in re.finditer(class_regex, content):
            class_name = match.group(1)
            extends = match.group(2)
            implements = match.group(3)
            
            # Parse implemented interfaces
            implemented_interfaces = []
            if implements:
                implemented_interfaces = [i.strip() for i in implements.split(',')]
            
            # Get class body (simplified)
            line_start = content[:match.start()].count('\n') + 1
            
            # Find opening brace
            open_brace_pos = content.find('{', match.end())
            if open_brace_pos == -1:
                continue
            
            # Find closing brace (naive implementation)
            brace_count = 1
            close_brace_pos = open_brace_pos + 1
            while brace_count > 0 and close_brace_pos < len(content):
                if content[close_brace_pos] == '{':
                    brace_count += 1
                elif content[close_brace_pos] == '}':
                    brace_count -= 1
                close_brace_pos += 1
            
            if close_brace_pos >= len(content):
                close_brace_pos = len(content) - 1
            
            class_body = content[match.start():close_brace_pos]
            line_end = content[:close_brace_pos].count('\n') + 1
            
            # Extract Javadoc
            docstring = ""
            javadoc_match = re.search(r'/\*\*([\s\S]*?)\*/', content[:match.start()])
            if javadoc_match and javadoc_match.end() + 5 >= match.start():
                docstring = javadoc_match.group(1).strip()
            
            # Extract methods
            methods = []
            method_regex = r'(?:public|private|protected)?\s*(?:static|final|abstract)?\s*(?:<[^>]+>\s*)?(?:[a-zA-Z0-9_$.<>[\],\s]+)\s+([a-zA-Z0-9_$]+)\s*\(([^)]*)\)'
            class_content = content[open_brace_pos:close_brace_pos]
            
            for method_match in re.finditer(method_regex, class_content):
                method_name = method_match.group(1)
                
                # Skip if this is a constructor (same name as class)
                if method_name == class_name:
                    continue
                
                # Get method parameters
                params = []
                if method_match.group(2):
                    # Java parameters include type, so we need to extract just the parameter name
                    param_str = method_match.group(2).strip()
                    if param_str:
                        for param in param_str.split(','):
                            param = param.strip()
                            if param:
                                # Extract parameter name (last word before any default value)
                                param_parts = param.split()
                                if len(param_parts) >= 2:
                                    param_name = param_parts[-1].split('=')[0].strip()
                                    params.append(param_name)
                
                # Get method body (simplified)
                method_start = open_brace_pos + method_match.start()
                method_line_start = content[:method_start].count('\n') + 1
                
                # Find opening brace
                method_open_brace_pos = content.find('{', method_start + method_match.end())
                if method_open_brace_pos == -1:
                    continue
                
                # Find closing brace (naive implementation)
                method_brace_count = 1
                method_close_brace_pos = method_open_brace_pos + 1
                while method_brace_count > 0 and method_close_brace_pos < close_brace_pos:
                    if content[method_close_brace_pos] == '{':
                        method_brace_count += 1
                    elif content[method_close_brace_pos] == '}':
                        method_brace_count -= 1
                    method_close_brace_pos += 1
                
                if method_close_brace_pos >= close_brace_pos:
                    method_close_brace_pos = close_brace_pos - 1
                
                method_body = content[method_start:method_close_brace_pos]
                method_line_end = content[:method_close_brace_pos].count('\n') + 1
                
                # Extract method Javadoc
                method_docstring = ""
                method_javadoc_match = re.search(r'/\*\*([\s\S]*?)\*/', class_content[:method_match.start()])
                if method_javadoc_match and method_javadoc_match.end() + 5 >= method_match.start():
                    method_docstring = method_javadoc_match.group(1).strip()
                
                methods.append({
                    "name": method_name,
                    "params": params,
                    "docstring": method_docstring,
                    "body": method_body,
                    "line_start": method_line_start,
                    "line_end": method_line_end
                })
            
            file_analysis["classes"].append({
                "name": class_name,
                "bases": [extends] if extends else [],
                "implements": implemented_interfaces,
                "docstring": docstring,
                "methods": methods,
                "body": class_body,
                "line_start": line_start,
                "line_end": line_end
            })
    
    def _analyze_cpp(self, content: str, file_analysis: Dict[str, Any]):
        """
        Analyze C++ code.
        
        Args:
            content (str): File content
            file_analysis (Dict[str, Any]): File analysis to update
        """
        # Extract includes
        include_regex = r'#include\s+[<"]([^>"]+)[>"]'
        includes = []
        
        for match in re.finditer(include_regex, content):
            includes.append({"module": match.group(1), "alias": None})
        
        file_analysis["imports"] = includes
        
        # Extract namespaces
        namespace_regex = r'namespace\s+([a-zA-Z0-9_]+)'
        namespaces = []
        
        for match in re.finditer(namespace_regex, content):
            namespaces.append(match.group(1))
        
        file_analysis["namespaces"] = namespaces
        
        # Extract classes
        class_regex = r'(?:class|struct)\s+([a-zA-Z0-9_]+)(?:\s*:\s*(?:public|protected|private)?\s*([a-zA-Z0-9_:]+))?'
        
        for match in re.finditer(class_regex, content):
            class_name = match.group(1)
            inherits = match.group(2)
            
            # Get class body (simplified)
            line_start = content[:match.start()].count('\n') + 1
            
            # Find opening brace
            open_brace_pos = content.find('{', match.end())
            if open_brace_pos == -1:
                continue
            
            # Find closing brace (naive implementation)
            brace_count = 1
            close_brace_pos = open_brace_pos + 1
            while brace_count > 0 and close_brace_pos < len(content):
                if content[close_brace_pos] == '{':
                    brace_count += 1
                elif content[close_brace_pos] == '}':
                    brace_count -= 1
                close_brace_pos += 1
            
            if close_brace_pos >= len(content):
                close_brace_pos = len(content) - 1
            
            class_body = content[match.start():close_brace_pos]
            line_end = content[:close_brace_pos].count('\n') + 1
            
            # Extract methods (simplified)
            methods = []
            method_regex = r'(?:public|private|protected)?:?\s*(?:virtual|static|inline)?\s*(?:[a-zA-Z0-9_:*&<>\[\],\s]+)\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\)'
            class_content = content[open_brace_pos:close_brace_pos]
            
            for method_match in re.finditer(method_regex, class_content):
                method_name = method_match.group(1)
                
                # Skip if this is a constructor (same name as class)
                if method_name == class_name:
                    continue
                
                # Get method parameters
                params = []
                if method_match.group(2):
                    # C++ parameters include type, so we need to extract just the parameter name
                    param_str = method_match.group(2).strip()
                    if param_str:
                        for param in param_str.split(','):
                            param = param.strip()
                            if param:
                                # Extract parameter name (last word before any default value)
                                param_parts = param.split()
                                if len(param_parts) >= 2:
                                    param_name = param_parts[-1].split('=')[0].strip()
                                    # Remove any pointer or reference symbols
                                    param_name = param_name.lstrip('*&')
                                    params.append(param_name)
                
                methods.append({
                    "name": method_name,
                    "params": params,
                    "body": "...",  # Simplified
                    "line_start": 0,  # Simplified
                    "line_end": 0  # Simplified
                })
            
            file_analysis["classes"].append({
                "name": class_name,
                "bases": [inherits] if inherits else [],
                "methods": methods,
                "body": class_body,
                "line_start": line_start,
                "line_end": line_end
            })
        
        # Extract functions
        function_regex = r'(?:static|inline)?\s*(?:[a-zA-Z0-9_:*&<>\[\],\s]+)\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\)\s*(?:const)?\s*(?:noexcept)?\s*(?:override)?\s*(?:final)?\s*(?:=\s*(?:default|delete|0))?\s*(?:{\s*|\n\s*{)'
        
        for match in re.finditer(function_regex, content):
            function_name = match.group(1)
            
            # Skip if inside a class
            prev_content = content[:match.start()]
            open_braces = prev_content.count('{')
            close_braces = prev_content.count('}')
            if open_braces > close_braces:
                continue
            
            # Get function parameters
            params = []
            if match.group(2):
                # C++ parameters include type, so we need to extract just the parameter name
                param_str = match.group(2).strip()
                if param_str:
                    for param in param_str.split(','):
                        param = param.strip()
                        if param:
                            # Extract parameter name (last word before any default value)
                            param_parts = param.split()
                            if len(param_parts) >= 2:
                                param_name = param_parts[-1].split('=')[0].strip()
                                # Remove any pointer or reference symbols
                                param_name = param_name.lstrip('*&')
                                params.append(param_name)
            
            # Get function body (simplified)
            line_start = content[:match.start()].count('\n') + 1
            
            # Find opening brace
            open_brace_pos = content.find('{', match.end())
            if open_brace_pos == -1:
                continue
            
            # Find closing brace (naive implementation)
            brace_count = 1
            close_brace_pos = open_brace_pos + 1
            while brace_count > 0 and close_brace_pos < len(content):
                if content[close_brace_pos] == '{':
                    brace_count += 1
                elif content[close_brace_pos] == '}':
                    brace_count -= 1
                close_brace_pos += 1
            
            if close_brace_pos >= len(content):
                close_brace_pos = len(content) - 1
            
            function_body = content[match.start():close_brace_pos]
            line_end = content[:close_brace_pos].count('\n') + 1
            
            file_analysis["functions"].append({
                "name": function_name,
                "params": params,
                "body": function_body,
                "line_start": line_start,
                "line_end": line_end
            })
    
    def _analyze_c(self, content: str, file_analysis: Dict[str, Any]):
        """
        Analyze C code.
        
        Args:
            content (str): File content
            file_analysis (Dict[str, Any]): File analysis to update
        """
        # C analysis is similar to C++ but without classes
        # Extract includes
        include_regex = r'#include\s+[<"]([^>"]+)[>"]'
        includes = []
        
        for match in re.finditer(include_regex, content):
            includes.append({"module": match.group(1), "alias": None})
        
        file_analysis["imports"] = includes
        
        # Extract functions
        function_regex = r'(?:static|inline)?\s*(?:[a-zA-Z0-9_:*&<>\[\],\s]+)\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\)\s*(?:{\s*|\n\s*{)'
        
        for match in re.finditer(function_regex, content):
            function_name = match.group(1)
            
            # Get function parameters
            params = []
            if match.group(2):
                # C parameters include type, so we need to extract just the parameter name
                param_str = match.group(2).strip()
                if param_str and param_str != "void":
                    for param in param_str.split(','):
                        param = param.strip()
                        if param:
                            # Extract parameter name (last word before any default value)
                            param_parts = param.split()
                            if len(param_parts) >= 2:
                                param_name = param_parts[-1].split('=')[0].strip()
                                # Remove any pointer or reference symbols
                                param_name = param_name.lstrip('*')
                                params.append(param_name)
            
            # Get function body (simplified)
            line_start = content[:match.start()].count('\n') + 1
            
            # Find opening brace
            open_brace_pos = content.find('{', match.end())
            if open_brace_pos == -1:
                continue
            
            # Find closing brace (naive implementation)
            brace_count = 1
            close_brace_pos = open_brace_pos + 1
            while brace_count > 0 and close_brace_pos < len(content):
                if content[close_brace_pos] == '{':
                    brace_count += 1
                elif content[close_brace_pos] == '}':
                    brace_count -= 1
                close_brace_pos += 1
            
            if close_brace_pos >= len(content):
                close_brace_pos = len(content) - 1
            
            function_body = content[match.start():close_brace_pos]
            line_end = content[:close_brace_pos].count('\n') + 1
            
            file_analysis["functions"].append({
                "name": function_name,
                "params": params,
                "body": function_body,
                "line_start": line_start,
                "line_end": line_end
            })
    
    def _analyze_generic(self, content: str, file_analysis: Dict[str, Any]):
        """
        Generic code analysis for unsupported languages.
        
        Args:
            content (str): File content
            file_analysis (Dict[str, Any]): File analysis to update
        """
        # Simple function detection based on common patterns
        function_regex = r'(?:function|def|func|fn|method|sub)\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\)'
        
        for match in re.finditer(function_regex, content):
            function_name = match.group(1)
            params_str = match.group(2)
            
            # Get function parameters
            params = []
            if params_str:
                params = [p.strip() for p in params_str.split(',') if p.strip()]
            
            # Get function body (simplified)
            line_start = content[:match.start()].count('\n') + 1
            line_end = line_start + 10  # Simplified
            
            file_analysis["functions"].append({
                "name": function_name,
                "params": params,
                "body": "...",  # Simplified
                "line_start": line_start,
                "line_end": line_end
            })
        
        # Simple class detection based on common patterns
        class_regex = r'(?:class|struct|interface)\s+([a-zA-Z0-9_]+)'
        
        for match in re.finditer(class_regex, content):
            class_name = match.group(1)
            
            # Get class body (simplified)
            line_start = content[:match.start()].count('\n') + 1
            line_end = line_start + 20  # Simplified
            
            file_analysis["classes"].append({
                "name": class_name,
                "bases": [],
                "methods": [],
                "body": "...",  # Simplified
                "line_start": line_start,
                "line_end": line_end
            })
    
    def _process_python_imports(self, file_path: str, dependency_graph: nx.DiGraph, import_dependencies: List[Dict[str, Any]]):
        """
        Process Python imports.
        
        Args:
            file_path (str): File path
            dependency_graph (nx.DiGraph): Dependency graph
            import_dependencies (List[Dict[str, Any]]): Import dependencies list to update
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse Python code
            tree = ast.parse(content)
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        import_name = name.name
                        alias = name.asname
                        
                        # Add import dependency
                        import_dependencies.append({
                            "source_file": file_path,
                            "module": import_name,
                            "alias": alias
                        })
                        
                        # Add to dependency graph
                        source_node = f"file:{file_path}"
                        target_node = f"module:{import_name}"
                        dependency_graph.add_node(target_node, type="module", name=import_name)
                        dependency_graph.add_edge(source_node, target_node, type="imports")
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for name in node.names:
                        import_name = f"{module}.{name.name}" if module else name.name
                        alias = name.asname
                        
                        # Add import dependency
                        import_dependencies.append({
                            "source_file": file_path,
                            "module": import_name,
                            "alias": alias
                        })
                        
                        # Add to dependency graph
                        source_node = f"file:{file_path}"
                        target_node = f"module:{import_name}"
                        dependency_graph.add_node(target_node, type="module", name=import_name)
                        dependency_graph.add_edge(source_node, target_node, type="imports")
        except Exception as e:
            logger.error(f"Error processing Python imports in {file_path}: {e}")
    
    def _process_js_imports(self, file_path: str, dependency_graph: nx.DiGraph, import_dependencies: List[Dict[str, Any]]):
        """
        Process JavaScript/TypeScript imports.
        
        Args:
            file_path (str): File path
            dependency_graph (nx.DiGraph): Dependency graph
            import_dependencies (List[Dict[str, Any]]): Import dependencies list to update
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract imports
            import_regex = r'(?:import|require)\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)|import\s+(?:\*\s+as\s+([a-zA-Z0-9_$]+)|{\s*([^}]+)\s*}|([a-zA-Z0-9_$]+))\s+from\s+[\'"]([^\'"]+)[\'"]'
            
            for match in re.finditer(import_regex, content):
                if match.group(1):  # require or dynamic import
                    module = match.group(1)
                    
                    # Add import dependency
                    import_dependencies.append({
                        "source_file": file_path,
                        "module": module,
                        "alias": None
                    })
                    
                    # Add to dependency graph
                    source_node = f"file:{file_path}"
                    target_node = f"module:{module}"
                    dependency_graph.add_node(target_node, type="module", name=module)
                    dependency_graph.add_edge(source_node, target_node, type="imports")
                
                elif match.group(5):  # ES6 import
                    module = match.group(5)
                    alias = None
                    
                    if match.group(2):  # import * as name
                        alias = match.group(2)
                    elif match.group(3):  # import { name1, name2 }
                        alias = match.group(3)
                    elif match.group(4):  # import name
                        alias = match.group(4)
                    
                    # Add import dependency
                    import_dependencies.append({
                        "source_file": file_path,
                        "module": module,
                        "alias": alias
                    })
                    
                    # Add to dependency graph
                    source_node = f"file:{file_path}"
                    target_node = f"module:{module}"
                    dependency_graph.add_node(target_node, type="module", name=module)
                    dependency_graph.add_edge(source_node, target_node, type="imports")
        except Exception as e:
            logger.error(f"Error processing JS imports in {file_path}: {e}")
    
    def _identify_function_dependencies(self, analysis_results: Dict[str, Any], dependency_graph: nx.DiGraph) -> List[Dict[str, Any]]:
        """
        Identify function dependencies.
        
        Args:
            analysis_results (Dict[str, Any]): Analysis results
            dependency_graph (nx.DiGraph): Dependency graph
            
        Returns:
            List[Dict[str, Any]]: Function dependencies
        """
        function_dependencies = []
        
        # Create a map of function names to their file paths
        function_map = {}
        for func in analysis_results.get("functions", []):
            function_map[func["name"]] = func["file_path"]
        
        # Check for function calls
        for func in analysis_results.get("functions", []):
            func_name = func["name"]
            file_path = func["file_path"]
            body = func.get("body", "")
            
            # Look for function calls in the body
            for called_func_name, called_func_path in function_map.items():
                if called_func_name == func_name:
                    continue  # Skip self-references
                
                # Simple pattern matching (can be improved)
                pattern = r'\b' + re.escape(called_func_name) + r'\s*\('
                if re.search(pattern, body):
                    # Add function dependency
                    function_dependencies.append({
                        "source_function": func_name,
                        "source_file": file_path,
                        "target_function": called_func_name,
                        "target_file": called_func_path
                    })
                    
                    # Add to dependency graph
                    source_node = f"function:{file_path}:{func_name}"
                    target_node = f"function:{called_func_path}:{called_func_name}"
                    dependency_graph.add_edge(source_node, target_node, type="calls")
        
        return function_dependencies
    
    def _identify_class_dependencies(self, analysis_results: Dict[str, Any], dependency_graph: nx.DiGraph) -> List[Dict[str, Any]]:
        """
        Identify class dependencies.
        
        Args:
            analysis_results (Dict[str, Any]): Analysis results
            dependency_graph (nx.DiGraph): Dependency graph
            
        Returns:
            List[Dict[str, Any]]: Class dependencies
        """
        class_dependencies = []
        
        # Create a map of class names to their file paths
        class_map = {}
        for cls in analysis_results.get("classes", []):
            class_map[cls["name"]] = cls["file_path"]
        
        # Check for inheritance
        for cls in analysis_results.get("classes", []):
            class_name = cls["name"]
            file_path = cls["file_path"]
            
            for base_class in cls.get("bases", []):
                # Handle qualified names (e.g., module.Class)
                base_name = base_class.split('.')[-1]
                
                if base_name in class_map:
                    base_path = class_map[base_name]
                    
                    # Add class dependency
                    class_dependencies.append({
                        "source_class": class_name,
                        "source_file": file_path,
                        "target_class": base_name,
                        "target_file": base_path,
                        "type": "inherits"
                    })
                    
                    # Add to dependency graph
                    source_node = f"class:{file_path}:{class_name}"
                    target_node = f"class:{base_path}:{base_name}"
                    dependency_graph.add_edge(source_node, target_node, type="inherits")
        
        return class_dependencies
    
    def _generate_dependency_visualization(self, dependency_graph: nx.DiGraph, output_dir: str):
        """
        Generate dependency visualization.
        
        Args:
            dependency_graph (nx.DiGraph): Dependency graph
            output_dir (str): Output directory
        """
        try:
            # Create visualization directory
            vis_dir = os.path.join(output_dir, "visualization")
            os.makedirs(vis_dir, exist_ok=True)
            
            # Generate JSON for D3.js visualization
            nodes = []
            links = []
            
            for node, attrs in dependency_graph.nodes(data=True):
                node_type = attrs.get("type", "unknown")
                node_name = attrs.get("name", node)
                
                nodes.append({
                    "id": node,
                    "name": node_name,
                    "type": node_type
                })
            
            for source, target, attrs in dependency_graph.edges(data=True):
                edge_type = attrs.get("type", "unknown")
                
                links.append({
                    "source": source,
                    "target": target,
                    "type": edge_type
                })
            
            graph_data = {
                "nodes": nodes,
                "links": links
            }
            
            # Save graph data as JSON
            with open(os.path.join(vis_dir, "dependency_graph.json"), 'w') as f:
                json.dump(graph_data, f, indent=2)
            
            logger.info(f"Dependency visualization data saved to {vis_dir}")
        except Exception as e:
            logger.error(f"Error generating dependency visualization: {e}")
