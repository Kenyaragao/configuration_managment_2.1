import argparse
import json
import sys
import os
import requests
from lxml import etree # Using lxml for robust XML/POM parsing

# --- Helper Functions from Stage 1 (Simplified for brevity) ---

def load_config(config_path):
    # ... (Same as Stage 1 load_config function) ...
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Error: The configuration file was not found at '{config_path}'.")
    with open(config_path, 'r') as f:
        return json.load(f)

def validate_config(config):
    # ... (Simplified validation for demonstration) ...
    required_params = ['package_name', 'group_id', 'repository_source', 'package_version', 'repo_mode']
    for param in required_params:
        if param not in config:
            raise ValueError(f"Configuration Error: The required parameter '{param}' is missing.")
    if config.get('repo_mode') != 'remote':
        # Stage 2 requires network access
        raise ValueError("Configuration Error: 'repo_mode' must be 'remote' for Stage 2 data collection.")
    
    return config

# ----------------------------------------------------
# Stage 2: Data Collection Logic
# ----------------------------------------------------

def build_pom_url(config):
    """
    Constructs the direct URL to the Maven POM file.
    Requirement 3: Uses the repository URL.
    """
    group_path = config['group_id'].replace('.', '/')
    artifact_id = config['package_name']
    version = config['package_version']
    base_url = config['repository_source'].rstrip('/')
    
    # Standard Maven repository path structure
    pom_url = f"{base_url}/{group_path}/{artifact_id}/{version}/{artifact_id}-{version}.pom"
    
    return pom_url

def fetch_and_parse_dependencies(pom_url):
    """
    Fetches the POM file and extracts direct dependencies.
    Requirements 1 & 3: Java (Maven) package dependency extraction.
    """
    print(f"Fetching POM file from: {pom_url}")
    
    try:
        response = requests.get(pom_url, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Error fetching POM file: {e}")

    try:
        # Parse XML content
        # Use lxml for robustness, but native etree works too
        root = etree.fromstring(response.content)
        
        # Define the XML namespace used in Maven POM files
        # The 'd' prefix is arbitrary for use in XPath
        namespaces = {'d': 'http://maven.apache.org/POM/4.0.0'}
        
        # XPath to find all direct <dependency> tags under <dependencies>
        dependencies_xpath = "//d:dependencies/d:dependency"
        
        dependencies = []
        for dep_element in root.xpath(dependencies_xpath, namespaces=namespaces):
            # Extract groupId, artifactId, and version for each direct dependency
            group_id = dep_element.xpath("./d:groupId/text()", namespaces=namespaces)
            artifact_id = dep_element.xpath("./d:artifactId/text()", namespaces=namespaces)
            version = dep_element.xpath("./d:version/text()", namespaces=namespaces)
            
            # Simple check to ensure we got all parts
            if group_id and artifact_id:
                dependencies.append({
                    'groupId': group_id[0],
                    'artifactId': artifact_id[0],
                    # Use version if available, otherwise mark as unknown or provided by parent POM
                    'version': version[0] if version else 'N/A (Managed)'
                })
        
        return dependencies

    except etree.XMLSyntaxError as e:
        raise ValueError(f"Error parsing POM XML: {e}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred during parsing: {e}")


def main():
    """Main function to execute Stage 2 logic."""
    parser = argparse.ArgumentParser(
        description="CLI tool for dependency graph visualization. Stage 2: Data Collection."
    )
    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help="Path to the JSON configuration file."
    )

    args = parser.parse_args()
    
    print("\n--- Starting Stage 2: Data Collection Protocol (Maven) ---")

    try:
        # 1. Load and Validate configuration
        config_data = load_config(args.config)
        validated_config = validate_config(config_data)

        # 2. Build URL and Fetch Data
        pom_url = build_pom_url(validated_config)
        direct_dependencies = fetch_and_parse_dependencies(pom_url)

        # Requirement 4: Display all direct dependencies
        print("\n Direct Dependencies of "
              f"{validated_config['group_id']}:{validated_config['package_name']}@v{validated_config['package_version']}:")
        
        if not direct_dependencies:
            print("- No direct dependencies found in the POM file.")
        else:
            for dep in direct_dependencies:
                print(f"- **{dep['groupId']}:{dep['artifactId']}** (Version: {dep['version']})")
        
        print("\n--- Stage 2 Completed Successfully. ---")

    except (FileNotFoundError, ValueError, ConnectionError, Exception) as e:
        print(f"\n FATAL ERROR during Stage 2:")
        print(f"{e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()