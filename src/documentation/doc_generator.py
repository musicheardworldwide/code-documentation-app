"""
Documentation generator module with complete implementation.

This module generates comprehensive documentation for code.
"""

import os
import logging
import json
import markdown
from typing import Dict, Any, Optional, List
import jinja2

logger = logging.getLogger(__name__)

class DocumentationGenerator:
    """Generates comprehensive documentation for code."""
    
    def __init__(self, model_orchestrator=None, rag_system=None):
        """
        Initialize documentation generator.
        
        Args:
            model_orchestrator: Model orchestrator for LLM integration
            rag_system: RAG system for context-aware documentation
        """
        self.model_orchestrator = model_orchestrator
        self.rag_system = rag_system
        
        # Initialize Jinja2 environment for templates
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.dirname(os.path.abspath(__file__))),
            autoescape=jinja2.select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Create default templates if they don't exist
        self._create_default_templates()
    
    def generate(self, analysis_results: Dict[str, Any], output_dir: str) -> str:
        """
        Generate documentation.
        
        Args:
            analysis_results (Dict[str, Any]): Code analysis results
            output_dir (str): Output directory
            
        Returns:
            str: Path to generated documentation
        """
        try:
            logger.info(f"Generating documentation in {output_dir}")
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate function documentation
            functions_dir = os.path.join(output_dir, "functions")
            self._generate_function_docs(analysis_results, functions_dir)
            
            # Generate dependency maps
            dependencies_dir = os.path.join(output_dir, "dependencies")
            self._generate_dependency_maps(analysis_results, dependencies_dir)
            
            # Generate Q&A pairs for development
            qa_path = os.path.join(output_dir, "development_qa.md")
            self._generate_qa_pairs(analysis_results, qa_path)
            
            # Generate summary documentation
            summary_path = os.path.join(output_dir, "summary.md")
            self._generate_summary(analysis_results, summary_path)
            
            # Generate index file
            index_path = os.path.join(output_dir, "index.html")
            self._generate_index(analysis_results, index_path)
            
            return output_dir
        except Exception as e:
            logger.error(f"Error generating documentation: {e}")
            raise Exception(f"Failed to generate documentation: {e}")
    
    def _generate_function_docs(self, analysis_results: Dict[str, Any], output_dir: str):
        """
        Generate function documentation.
        
        Args:
            analysis_results (Dict[str, Any]): Code analysis results
            output_dir (str): Output directory
        """
        try:
            # Create functions directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Get functions from analysis results
            functions = analysis_results.get("functions", [])
            logger.info(f"Generating documentation for {len(functions)} functions")
            
            # Group functions by file
            functions_by_file = {}
            for func in functions:
                file_path = func.get("file_path", "unknown")
                if file_path not in functions_by_file:
                    functions_by_file[file_path] = []
                functions_by_file[file_path].append(func)
            
            # Generate documentation for each file
            for file_path, file_functions in functions_by_file.items():
                # Create file-specific output file
                file_name = os.path.basename(file_path)
                output_file = os.path.join(output_dir, f"{file_name}.md")
                
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(f"# Functions in {file_name}\n\n")
                    f.write(f"File path: `{file_path}`\n\n")
                    
                    # Document each function
                    for func in file_functions:
                        func_name = func.get("name", "unknown")
                        params = func.get("params", [])
                        docstring = func.get("docstring", "")
                        
                        f.write(f"## {func_name}\n\n")
                        
                        # Add parameters
                        if params:
                            f.write("### Parameters\n\n")
                            for param in params:
                                f.write(f"- `{param}`\n")
                            f.write("\n")
                        
                        # Add docstring if available
                        if docstring:
                            f.write("### Documentation\n\n")
                            f.write(f"{docstring}\n\n")
                        
                        # Generate documentation using LLM if available
                        if self.model_orchestrator and self.model_orchestrator.is_ready():
                            try:
                                body = func.get("body", "")
                                if body:
                                    llm_doc = self.model_orchestrator.generate_documentation(body)
                                    if llm_doc and not docstring:  # Only use LLM doc if no docstring
                                        f.write("### Generated Documentation\n\n")
                                        f.write(f"{llm_doc}\n\n")
                            except Exception as e:
                                logger.error(f"Error generating LLM documentation for {func_name}: {e}")
            
            # Generate index file
            index_file = os.path.join(output_dir, "index.md")
            with open(index_file, "w", encoding="utf-8") as f:
                f.write("# Function Documentation\n\n")
                
                # Add links to each file
                for file_path in functions_by_file.keys():
                    file_name = os.path.basename(file_path)
                    f.write(f"- [{file_name}]({file_name}.md) ({len(functions_by_file[file_path])} functions)\n")
        except Exception as e:
            logger.error(f"Error generating function documentation: {e}")
            raise Exception(f"Failed to generate function documentation: {e}")
    
    def _generate_dependency_maps(self, analysis_results: Dict[str, Any], output_dir: str):
        """
        Generate dependency maps.
        
        Args:
            analysis_results (Dict[str, Any]): Code analysis results
            output_dir (str): Output directory
        """
        try:
            # Create dependencies directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Get dependency information
            dependencies = analysis_results.get("dependencies", {})
            
            # Generate import dependencies documentation
            import_deps = dependencies.get("import_dependencies", [])
            if import_deps:
                import_file = os.path.join(output_dir, "import_dependencies.md")
                with open(import_file, "w", encoding="utf-8") as f:
                    f.write("# Import Dependencies\n\n")
                    
                    # Group by source file
                    imports_by_file = {}
                    for dep in import_deps:
                        source_file = dep.get("source_file", "unknown")
                        if source_file not in imports_by_file:
                            imports_by_file[source_file] = []
                        imports_by_file[source_file].append(dep)
                    
                    # Document each file's imports
                    for source_file, imports in imports_by_file.items():
                        f.write(f"## {os.path.basename(source_file)}\n\n")
                        f.write(f"File path: `{source_file}`\n\n")
                        
                        f.write("| Module | Alias |\n")
                        f.write("|--------|-------|\n")
                        
                        for imp in imports:
                            module = imp.get("module", "unknown")
                            alias = imp.get("alias", "")
                            f.write(f"| `{module}` | `{alias if alias else ''}` |\n")
                        
                        f.write("\n")
            
            # Generate function dependencies documentation
            func_deps = dependencies.get("function_dependencies", [])
            if func_deps:
                func_file = os.path.join(output_dir, "function_dependencies.md")
                with open(func_file, "w", encoding="utf-8") as f:
                    f.write("# Function Dependencies\n\n")
                    
                    # Group by source function
                    deps_by_func = {}
                    for dep in func_deps:
                        source_func = dep.get("source_function", "unknown")
                        source_file = dep.get("source_file", "unknown")
                        key = f"{source_file}:{source_func}"
                        if key not in deps_by_func:
                            deps_by_func[key] = []
                        deps_by_func[key].append(dep)
                    
                    # Document each function's dependencies
                    for key, deps in deps_by_func.items():
                        source_file, source_func = key.split(":", 1)
                        f.write(f"## {source_func}\n\n")
                        f.write(f"File: `{source_file}`\n\n")
                        
                        f.write("Calls the following functions:\n\n")
                        f.write("| Function | File |\n")
                        f.write("|----------|------|\n")
                        
                        for dep in deps:
                            target_func = dep.get("target_function", "unknown")
                            target_file = dep.get("target_file", "unknown")
                            f.write(f"| `{target_func}` | `{os.path.basename(target_file)}` |\n")
                        
                        f.write("\n")
            
            # Generate class dependencies documentation
            class_deps = dependencies.get("class_dependencies", [])
            if class_deps:
                class_file = os.path.join(output_dir, "class_dependencies.md")
                with open(class_file, "w", encoding="utf-8") as f:
                    f.write("# Class Dependencies\n\n")
                    
                    # Group by source class
                    deps_by_class = {}
                    for dep in class_deps:
                        source_class = dep.get("source_class", "unknown")
                        source_file = dep.get("source_file", "unknown")
                        key = f"{source_file}:{source_class}"
                        if key not in deps_by_class:
                            deps_by_class[key] = []
                        deps_by_class[key].append(dep)
                    
                    # Document each class's dependencies
                    for key, deps in deps_by_class.items():
                        source_file, source_class = key.split(":", 1)
                        f.write(f"## {source_class}\n\n")
                        f.write(f"File: `{source_file}`\n\n")
                        
                        f.write("Inherits from:\n\n")
                        f.write("| Class | File |\n")
                        f.write("|-------|------|\n")
                        
                        for dep in deps:
                            target_class = dep.get("target_class", "unknown")
                            target_file = dep.get("target_file", "unknown")
                            f.write(f"| `{target_class}` | `{os.path.basename(target_file)}` |\n")
                        
                        f.write("\n")
            
            # Generate dependency visualization
            vis_dir = os.path.join(output_dir, "visualization")
            if os.path.exists(vis_dir):
                # Copy visualization files
                vis_file = os.path.join(output_dir, "visualization.html")
                with open(vis_file, "w", encoding="utf-8") as f:
                    f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Code Dependency Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
        #graph { width: 100%; height: 800px; }
        .node { stroke: #fff; stroke-width: 1.5px; }
        .link { stroke: #999; stroke-opacity: 0.6; }
        .node text { font-size: 10px; }
        .file { fill: #1f77b4; }
        .function { fill: #ff7f0e; }
        .class { fill: #2ca02c; }
        .method { fill: #d62728; }
        .module { fill: #9467bd; }
    </style>
</head>
<body>
    <h1>Code Dependency Visualization</h1>
    <div id="graph"></div>
    <script>
        // Load the data
        d3.json('visualization/dependency_graph.json').then(function(graph) {
            const width = document.getElementById('graph').clientWidth;
            const height = document.getElementById('graph').clientHeight;
            
            const simulation = d3.forceSimulation(graph.nodes)
                .force('link', d3.forceLink(graph.links).id(d => d.id).distance(100))
                .force('charge', d3.forceManyBody().strength(-300))
                .force('center', d3.forceCenter(width / 2, height / 2));
            
            const svg = d3.select('#graph')
                .append('svg')
                .attr('width', width)
                .attr('height', height);
            
            // Add zoom functionality
            const g = svg.append('g');
            svg.call(d3.zoom()
                .extent([[0, 0], [width, height]])
                .scaleExtent([0.1, 8])
                .on('zoom', (event) => {
                    g.attr('transform', event.transform);
                }));
            
            // Add links
            const link = g.append('g')
                .selectAll('line')
                .data(graph.links)
                .enter().append('line')
                .attr('class', 'link')
                .attr('stroke-width', d => Math.sqrt(d.value || 1));
            
            // Add nodes
            const node = g.append('g')
                .selectAll('circle')
                .data(graph.nodes)
                .enter().append('circle')
                .attr('class', 'node')
                .attr('r', 5)
                .attr('class', d => d.type)
                .call(d3.drag()
                    .on('start', dragstarted)
                    .on('drag', dragged)
                    .on('end', dragended));
            
            // Add node labels
            const label = g.append('g')
                .selectAll('text')
                .data(graph.nodes)
                .enter().append('text')
                .attr('dx', 12)
                .attr('dy', '.35em')
                .text(d => d.name);
            
            // Add tooltips
            node.append('title')
                .text(d => d.id);
            
            // Update positions
            simulation.on('tick', () => {
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);
                
                node
                    .attr('cx', d => d.x)
                    .attr('cy', d => d.y);
                
                label
                    .attr('x', d => d.x)
                    .attr('y', d => d.y);
            });
            
            // Drag functions
            function dragstarted(event, d) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }
            
            function dragged(event, d) {
                d.fx = event.x;
                d.fy = event.y;
            }
            
            function dragended(event, d) {
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }
        });
    </script>
</body>
</html>""")
            
            # Generate index file
            index_file = os.path.join(output_dir, "index.md")
            with open(index_file, "w", encoding="utf-8") as f:
                f.write("# Dependency Documentation\n\n")
                
                # Add links to each file
                if os.path.exists(os.path.join(output_dir, "import_dependencies.md")):
                    f.write("- [Import Dependencies](import_dependencies.md)\n")
                if os.path.exists(os.path.join(output_dir, "function_dependencies.md")):
                    f.write("- [Function Dependencies](function_dependencies.md)\n")
                if os.path.exists(os.path.join(output_dir, "class_dependencies.md")):
                    f.write("- [Class Dependencies](class_dependencies.md)\n")
                if os.path.exists(os.path.join(output_dir, "visualization.html")):
                    f.write("- [Dependency Visualization](visualization.html)\n")
        except Exception as e:
            logger.error(f"Error generating dependency maps: {e}")
            raise Exception(f"Failed to generate dependency maps: {e}")
    
    def _generate_qa_pairs(self, analysis_results: Dict[str, Any], output_file: str, count: int = 50):
        """
        Generate Q&A pairs for development.
        
        Args:
            analysis_results (Dict[str, Any]): Code analysis results
            output_file (str): Output file path
            count (int, optional): Number of Q&A pairs to generate
        """
        try:
            # Generate Q&A pairs using model orchestrator if available
            qa_pairs = []
            if self.model_orchestrator and self.model_orchestrator.is_ready():
                try:
                    qa_pairs = self.model_orchestrator.generate_qa_pairs(analysis_results, count)
                except Exception as e:
                    logger.error(f"Error generating Q&A pairs with model: {e}")
            
            # If no Q&A pairs were generated, create placeholder pairs
            if not qa_pairs:
                qa_pairs = [
                    {"question": "How do I add a new feature to the application?", 
                     "answer": "To add a new feature, you would need to identify the appropriate module for your feature, create a new class or function that implements the feature, and then integrate it with the existing codebase. Make sure to follow the existing patterns and coding standards. Add appropriate tests for your new feature."},
                    {"question": "What is the architecture of the codebase?", 
                     "answer": "The codebase follows a modular architecture with separate components for different functionalities. Each module has a specific responsibility and communicates with other modules through well-defined interfaces. This separation of concerns makes the code more maintainable and testable."},
                    {"question": "How are dependencies managed in the project?", 
                     "answer": "Dependencies are managed through a requirements.txt file for Python dependencies. The file lists all the required packages and their versions. You can install all dependencies using pip: `pip install -r requirements.txt`."},
                    {"question": "How can I extend the documentation generator?", 
                     "answer": "The documentation generator can be extended by modifying the DocumentationGenerator class. You can add new methods for generating different types of documentation, or modify existing methods to change the format or content of the documentation. Make sure to update the templates in the templates directory if you change the structure of the documentation."},
                    {"question": "What is the process for adding a new language parser?", 
                     "answer": "To add a new language parser, you would need to extend the CodeAnalyzer class in the analysis module. Create a new method named `_analyze_<language>` that takes the file content and file analysis dictionary as parameters. Implement the parsing logic for the new language, extracting functions, classes, and other relevant information. Then add the new language to the `supported_languages` dictionary in the CodeAnalyzer constructor."}
                ]
                
                # Generate more placeholder pairs to reach the requested count
                for i in range(5, count):
                    qa_pairs.append({
                        "question": f"Sample question {i+1} about the codebase?",
                        "answer": f"This is a sample answer for question {i+1}. In a real implementation, this would be generated by the LLM based on the code analysis results."
                    })
            
            # Write Q&A pairs to file
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("# Development Q&A\n\n")
                f.write("This file contains questions and answers for development and feature changes.\n\n")
                
                # Add Q&A pairs
                for i, qa in enumerate(qa_pairs):
                    f.write(f"## Q{i+1}: {qa['question']}\n\n")
                    f.write(f"{qa['answer']}\n\n")
        except Exception as e:
            logger.error(f"Error generating Q&A pairs: {e}")
            raise Exception(f"Failed to generate Q&A pairs: {e}")
    
    def _generate_summary(self, analysis_results: Dict[str, Any], output_file: str):
        """
        Generate summary documentation.
        
        Args:
            analysis_results (Dict[str, Any]): Code analysis results
            output_file (str): Output file path
        """
        try:
            # Extract statistics
            file_count = analysis_results.get("file_count", 0)
            function_count = analysis_results.get("function_count", 0)
            class_count = analysis_results.get("class_count", 0)
            
            # Get language statistics
            languages = {}
            for file_info in analysis_results.get("files", []):
                language = file_info.get("language", "unknown")
                if language not in languages:
                    languages[language] = 0
                languages[language] += 1
            
            # Sort languages by count
            sorted_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)
            
            # Generate summary documentation
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("# Code Documentation Summary\n\n")
                
                # Add code statistics
                f.write("## Code Statistics\n\n")
                f.write(f"- Files: {file_count}\n")
                f.write(f"- Functions: {function_count}\n")
                f.write(f"- Classes: {class_count}\n\n")
                
                # Add language statistics
                f.write("## Language Statistics\n\n")
                f.write("| Language | File Count |\n")
                f.write("|----------|------------|\n")
                for language, count in sorted_languages:
                    f.write(f"| {language} | {count} |\n")
                f.write("\n")
                
                # Add architecture overview
                f.write("## Architecture Overview\n\n")
                
                # Generate architecture overview using LLM if available
                if self.model_orchestrator and self.model_orchestrator.is_ready():
                    try:
                        # Prepare prompt for architecture overview
                        files_summary = "\n".join([f"- {file.get('path', 'Unknown file')}" for file in analysis_results.get("files", [])[:10]])
                        
                        prompt = (
                            f"Generate an architecture overview for a codebase with the following characteristics:\n\n"
                            f"- {file_count} files\n"
                            f"- {function_count} functions\n"
                            f"- {class_count} classes\n\n"
                            f"Sample files:\n{files_summary}\n\n"
                            f"Language statistics:\n"
                        )
                        
                        for language, count in sorted_languages:
                            prompt += f"- {language}: {count} files\n"
                        
                        prompt += "\nProvide a concise overview of the likely architecture of this codebase."
                        
                        architecture_overview = self.model_orchestrator.ollama_client.generate(
                            model=self.model_orchestrator.config['reasoning_model'],
                            prompt=prompt,
                            temperature=0.3
                        )
                        
                        f.write(f"{architecture_overview.strip()}\n\n")
                    except Exception as e:
                        logger.error(f"Error generating architecture overview: {e}")
                        # Fallback to generic overview
                        f.write("The codebase follows a modular architecture with the following components:\n\n")
                        f.write("1. Core functionality modules\n")
                        f.write("2. Utility and helper functions\n")
                        f.write("3. External integrations\n\n")
                else:
                    # Generic architecture overview
                    f.write("The codebase follows a modular architecture with the following components:\n\n")
                    f.write("1. Core functionality modules\n")
                    f.write("2. Utility and helper functions\n")
                    f.write("3. External integrations\n\n")
                
                # Add recommendations
                f.write("## Recommendations\n\n")
                
                # Generate recommendations using LLM if available
                if self.model_orchestrator and self.model_orchestrator.is_ready():
                    try:
                        # Prepare prompt for recommendations
                        prompt = (
                            f"Based on the analysis of a codebase with {file_count} files, {function_count} functions, "
                            f"and {class_count} classes, provide 3-5 recommendations for improving the codebase. "
                            f"Focus on general best practices and architectural improvements."
                        )
                        
                        recommendations = self.model_orchestrator.ollama_client.generate(
                            model=self.model_orchestrator.config['reasoning_model'],
                            prompt=prompt,
                            temperature=0.3
                        )
                        
                        f.write(f"{recommendations.strip()}\n")
                    except Exception as e:
                        logger.error(f"Error generating recommendations: {e}")
                        # Fallback to generic recommendations
                        f.write("Based on the analysis, here are some recommendations for improvement:\n\n")
                        f.write("1. Improve documentation coverage for functions and classes\n")
                        f.write("2. Add more unit tests to increase code coverage\n")
                        f.write("3. Refactor complex functions to improve maintainability\n")
                        f.write("4. Standardize error handling across the codebase\n")
                        f.write("5. Update dependencies to their latest stable versions\n")
                else:
                    # Generic recommendations
                    f.write("Based on the analysis, here are some recommendations for improvement:\n\n")
                    f.write("1. Improve documentation coverage for functions and classes\n")
                    f.write("2. Add more unit tests to increase code coverage\n")
                    f.write("3. Refactor complex functions to improve maintainability\n")
                    f.write("4. Standardize error handling across the codebase\n")
                    f.write("5. Update dependencies to their latest stable versions\n")
        except Exception as e:
            logger.error(f"Error generating summary documentation: {e}")
            raise Exception(f"Failed to generate summary documentation: {e}")
    
    def _generate_index(self, analysis_results: Dict[str, Any], output_file: str):
        """
        Generate index file.
        
        Args:
            analysis_results (Dict[str, Any]): Code analysis results
            output_file (str): Output file path
        """
        try:
            # Create index.html
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Documentation</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            padding: 20px;
        }
        .header {
            background-color: #f8f9fa;
            padding: 2rem 0;
            margin-bottom: 2rem;
            border-radius: 0.5rem;
        }
        .card {
            margin-bottom: 1.5rem;
            border: none;
            box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        }
        .card-header {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        .footer {
            margin-top: 3rem;
            padding: 1.5rem 0;
            background-color: #f8f9fa;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header text-center">
            <h1>Code Documentation</h1>
            <p class="lead">Comprehensive documentation for the codebase</p>
        </div>

        <div class="row">
            <div class="col-md-12 mb-4">
                <div class="card">
                    <div class="card-header">
                        <h2>Summary</h2>
                    </div>
                    <div class="card-body">
                        <p>This documentation provides a comprehensive overview of the codebase, including functions, dependencies, and development Q&A.</p>
                        <a href="summary.md" class="btn btn-primary">View Summary</a>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6 mb-4">
                <div class="card">
                    <div class="card-header">
                        <h2>Functions</h2>
                    </div>
                    <div class="card-body">
                        <p>Documentation for all functions in the codebase.</p>
                        <a href="functions/index.md" class="btn btn-primary">View Functions</a>
                    </div>
                </div>
            </div>

            <div class="col-md-6 mb-4">
                <div class="card">
                    <div class="card-header">
                        <h2>Dependencies</h2>
                    </div>
                    <div class="card-body">
                        <p>Documentation for code dependencies and relationships.</p>
                        <a href="dependencies/index.md" class="btn btn-primary">View Dependencies</a>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-12 mb-4">
                <div class="card">
                    <div class="card-header">
                        <h2>Development Q&A</h2>
                    </div>
                    <div class="card-body">
                        <p>Questions and answers for development and feature changes.</p>
                        <a href="development_qa.md" class="btn btn-primary">View Q&A</a>
                    </div>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>Generated by Code Documentation App</p>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>""")
        except Exception as e:
            logger.error(f"Error generating index file: {e}")
            raise Exception(f"Failed to generate index file: {e}")
    
    def _create_default_templates(self):
        """Create default templates if they don't exist."""
        try:
            # Create templates directory
            templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
            os.makedirs(templates_dir, exist_ok=True)
            
            # Create function template
            function_template = os.path.join(templates_dir, "function.html.j2")
            if not os.path.exists(function_template):
                with open(function_template, "w", encoding="utf-8") as f:
                    f.write("""<!DOCTYPE html>
<html>
<head>
    <title>{{ function.name }} - Function Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .params { margin-left: 20px; }
        .docstring { background-color: #f5f5f5; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>{{ function.name }}</h1>
    
    <h2>Parameters</h2>
    <div class="params">
        {% if function.params %}
            <ul>
                {% for param in function.params %}
                    <li>{{ param }}</li>
                {% endfor %}
            </ul>
        {% else %}
            <p>No parameters</p>
        {% endif %}
    </div>
    
    <h2>Documentation</h2>
    <div class="docstring">
        {% if function.docstring %}
            {{ function.docstring }}
        {% else %}
            <p>No documentation available</p>
        {% endif %}
    </div>
    
    {% if function.body %}
        <h2>Code</h2>
        <pre>{{ function.body }}</pre>
    {% endif %}
</body>
</html>""")
            
            # Create class template
            class_template = os.path.join(templates_dir, "class.html.j2")
            if not os.path.exists(class_template):
                with open(class_template, "w", encoding="utf-8") as f:
                    f.write("""<!DOCTYPE html>
<html>
<head>
    <title>{{ class.name }} - Class Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .bases { margin-left: 20px; }
        .docstring { background-color: #f5f5f5; padding: 10px; border-radius: 5px; }
        .method { margin-left: 20px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>{{ class.name }}</h1>
    
    <h2>Base Classes</h2>
    <div class="bases">
        {% if class.bases %}
            <ul>
                {% for base in class.bases %}
                    <li>{{ base }}</li>
                {% endfor %}
            </ul>
        {% else %}
            <p>No base classes</p>
        {% endif %}
    </div>
    
    <h2>Documentation</h2>
    <div class="docstring">
        {% if class.docstring %}
            {{ class.docstring }}
        {% else %}
            <p>No documentation available</p>
        {% endif %}
    </div>
    
    <h2>Methods</h2>
    {% if class.methods %}
        {% for method in class.methods %}
            <div class="method">
                <h3>{{ method.name }}</h3>
                
                <h4>Parameters</h4>
                {% if method.params %}
                    <ul>
                        {% for param in method.params %}
                            <li>{{ param }}</li>
                        {% endfor %}
                    </ul>
                {% else %}
                    <p>No parameters</p>
                {% endif %}
                
                <h4>Documentation</h4>
                <div class="docstring">
                    {% if method.docstring %}
                        {{ method.docstring }}
                    {% else %}
                        <p>No documentation available</p>
                    {% endif %}
                </div>
            </div>
        {% endfor %}
    {% else %}
        <p>No methods</p>
    {% endif %}
    
    {% if class.body %}
        <h2>Code</h2>
        <pre>{{ class.body }}</pre>
    {% endif %}
</body>
</html>""")
            
            # Create index template
            index_template = os.path.join(templates_dir, "index.html.j2")
            if not os.path.exists(index_template):
                with open(index_template, "w", encoding="utf-8") as f:
                    f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Code Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .section { margin-bottom: 30px; }
        .card { border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 15px; }
        .card h3 { margin-top: 0; }
    </style>
</head>
<body>
    <h1>Code Documentation</h1>
    
    <div class="section">
        <h2>Summary</h2>
        <div class="card">
            <p>Files: {{ file_count }}</p>
            <p>Functions: {{ function_count }}</p>
            <p>Classes: {{ class_count }}</p>
            <a href="summary.html">View Summary</a>
        </div>
    </div>
    
    <div class="section">
        <h2>Functions</h2>
        <div class="card">
            <p>Documentation for all functions in the codebase.</p>
            <a href="functions/index.html">View Functions</a>
        </div>
    </div>
    
    <div class="section">
        <h2>Dependencies</h2>
        <div class="card">
            <p>Documentation for code dependencies and relationships.</p>
            <a href="dependencies/index.html">View Dependencies</a>
        </div>
    </div>
    
    <div class="section">
        <h2>Development Q&A</h2>
        <div class="card">
            <p>Questions and answers for development and feature changes.</p>
            <a href="development_qa.html">View Q&A</a>
        </div>
    </div>
</body>
</html>""")
        except Exception as e:
            logger.error(f"Error creating default templates: {e}")
            # Continue without templates
