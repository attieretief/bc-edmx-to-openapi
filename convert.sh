#!/bin/bash

set -e

# EDMX to Enhanced OpenAPI Converter
# 
# This script works both as a standalone CLI tool and as a GitHub Action entrypoint.
# It auto-detects the environment and adapts accordingly.

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect if running in GitHub Actions
is_github_actions() {
    [[ -n "$GITHUB_ACTIONS" ]] || [[ -n "$GITHUB_WORKSPACE" ]] || [[ -d "/github/workspace" ]]
}

# Function to show usage (for CLI mode)
show_usage() {
    echo "Usage: $0 <input_edmx_file> <output_json_file> [OPTIONS]"
    echo ""
    echo "Positional Arguments:"
    echo "  input_edmx_file     Path to input EDMX file"
    echo "  output_json_file    Path for output OpenAPI JSON file"
    echo ""
    echo "Options:"
    echo "  --title TITLE                API title"
    echo "  --description DESC           API description"
    echo "  --api-name NAME             API name for URLs (e.g., 'produceLinc', 'myApp')"
    echo "  --api-version VERSION       API version for URLs (e.g., 'v1.0', 'v2.0')"
    echo "  --tenant-placeholder PLACEHOLDER  Tenant placeholder for OAuth (e.g., '{tenant_id}')"
    echo "  --no-html                   Skip HTML generation"
    echo ""
    echo "Examples:"
    echo "  $0 docs/api.xml docs/api_enhanced.json"
    echo "  $0 docs/api.xml docs/api_enhanced.json --title \"My Custom API\""
    echo "  $0 docs/api.xml docs/api_enhanced.json --api-name \"ProduceLinc\" --api-version \"v1.0\""
    echo ""
    echo "GitHub Actions Mode:"
    echo "  When running in GitHub Actions, arguments are passed positionally:"
    echo "  $0 \$INPUT_PATH \$OUTPUT_PATH \$API_NAME \$TITLE \$DESCRIPTION \$API_VERSION \$TENANT_PLACEHOLDER"
    echo ""
}

# Initialize variables
INPUT_FILE=""
OUTPUT_FILE=""
TITLE=""
DESCRIPTION=""
API_NAME=""
API_VERSION=""
TENANT_PLACEHOLDER=""
GENERATE_HTML=true

# Parse arguments based on environment
if is_github_actions; then
    # GitHub Actions mode - positional arguments
    print_status "EDMX to Enhanced OpenAPI Converter - GitHub Action Mode"
    print_status "======================================================"
    
    INPUT_FILE="$1"
    OUTPUT_FILE="$2"
    API_NAME="$3"
    TITLE="$4"
    DESCRIPTION="$5"
    API_VERSION="$6"
    TENANT_PLACEHOLDER="$7"
    
    # Convert to absolute paths within the workspace
    WORKSPACE="${GITHUB_WORKSPACE:-/github/workspace}"
    if [[ "$INPUT_FILE" != /* ]]; then
        INPUT_FILE="${WORKSPACE}/${INPUT_FILE}"
    fi
    if [[ "$OUTPUT_FILE" != /* ]]; then
        OUTPUT_FILE="${WORKSPACE}/${OUTPUT_FILE}"
    fi
    
else
    # CLI mode - flexible argument parsing
    print_status "EDMX to Enhanced OpenAPI Converter - CLI Mode"
    print_status "============================================="
    
    # Check minimum arguments
    if [ $# -lt 2 ]; then
        show_usage
        exit 1
    fi
    
    # Get required positional arguments
    INPUT_FILE="$1"
    OUTPUT_FILE="$2"
    shift 2
    
    # Check if using legacy positional arguments (no -- flags)
    if [ $# -gt 0 ] && [[ "$1" != --* ]]; then
        # Legacy positional argument mode
        TITLE="$1"
        DESCRIPTION="$2"
        API_NAME="$3"
        API_VERSION="$4"
        TENANT_PLACEHOLDER="$5"
    else
        # Parse named arguments
        while [[ $# -gt 0 ]]; do
            case $1 in
                --title)
                    TITLE="$2"
                    shift 2
                    ;;
                --description)
                    DESCRIPTION="$2"
                    shift 2
                    ;;
                --api-name)
                    API_NAME="$2"
                    shift 2
                    ;;
                --api-version)
                    API_VERSION="$2"
                    shift 2
                    ;;
                --tenant-placeholder)
                    TENANT_PLACEHOLDER="$2"
                    shift 2
                    ;;
                --no-html)
                    GENERATE_HTML=false
                    shift
                    ;;
                -h|--help)
                    show_usage
                    exit 0
                    ;;
                *)
                    print_error "Unknown option: $1"
                    show_usage
                    exit 1
                    ;;
            esac
        done
    fi
fi

# Validate required inputs
if [ -z "$INPUT_FILE" ] || [ -z "$OUTPUT_FILE" ]; then
    print_error "Both input and output files are required"
    if ! is_github_actions; then
        show_usage
    fi
    exit 1
fi

# Display configuration
print_status "Input file: $INPUT_FILE"
print_status "Output file: $OUTPUT_FILE"

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    print_error "Input file '$INPUT_FILE' not found!"
    exit 1
fi

# For CLI mode, check dependencies
if ! is_github_actions; then
    # Check if npx is available
    if ! command -v npx &> /dev/null; then
        print_error "npx not found! Please install Node.js and npm."
        exit 1
    fi

    print_status "Checking for odata-openapi3 tool..."
    if ! npx odata-openapi3 --help &> /dev/null; then
        print_warning "odata-openapi3 not found. Installing..."
        npm install -g odata-openapi
        print_success "odata-openapi3 installed successfully!"
    fi
fi

# Create output directory if it doesn't exist
OUTPUT_DIR=$(dirname "$OUTPUT_FILE")
mkdir -p "$OUTPUT_DIR"

# Build the Python command
PYTHON_SCRIPT="/action/edmx_to_enhanced_openapi.py"
if ! is_github_actions; then
    # In CLI mode, use the script from the same directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PYTHON_SCRIPT="${SCRIPT_DIR}/edmx_to_enhanced_openapi.py"
fi

PYTHON_CMD="python3 \"$PYTHON_SCRIPT\" \"$INPUT_FILE\" \"$OUTPUT_FILE\""

# Add optional parameters if provided
if [ -n "$TITLE" ] && [ "$TITLE" != "null" ]; then
    PYTHON_CMD="$PYTHON_CMD --title \"$TITLE\""
    print_status "Title: $TITLE"
fi

if [ -n "$DESCRIPTION" ] && [ "$DESCRIPTION" != "null" ]; then
    PYTHON_CMD="$PYTHON_CMD --description \"$DESCRIPTION\""
    print_status "Description: $DESCRIPTION"
fi

if [ -n "$API_NAME" ] && [ "$API_NAME" != "null" ]; then
    PYTHON_CMD="$PYTHON_CMD --api-name \"$API_NAME\""
    print_status "API Name: $API_NAME"
fi

if [ -n "$API_VERSION" ] && [ "$API_VERSION" != "null" ]; then
    PYTHON_CMD="$PYTHON_CMD --api-version \"$API_VERSION\""
    print_status "API Version: $API_VERSION"
fi

if [ -n "$TENANT_PLACEHOLDER" ] && [ "$TENANT_PLACEHOLDER" != "null" ]; then
    PYTHON_CMD="$PYTHON_CMD --tenant-placeholder \"$TENANT_PLACEHOLDER\""
    print_status "Tenant Placeholder: $TENANT_PLACEHOLDER"
fi

print_status "Starting conversion..."

# Execute the Python script
if eval $PYTHON_CMD; then
    print_success "Conversion completed successfully!"
    print_success "Enhanced OpenAPI file saved to: $OUTPUT_FILE"
    
    # Set GitHub Action outputs if in GitHub Actions
    if is_github_actions; then
        # Convert back to relative path for output
        REL_OUTPUT_FILE="${OUTPUT_FILE#$WORKSPACE/}"
        echo "output-file=$REL_OUTPUT_FILE" >> $GITHUB_OUTPUT
    fi
    
    # Get file size if possible
    if [ -f "$OUTPUT_FILE" ]; then
        FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
        if is_github_actions; then
            echo "file-size=$FILE_SIZE" >> $GITHUB_OUTPUT
        fi
        print_status "Output file size: $FILE_SIZE"
        
        # Show line count
        LINE_COUNT=$(wc -l < "$OUTPUT_FILE")
        print_status "Total lines: $LINE_COUNT"
    fi
    
    # Generate HTML viewer if enabled
    if [ "$GENERATE_HTML" = true ]; then
        HTML_OUTPUT_FILE="${OUTPUT_DIR}/index.html"
        
        if [ ! -f "$HTML_OUTPUT_FILE" ]; then
            print_status "Creating index.html documentation viewer..."
            
            # Get the OpenAPI filename for the HTML
            OPENAPI_FILENAME=$(basename "$OUTPUT_FILE")
            
            cat > "$HTML_OUTPUT_FILE" << 'EOF'
<!doctype html>
<html>
  <head>
    <title>API Reference</title>
    <meta charset="utf-8" />
    <meta
      name="viewport"
      content="width=device-width, initial-scale=1" />
  </head>
  <body>
    <div id="app"></div>
    <!-- Load the Script -->
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
    <!-- Initialize the Scalar API Reference -->
    <script>
      Scalar.createApiReference('#app', {
        url: './OPENAPI_FILENAME',
        proxyUrl: 'https://proxy.scalar.com',
        darkMode: false,
        documentDownloadType: 'none',
        hideClientButton: true,
        hideModels: true,
        layout: 'modern',
        showToolbar: 'never',
        theme: 'bluePlanet',
      })
    </script>
  </body>
</html>
EOF
            
            # Replace the placeholder with actual filename
            if command -v sed &> /dev/null; then
                sed -i.bak "s/OPENAPI_FILENAME/$OPENAPI_FILENAME/g" "$HTML_OUTPUT_FILE" && rm -f "$HTML_OUTPUT_FILE.bak"
            else
                # Fallback for systems without sed
                python3 -c "
import sys
with open('$HTML_OUTPUT_FILE', 'r') as f:
    content = f.read()
content = content.replace('OPENAPI_FILENAME', '$OPENAPI_FILENAME')
with open('$HTML_OUTPUT_FILE', 'w') as f:
    f.write(content)
"
            fi
            
            print_success "Created index.html documentation viewer at: $HTML_OUTPUT_FILE"
            
            if is_github_actions; then
                REL_HTML_FILE="${HTML_OUTPUT_FILE#$WORKSPACE/}"
                echo "html-file=$REL_HTML_FILE" >> $GITHUB_OUTPUT
            fi
        else
            print_status "index.html already exists, skipping creation"
        fi
    fi
    
    echo ""
    print_success "✅ Your enhanced OpenAPI file is ready!"
    echo "   📄 OpenAPI JSON: $OUTPUT_FILE"
    if [ "$GENERATE_HTML" = true ]; then
        echo "   🌐 HTML Viewer: ${OUTPUT_DIR}/index.html"
    fi
    echo "   You can now use it with documentation tools like Scalar, Swagger UI, or Redoc."
    
else
    print_error "Conversion failed!"
    exit 1
fi