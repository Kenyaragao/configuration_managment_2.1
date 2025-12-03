import argparse
import json
import sys
import os
import requests
from lxml import etree 

# --- GraphBuilder Class ---

class GraphBuilder:
    def __init__(self, start_package, config):
        self.start_package = start_package
        self.config = config
        # Adjacency list: {package: [direct_dependencies]}
        self.graph = {}  
        self.reverse_graph = {} # New: {dependency: [dependents]}

    def _load_test_graph(self):
        """Loads the test graph from a file."""
        graph_path = self.config.get('test_graph_path')
        if not graph_path or not os.path.exists(graph_path):
            raise FileNotFoundError(f"Error: Test graph file not found at '{graph_path}'.")

        print(f"Loading dependencies from test file: {graph_path}")
        
        with open(graph_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if ':' in line:
                    parent, deps_str = line.split(':', 1)
                    parent = parent.strip()
                    dependencies = [dep.strip() for dep in deps_str.split(',') if dep.strip()]
                    self.graph[parent] = dependencies
                elif line.strip():
                    self.graph[line.strip()] = []

    def build_dependency_graph(self):
        """
        Builds the full transitive dependency graph using non-recursive DFS.
        """
        if self.config['repo_mode'] == 'local':
            self._load_test_graph()
        
        stack = [(self.start_package, iter(self.graph.get(self.start_package, [])))]
        visited = set()
        recursion_stack = {self.start_package}
        
        full_graph = {pkg: [] for pkg in self.graph.keys()} 
        if self.start_package not in full_graph:
            full_graph[self.start_package] = []
            
        print("Starting DFS traversal...")

        while stack:
            parent, children_iterator = stack[-1]

            try:
                child = next(children_iterator)
                
                if child not in full_graph:
                    full_graph[child] = []
                full_graph[parent].append(child)

                # Cycle Detection
                if child in recursion_stack:
                    print(f"⚠️ **CYCLE DETECTED:** Cycle involving {child} found.")
                    continue 
                
                # Push child onto stack
                child_deps_iterator = iter(self.graph.get(child, []))
                
                stack.append((child, child_deps_iterator))
                recursion_stack.add(child)
                
                if child not in self.graph and child not in visited:
                    visited.add(child)

            except StopIteration:
                recursion_stack.remove(parent) 
                visited.add(parent)
                stack.pop()
            
        return full_graph

    def build_reverse_graph(self):
        """
        New Stage 4 Logic: Constructs the reverse graph.
        {dependency: [dependents]}
        """
        for parent, children in self.graph.items():
            for child in children:
                if child not in self.reverse_graph:
                    self.reverse_graph[child] = []
                self.reverse_graph[child].append(parent)
        
        return self.reverse_graph
        
    def get_reverse_dependencies(self, target_package):
        """
        Finds all packages that depend directly or transitively on the target_package.
        Uses the pre-built reverse graph.
        """
        # Ensure the reverse graph is built
        if not self.reverse_graph:
             self.build_reverse_graph()
        
        if target_package not in self.reverse_graph:
            return []

        # Use BFS on the reverse graph to find all transitive dependents
        # BFS is simpler here as we only need the list, not the path structure
        queue = [target_package]
        reverse_deps = set()
        
        while queue:
            current = queue.pop(0)
            
            # Find direct dependents of the current package
            dependents = self.reverse_graph.get(current, [])
            
            for dep in dependents:
                if dep not in reverse_deps:
                    reverse_deps.add(dep)
                    queue.append(dep)

        # Remove the target package itself and return the list
        return sorted(list(reverse_deps))

# --- Utility Functions ---

def display_graph(graph):
    """Displays the built dependency graph."""
    print("\n=== Dependency Graph (DFS-Built) ===")
    if not graph:
        print("Graph is empty.")
        return
        
    displayed_edges = set() 
    for parent, children in graph.items():
        if children:
            for child in children:
                edge = (parent, child)
                if edge not in displayed_edges:
                    print(f"{parent} -> {child}")
                    displayed_edges.add(edge)

def display_reverse_dependencies(target_package, dependencies):
    """Displays the reverse dependencies (Stage 4 requirement)."""
    print(f"\n=== Reverse Dependencies for Package: {target_package} ===")
    if not dependencies:
        print(f"No packages found that depend on '{target_package}'.")
    else:
        for dep in dependencies:
            print(f"- {dep}")

# --- Main Execution Flow ---

def load_config(config_path):
    # ... (Same as previous stage load_config) ...
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Error: The configuration file not found at '{config_path}'.")
    with open(config_path, 'r') as f:
        return json.load(f)

def validate_config(config):
    # ... (Same as previous stage validate_config) ...
    required_params = ['package_name', 'repository_source', 'repo_mode', 'package_version', 'test_graph_path']
    for param in required_params:
        if param not in config:
            raise ValueError(f"Configuration Error: The required parameter '{param}' is missing.")
    return config

def main():
    parser = argparse.ArgumentParser(
        description="CLI tool for dependency graph visualization. Stage 4: Reverse Dependencies."
    )
    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help="Path to the JSON configuration file."
    )
    # New argument for Stage 4
    parser.add_argument(
        '--target-package',
        type=str,
        required=False,
        help="The package for which to find reverse dependencies (who depends on this package)."
    )

    args = parser.parse_args()
    
    # 1. Load and Validate configuration
    try:
        config_data = load_config(args.config)
        validated_config = validate_config(config_data)
        
        start_package = validated_config['package_name']
        
        builder = GraphBuilder(start_package, validated_config)
        
        # Always build the forward graph first to load dependencies
        dependency_graph = builder.build_dependency_graph()
        
        # --- Stage 4 Execution ---
        if args.target_package:
            print("\n--- Starting Stage 4: Reverse Dependency Search ---")
            
            # Get the result
            reverse_deps = builder.get_reverse_dependencies(args.target_package)
            
            # Display the result
            display_reverse_dependencies(args.target_package, reverse_deps)
            
            print("\n--- Stage 4 Completed Successfully. ---")
            
        else:
            # --- Stage 3 Display (Default if no target package specified) ---
            print("\n--- Starting Stage 3: Graph Construction (Default Display) ---")
            display_graph(dependency_graph)
            print("\n--- Stage 3 Completed Successfully. ---")


    except (FileNotFoundError, ValueError, Exception) as e:
        print(f"\n❌ FATAL ERROR:")
        print(f"{e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()