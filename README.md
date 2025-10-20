# EDMX to Enhanced OpenAPI Converter Action

A GitHub Action that converts Business Central EDMX (Entity Data Model XML) files to enhanced OpenAPI 3.1.1 format with Business Central-specific configurations.

## Features

- 🔄 Converts EDMX files to OpenAPI 3.1.1 JSON format
- � **Generates interactive HTML documentation viewer**
- �🏢 Adds Business Central-specific server configurations
- 🔐 Includes OAuth2 security schemes for Business Central
- 📝 Enhances documentation with custom titles and descriptions
- 🎯 Configurable API names and versions for URL generation
- 📊 Provides file size and line count outputs

## Usage

### Basic Usage

```yaml
- name: Convert EDMX to OpenAPI
  uses: attieretief/bc-edmx-to-openapi@v1
  with:
    input-path: 'docs/api.xml'
    output-path: 'docs/api.json'
    api-name: 'MyAPI'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `input-path` | Path to the input EDMX file relative to repository root | ✅ | |
| `output-path` | Path where the output OpenAPI JSON file should be saved relative to repository root | ✅ | |
| `api-name` | API name for URLs and documentation (e.g., "produceLinc", "myApp") | ❌ | |
| `title` | Custom API title | ❌ | |
| `description` | Custom API description | ❌ | |
| `api-version` | API version for URLs (e.g., "v1.0", "v2.0") | ❌ | `v1.0` |
| `tenant-placeholder` | Tenant ID placeholder for OAuth URLs | ❌ | `{tenant_id}` |

## Outputs

| Output | Description |
|--------|-------------|
| `output-file` | Path to the generated OpenAPI JSON file |
| `html-file` | Path to the generated HTML documentation viewer |
| `file-size` | Size of the generated file |

## Complete Workflow Example

Here's a complete workflow that converts an EDMX file and then deploys the documentation:

```yaml
name: Generate API Documentation

on:
  push:
    branches: [ main ]
    paths: [ '**/api.xml' ]  # Triggers when any api.xml file changes
  workflow_dispatch:        # Allows manual triggering
    inputs:
      input_path:
        description: 'Path to EDMX file'
        default: 'docs/api.xml'
      output-path:
        description: 'Path where the output OpenAPI JSON file should be saved relative to repository root'
        default: 'docs/api.json'
      api_name:
        description: 'API name'
        default: 'BusinessCentral'

jobs:
  convert-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      
    - name: Convert EDMX to OpenAPI
      id: convert
      uses: attieretief/bc-edmx-to-openapi@v1
      with:
        input-path: ${{ github.event.inputs.input_path || 'docs/api.xml' }}
        output-path: ${{ github.event.inputs.output_path || 'docs/api.json }}
        api-name: ${{ github.event.inputs.api_name || 'BusinessCentral' }}
    
    - name: Display conversion results
      run: |
        echo "Generated OpenAPI: ${{ steps.convert.outputs.output-file }}"
        echo "Generated HTML: ${{ steps.convert.outputs.html-file }}"
        echo "File size: ${{ steps.convert.outputs.file-size }}"
    
    - name: Deploy to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./docs
```

## What Gets Enhanced?

The action takes your EDMX file and:

1. **Converts to OpenAPI 3.1.1**: Uses the industry-standard `odata-openapi3` tool
2. **Adds Business Central Servers**: Configures both sandbox and production Business Central endpoints
3. **Security Schemes**: Includes OAuth2 configurations for Business Central authentication
4. **Custom Documentation**: Enhances info section with your custom title and description
5. **URL Configuration**: Uses your API name and version for proper URL generation
6. **Clean Structure**: Removes unused schema variants and optimizes the output
7. **🆕 Interactive HTML Viewer**: Creates an `index.html` file with multiple documentation viewers

### Interactive HTML Documentation

The action automatically generates an `index.html` file in the same directory as your OpenAPI JSON file. This HTML viewer includes:

- **📖 Scalar Integration**: Interactive API testing with a beautiful, modern interface

Simply open the `index.html` file in any browser to explore your API documentation interactively!

## Local Development

You can also use this converter locally without GitHub Actions:

```bash
# Make the script executable
chmod +x convert.sh

# Basic usage
./convert.sh docs/api.xml docs/api-openapi.json

# With custom options
./convert.sh docs/api.xml docs/api-openapi.json \
  --title "My Business Central API" \
  --description "Custom API documentation" \
  --api-name "MyApp" \
  --api-version "v2.0"

# Skip HTML generation
./convert.sh docs/api.xml docs/api-openapi.json --no-html
```

The script automatically:
- Detects if it's running locally vs in GitHub Actions
- Installs dependencies if needed (local mode)
- Generates both JSON and HTML files
- Provides appropriate outputs for each environment

### Local Requirements

For local usage, you need:
- Node.js and npm (for `odata-openapi3`)
- Python 3
- The script will auto-install `odata-openapi` if missing

### GitHub Actions Requirements

The action runs in a Docker container with all dependencies pre-installed:
- Node.js 18 (for `odata-openapi3`)
- Python 3 (for enhancement processing)
- No setup required in your repository!

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/attieretief/bc-edmx-to-openapi/issues) page
2. Create a new issue with details about your use case
3. Include your EDMX file structure and expected output

---

**Made with ❤️ for the Business Central community**