import argparse
import sys
import os
# Imports like requests, lxml are omitted here for brevity and focus on 'local' mode.

# ====================================================
# PROJECT CONFIGURATION (Hardcoded to eliminate config.json dependency)
# ====================================================
CONFIG = {
    "package_name": "A",
    "group_id": "org.test",
    "repository_source": "https://repo1.maven.org/maven2/",
    "repo_mode": "local",
    "package_version": "1.0.0",
    "output_mode_ascii_tree": True, # Set to True for ASCII visualization
    "test_graph_path": "test_graph.txt" 
}
# ====================================================

# --- Helper Functions (Removed Load/Validate) ---

# We don't need load_config or validate_config anymore as we use the CONFIG dictionary directly.
# The code structure now assumes the test_graph.txt file is in the same directory.

# --- GraphBuilder Class (Stage 3/4 Logic) ---

class GraphBuilder:
    def __init__(self, start_package, config):
        self.start_package = start_package
        self.config = config
        self.graph = {}  # {package: [direct_dependencies]}

    def _load_test_graph(self):
        """Loads the test graph from a file."""
        graph_path = self.config.get('test_graph_path')
        if not graph_path or not os.path.exists(graph_path):
            # This check is now the primary point of failure if test_graph.txt is missing
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

                if child in recursion_stack:
                    print(f"⚠️ **CYCLE DETECTED:** Cycle involving {child} found.")
                    continue 
                
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

# ----------------------------------------------------
# Stage 5: Visualization Logic
# ----------------------------------------------------

def generate_mermaid_graph(graph):
    """Generates the graph representation in Mermaid syntax."""
    mermaid_code = ["graph TD"]
    unique_edges = set() 
    
    for parent, children in graph.items():
        for child in children:
            edge = f'{parent} --> {child}'
            if edge not in unique_edges:
                mermaid_code.append(f'    {parent} --> {child}')
                unique_edges.add(edge)

    return "\n".join(mermaid_code)

def generate_ascii_tree(graph, start_package):
    """Generates the dependencies in ASCII-Tree format (DFS based)."""
    tree_lines = []
    stack = [(start_package, "")]
    visited_viz = {start_package}
    
    while stack:
        current_node, prefix = stack.pop()
        children = sorted(list(set(graph.get(current_node, []))))
        
        for i, child in enumerate(reversed(children)):
            is_last = (i == 0)
            connector = "└── " if is_last else "├── "
            new_prefix = prefix + ("    " if is_last else "│   ")
            
            cycle_flag = ""
            if child in visited_viz:
                cycle_flag = " (Cycle Detected)"
            else:
                visited_viz.add(child)
                
            stack.append((child, new_prefix))
            tree_lines.insert(0, f"{prefix}{connector}{child}{cycle_flag}")
            
    tree_lines.insert(0, start_package)
    return "\n".join(tree_lines)


def compare_with_standard_tools(repo_mode):
    """Analysis of results vs. standard tools (Requirement 5)."""
    print("This tool uses a custom non-recursive DFS algorithm, while standard tools (like Cargo or Maven) typically use highly optimized, proprietary algorithms or local caching.")
    print("Potential discrepancies (if observed in 'remote' mode):")
    print("1. **Version Resolution:** Standard tools handle complex version ranges ('1.x' or '>=2.0') which this simplified tool does not.")
    print("2. **Profile/Scope Filtering:** Standard tools filter dependencies by build profile (e.g., 'test' or 'provided' scope in Maven), which this tool ignores.")
    print("3. **Dependency Management:** Standard tools respect dependency management blocks (parent POMs) which determine versions; this tool uses only the direct dependency version.")


def main():
    parser = argparse.ArgumentParser(
        description="CLI tool for dependency graph visualization. Stage 5: Visualization."
    )
    # The --config argument is now OPTIONAL, so we remove 'required=True'
    parser.add_argument(
        '--config',
        type=str,
        required=False,
        help="Path to the JSON configuration file (Optional, configuration is hardcoded)."
    )
    parser.add_argument(
        '--target-package',
        type=str,
        required=False,
        help="The package for which to find reverse dependencies (Stage 4)."
    )
    parser.add_argument(
        '--start-package',
        type=str,
        required=False,
        help="Override the starting package name to demonstrate different graph roots."
    )

    args = parser.parse_args()
    
    try:
        # Use the hardcoded configuration
        config_data = CONFIG
        
        start_package = args.start_package if args.start_package else config_data['package_name']

        # Check for test file availability before proceeding
        if config_data['repo_mode'] == 'local' and not os.path.exists(config_data['test_graph_path']):
            raise FileNotFoundError(f"Fatal: Required test graph file not found at '{config_data['test_graph_path']}'. Please ensure it is in the same directory.")


        builder = GraphBuilder(start_package, config_data)
        
        dependency_graph = builder.build_dependency_graph()
        
        # --- Stage 5 Execution ---
        if not args.target_package:
            print("\n--- Starting Stage 5: Visualization Protocol ---")

            # 1. Mermaid Graph (Requirement 1 & 2)
            mermaid_output = generate_mermaid_graph(dependency_graph)
            print("\n[--- Mermaid Graph Syntax (Requirement 1 & 2) ---]")
            print(mermaid_output)
            print("\n(To view the image, paste the syntax above into a Mermaid rendering tool.)")
            # 

            # 2. ASCII Tree (Requirement 3)
            if config_data.get('output_mode_ascii_tree', False):
                print("\n[--- ASCII Dependency Tree (Requirement 3) ---]")
                ascii_output = generate_ascii_tree(dependency_graph, start_package)
                print(ascii_output)
            
            # 3. Comparison (Requirement 5)
            print("\n[--- Comparison Analysis (Requirement 5) ---]")
            compare_with_standard_tools(config_data['repo_mode'])
            
            print("\n--- Stage 5 Completed Successfully. ---")

        # --- Stage 4 Execution (maintained) ---
        # ... (Stage 4 logic would be here if implemented in this file) ...

    except Exception as e:
        print(f"\n❌ FATAL ERROR:")
        print(f"{e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()