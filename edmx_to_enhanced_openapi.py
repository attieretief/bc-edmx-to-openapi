#!/usr/bin/env python3
"""
Business Central OData EDMX to OpenAPI Converter

This script uses the odata-openapi3 tool to convert EDMX files to OpenAPI 3.1.1 format,
then enhances the result with custom info, security, and server configurations specific 
to Business Central APIs.

Usage:
    python edmx_to_enhanced_openapi.py input.xml output.json [--title "API Title"] [--description "API Description"]

Requirements:
    npm install -g odata-openapi
"""

import json
import argparse
import sys
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Set


class EdmxToEnhancedOpenApiConverter:
    """Converts EDMX files to enhanced OpenAPI 3.1.1 JSON format."""
    
    def __init__(self):
        self.edmx_capabilities = {}  # Store EntitySet capability restrictions
        self.entity_type_capabilities = {}  # Store EntityType capability restrictions
        
    def convert(self, edmx_file: str, output_file: str, title: str = None, description: str = None, 
                api_name: str = None, api_version: str = None, tenant_placeholder: str = None) -> None:
        """Convert EDMX file to enhanced OpenAPI JSON."""
        print(f"Converting {edmx_file} to {output_file}")
        
        # Step 0: Parse EDMX file for capability annotations
        self._parse_edmx_capabilities(edmx_file)
        
        # Step 1: Use odata-openapi3 to generate base OpenAPI file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Run odata-openapi3 tool
            result = subprocess.run([
                'npx', 'odata-openapi3', 
                '--pretty', 
                '--openapi-version', '3.1.0',
                '--target', temp_path,
                edmx_file
            ], capture_output=True, text=True, check=True)
            
            print(f"Base OpenAPI generated at {temp_path}")
            
            # Step 2: Load and enhance the generated OpenAPI
            with open(temp_path, 'r', encoding='utf-8') as f:
                openapi_spec = json.load(f)
            
            # Step 3: Apply enhancements
            self._enhance_openapi_spec(openapi_spec, title, description, api_name, api_version, tenant_placeholder)
            
            # Step 4: Write enhanced output file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(openapi_spec, f, indent=4, ensure_ascii=False)
            
            print(f"Enhanced OpenAPI saved to {output_file}")
            
        except subprocess.CalledProcessError as e:
            print(f"Error running odata-openapi3: {e}")
            print(f"stderr: {e.stderr}")
            sys.exit(1)
        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)
    
    def _enhance_openapi_spec(self, spec: Dict[str, Any], title: str = None, description: str = None,
                              api_name: str = None, api_version: str = None, tenant_placeholder: str = None) -> None:
        """Enhance the OpenAPI specification with custom sections."""
        
        # Update OpenAPI version to 3.1.1
        spec['openapi'] = '3.1.1'
        
        # Enhance info section
        spec['info'] = self._build_enhanced_info_section(title, description, api_name)
        
        # Replace servers section
        spec['servers'] = self._build_enhanced_servers_section(api_name, api_version)
        
        # Add security section
        spec['security'] = self._build_security_section()
        
        # Enhance components section with security schemes
        if 'components' not in spec:
            spec['components'] = {}
        
        spec['components']['securitySchemes'] = self._build_security_schemes(tenant_placeholder)
        
        # Add company parameter to components and update paths to use $ref
        self._add_company_parameter(spec)
        
        # Remove unnecessary navigation paths to reduce verbosity
        self._remove_navigation_paths(spec)
        
        # Remove system audit fields from create/update schemas
        self._remove_system_fields_from_mutation_schemas(spec)
        
        # Remove HTTP methods that violate EDMX capability annotations
        self._enforce_edmx_capabilities(spec)
        
        # Remove unused create/update schema variants
        self._remove_unused_schema_variants(spec)
        
        print("Applied enhancements: info, servers, security, securitySchemes, company parameter optimization, navigation path cleanup, system audit field removal, EDMX capability enforcement, and unused schema cleanup")
    
    def _build_enhanced_info_section(self, title: str = None, description: str = None, api_name: str = None) -> Dict[str, Any]:
        """Build the enhanced info section of the OpenAPI spec."""
        # Use provided api_name
        default_api_name = api_name
        default_title = f"{default_api_name} API"
        
        default_description = f"""# Getting Started

## Introduction

Welcome to the Documentation and API Reference for the {default_api_name} API.

The {default_api_name} API exposes {default_api_name} entities within a Business Central tenant, where {default_api_name} and the {default_api_name} API app have been installed.

It is therefore important to understand the workings of the [Business Central API](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/devenv-develop-connect-apps), since the {default_api_name} API is a subset of the [Business Central API](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/devenv-develop-connect-apps).

## Built-in System Endpoints

In addition to the {default_api_name}-specific business entities, this API includes several built-in Business Central system endpoints that provide essential metadata and administrative functionality:

### Core System Endpoints

- **`/companies`** - Lists all companies within the Business Central tenant. Every business entity operation requires a company context, making this endpoint essential for discovering available companies before accessing business data.  
  📖 [Learn more about companies in Business Central API](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/devenv-connect-apps-tips#get)

- **`/entityDefinitions`** - Provides metadata about all available API entities, including their properties, relationships, and capabilities. Essential for API discovery and dynamic client applications.  
  📖 [Learn more about API metadata and discovery](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/webservices/api-endpoint-structure)

- **`/$batch`** - Enables transactional batch operations where multiple API calls can be grouped together and executed atomically. If any operation in the batch fails, all changes are rolled back.  
  📖 [Learn more about OData transactional $batch requests](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/devenv-connect-apps-tips#batch)

### Event and Subscription Management

- **`/externalbusinesseventdefinitions`** - Lists available business event definitions that external systems can subscribe to for real-time notifications when specific business processes occur in Business Central.  
  📖 [Learn more about Business Central integration overview](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/integration-overview)

- **`/externaleventsubscriptions`** - Manages subscriptions to business events, allowing external systems to register webhooks or other notification mechanisms.  
  📖 [Learn more about web services and integrations](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/webservices/web-services)

- **`/subscriptions`** - General subscription management endpoint for various Business Central notification services.  
  📖 [Learn more about Business Central web services](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/webservices/web-services)

### API Discovery and Routing

- **`/apicategoryroutes`** - Provides information about available API routes and categories, helping client applications discover what APIs are available in the current Business Central environment.  
  📖 [Learn more about API endpoint structure](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/webservices/api-endpoint-structure)

These system endpoints follow the same authentication and security model as the business entity endpoints but typically don't require a company parameter since they operate at the tenant level.

## Authentication

A point-to-point connection between Dynamics 365 Business Central and a third-party solution or service is typically created using standard REST API to interchange data. Any coding language capable of calling REST APIs can be used to develop your solution.

Business Central is multi-tenanted, and connecting to the Business Central API instance where the {default_api_name} API is installed, uses the OAuth 2.0 client credentials flow.

Authentication therefore involves first obtaining a token from the Microsoft Identity Platform. An administrator of the tenant you are trying to connect to, will have to create an Entra App registration for your use, and grant this Entra App the required permissions in Business Central and {default_api_name}.

For more information, see [Microsoft Identity Platform and the OAuth 2.0 Client Credentials Flow](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-client-creds-grant-flow).

1. [How to get the tokens needed to call the API using a shared secret](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-client-creds-grant-flow#first-case-access-token-request-with-a-shared-secret)

1. [Using the token in subsequent API requests](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-client-creds-grant-flow#use-a-token)

## Live Testing

This API documentation is rendered using Scalar.com, which provides interactive testing capabilities directly within the documentation interface. To test the API endpoints live:

1. **Environment Name**: Specify the appropriate environment name in the EnvironmentName input field. The default is set to "Production", but you can change this to match your Business Central environment (e.g., "Sandbox", "UAT", etc.).

1. **Authentication Setup**: In the authentication section of the Scalar documentation:
   - Replace `{{tenant_id}}` in the token URL with the actual tenant ID provided by your client
   - Enter your **Client ID** in the appropriate field
   - Enter your **Client Secret** in the appropriate field
   - Select all Scopes from the **Scopes** dropdown
   - Click **Authorize**

1. **Testing**: Once configured, you can test any API endpoint directly from the documentation:
   - Click on any endpoint
   - Fill in the required parameters
   - Click **Test Request**
   - View the live response from your Business Central environment

This interactive testing feature allows you to explore the API functionality and validate your integration before implementing it in your application.

## Useful Links

[Tips for working with APIs](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/devenv-connect-apps-tips)

[Using filters with API calls](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/devenv-connect-apps-filtering)

[Troubleshooting API calls](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/webservices/dynamics-error-codes)

[API Performance](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/webservices/web-service-performance)

[Working with API Limits](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/api-reference/v2.0/dynamics-rate-limits)"""
        
        return {
            'title': title or default_title,
            'description': description or default_description
        }
    
    def _build_enhanced_servers_section(self, api_name: str = None, api_version: str = None) -> List[Dict[str, Any]]:
        """Build the enhanced servers section of the OpenAPI spec."""
        # Use provided values
        default_api_name = (api_name or "api").lower()
        default_api_version = api_version or "v2.0"
        
        return [
            {
                'url': f'https://api.businesscentral.dynamics.com/v2.0/{{EnvironmentName}}/api/linc/{default_api_name}/{default_api_version}',
                'variables': {
                    'EnvironmentName': {
                        'default': 'Production',
                        'description': 'The Business Central environment name'
                    }
                }
            }
        ]
    
    def _build_security_section(self) -> List[Dict[str, List]]:
        """Build the security section."""
        return [
            {
                'oauth2_client_credentials': []
            }
        ]
    
    def _build_security_schemes(self, tenant_placeholder: str = None) -> Dict[str, Any]:
        """Build the security schemes section."""
        # Use provided tenant placeholder or default
        default_tenant_placeholder = tenant_placeholder or "{tenant_Id}"
        
        return {
            'oauth2_client_credentials': {
                'type': 'oauth2',
                'description': 'OAuth2 Client Credentials Flow for Business Central API',
                'flows': {
                    'clientCredentials': {
                        'tokenUrl': f'https://login.microsoftonline.com/{default_tenant_placeholder}/oauth2/v2.0/token',
                        'scopes': {
                            'https://api.businesscentral.dynamics.com/.default': 'Default Scope for Business Central API'
                        }
                    }
                }
            }
        }

    def _add_company_parameter(self, spec: Dict[str, Any]) -> None:
        """Add company parameter to components."""
        
        # Add company parameter to components/parameters
        if 'parameters' not in spec['components']:
            spec['components']['parameters'] = {}
            
        spec['components']['parameters']['company'] = {
            'in': 'query',
            'name': 'company',
            "description": "The company name to which the request is directed.",
            'required': True,
            'schema': {
                'type': 'string',
                "maxLength": 100
            }
        }
        
        # Add company parameter to paths as $ref
        # But don't add to paths starting with: $batch, apicategoryroutes, companies, entitydefinitions, externalbusinesseventdefinitions, externaleventsubscriptions, subscriptions

        if 'paths' not in spec:
            return

        new_paths = {}
        for path in spec['paths'].items():
            # print first element of path tuple
            path_name, values = path
            if not any(path_name.startswith(prefix) for prefix in [
                '/$batch', '/apicategoryroutes', '/companies', '/entitydefinitions',
                '/externalbusinesseventdefinitions', '/externaleventsubscriptions',
                '/subscriptions', '/entityDefinitions'
            ]):
                if 'parameters' not in values:
                    values['parameters'] = []
                values['parameters'].append({
                    '$ref': '#/components/parameters/company'
                })
            new_paths.update({path_name: values})

        spec['paths'] = dict(new_paths)
        print("Added company parameter to components and paths.")

    def _remove_navigation_paths(self, spec: Dict[str, Any]) -> None:
        """Remove unnecessary navigation paths to reduce API documentation verbosity."""
        if 'paths' not in spec:
            return
        
        paths_to_remove = []
        company_paths_checked = 0
        all_paths_count = len(spec['paths'])
        system_paths_skipped = 0
        
        for path_name in spec['paths']:
            # Keep basic system endpoints only (not company entities)
            # Only skip exact matches and basic parameterized versions
            is_system_endpoint = False
            
            # Check for exact system endpoint matches
            system_prefixes = [
                '/$batch', '/apicategoryroutes', '/entitydefinitions',
                '/externalbusinesseventdefinitions', '/externaleventsubscriptions',
                '/subscriptions', '/entityDefinitions'
            ]
            
            for prefix in system_prefixes:
                if path_name == prefix or path_name.startswith(prefix + '('):
                    is_system_endpoint = True
                    break
            
            # Special case: only skip the basic companies endpoints, not company entity paths
            if path_name == '/companies' or path_name == '/companies({id})':
                is_system_endpoint = True
            
            if is_system_endpoint:
                system_paths_skipped += 1
                continue
            
            # For company paths, only keep first level navigation
            # Pattern: /companies({id})/entityName or /companies({id})/entityName(...)
            if path_name.startswith('/companies({id})/'):
                company_paths_checked += 1
                # Remove the prefix and analyze the remainder
                remainder = path_name[17:]  # Length of '/companies({id})/'
                path_levels = remainder.split('/')
                path_levels = [level for level in path_levels if level]  # Remove empty strings
                
                # Only keep paths with 1 level (entity) or 2 levels (entity + id)
                # Remove paths with 3+ levels (navigation properties)
                if len(path_levels) > 2:
                    paths_to_remove.append(path_name)
                    continue
                elif len(path_levels) == 2:
                    # Check if second level is an ID (contains parentheses) or navigation property
                    second_level = path_levels[1]
                    if not (second_level.startswith('(') and second_level.endswith(')')):
                        # This is a navigation property, not an ID
                        paths_to_remove.append(path_name)
                        continue
            
            # Remove non-company paths that have navigation properties
            # Pattern: /entityName/navigationProperty or /entityName(...)/navigationProperty
            elif not path_name.startswith('/companies'):
                path_parts = path_name.strip('/').split('/')
                
                # Remove paths with more than 2 segments (entity and optional ID)
                # Keep: /entityName and /entityName(...)
                # Remove: /entityName/navigationProperty, /entityName(...)/navigationProperty, etc.
                if len(path_parts) > 2:
                    paths_to_remove.append(path_name)
                elif len(path_parts) == 2:
                    # Keep if second part looks like an ID: entityName(...)
                    # Remove if second part is a navigation property name
                    second_part = path_parts[1]
                    if not (second_part.startswith('(') and second_part.endswith(')')):
                        paths_to_remove.append(path_name)
        
        # Remove the identified paths
        removed_count = 0
        for path_name in paths_to_remove:
            if path_name in spec['paths']:
                del spec['paths'][path_name]
                removed_count += 1
        
        print(f"Checked {company_paths_checked} company paths, skipped {system_paths_skipped} system paths out of {all_paths_count} total paths")
        if removed_count > 0:
            print(f"Removed {removed_count} navigation property paths to reduce API documentation verbosity")
        else:
            print("No navigation property paths found to remove")

    def _remove_system_fields_from_mutation_schemas(self, spec: Dict[str, Any]) -> None:
        """Remove system audit fields from create and update schemas."""
        if 'components' not in spec or 'schemas' not in spec['components']:
            return
        
        # System audit fields that should not be in create/update schemas
        system_fields = {
            'systemCreatedAt',
            'systemCreatedBy', 
            'systemModifiedAt',
            'systemModifiedBy'
        }
        
        schemas_modified = 0
        fields_removed = 0
        
        for schema_name, schema_def in spec['components']['schemas'].items():
            # Only process -create and -update schemas
            if not (schema_name.endswith('-create') or schema_name.endswith('-update')):
                continue
                
            if not isinstance(schema_def, dict) or 'properties' not in schema_def:
                continue
                
            # Check if schema has any system fields
            properties = schema_def['properties']
            fields_to_remove = []
            
            for field_name in properties:
                if field_name in system_fields:
                    fields_to_remove.append(field_name)
            
            # Remove system fields from this schema
            if fields_to_remove:
                schemas_modified += 1
                for field_name in fields_to_remove:
                    del properties[field_name]
                    fields_removed += 1
        
        if schemas_modified > 0:
            print(f"Removed {fields_removed} system audit fields from {schemas_modified} create/update schemas")
        else:
            print("No system audit fields found in create/update schemas")

    def _parse_edmx_capabilities(self, edmx_file: str) -> None:
        """Parse EDMX file to extract EntitySet capability annotations."""
        try:
            tree = ET.parse(edmx_file)
            root = tree.getroot()
            
            # Define namespaces used in EDMX files
            namespaces = {
                'edmx': 'http://docs.oasis-open.org/odata/ns/edmx',
                'edm': 'http://docs.oasis-open.org/odata/ns/edm'
            }
            
            # Find all EntitySets and create mapping to EntityTypes
            entity_sets = root.findall('.//edm:EntitySet', namespaces)
            entity_set_to_type = {}
            
            for entity_set in entity_sets:
                entity_set_name = entity_set.get('Name')
                entity_type = entity_set.get('EntityType')
                if not entity_set_name or not entity_type:
                    continue
                
                # Extract just the type name (remove namespace prefix)
                entity_type_name = entity_type.split('.')[-1] if '.' in entity_type else entity_type
                entity_set_to_type[entity_set_name] = entity_type_name
                
                capabilities = {
                    'insertable': True,  # Default to true per OData spec
                    'updatable': True,   # Default to true per OData spec
                    'deletable': True    # Default to true per OData spec
                }
                
                # Look for capability annotations
                annotations = entity_set.findall('.//edm:Annotation', namespaces)
                
                for annotation in annotations:
                    term = annotation.get('Term', '')
                    
                    if 'InsertRestrictions' in term:
                        # Find Insertable property
                        insertable_prop = annotation.find('.//edm:PropertyValue[@Property="Insertable"]', namespaces)
                        if insertable_prop is not None:
                            bool_value = insertable_prop.get('Bool', 'true').lower()
                            capabilities['insertable'] = bool_value == 'true'
                    
                    elif 'UpdateRestrictions' in term:
                        # Find Updatable property
                        updatable_prop = annotation.find('.//edm:PropertyValue[@Property="Updatable"]', namespaces)
                        if updatable_prop is not None:
                            bool_value = updatable_prop.get('Bool', 'true').lower()
                            capabilities['updatable'] = bool_value == 'true'
                    
                    elif 'DeleteRestrictions' in term:
                        # Find Deletable property
                        deletable_prop = annotation.find('.//edm:PropertyValue[@Property="Deletable"]', namespaces)
                        if deletable_prop is not None:
                            bool_value = deletable_prop.get('Bool', 'true').lower()
                            capabilities['deletable'] = bool_value == 'true'
                
                # Store capabilities for both EntitySet name and EntityType name
                self.edmx_capabilities[entity_set_name] = capabilities
                self.entity_type_capabilities[entity_type_name] = capabilities
                
                # Debug output for entities with restrictions
                if not all(capabilities.values()):
                    restricted_ops = [op for op, allowed in capabilities.items() if not allowed]
                    print(f"EntitySet '{entity_set_name}' (EntityType '{entity_type_name}') has restrictions: {', '.join(restricted_ops)} not allowed")
            
            print(f"Parsed capability annotations for {len(self.edmx_capabilities)} EntitySets")
            
        except Exception as e:
            print(f"Warning: Could not parse EDMX capabilities: {e}")
            # Continue without capability enforcement if parsing fails

    def _enforce_edmx_capabilities(self, spec: Dict[str, Any]) -> None:
        """Remove HTTP methods from paths that violate EDMX capability annotations."""
        if 'paths' not in spec or not self.edmx_capabilities:
            return
        
        methods_removed = 0
        
        for path, path_obj in spec['paths'].items():
            # Check for direct EntitySet paths
            entity_set_name = self._extract_entity_set_from_path(path)
            capabilities = None
            
            if entity_set_name and entity_set_name in self.edmx_capabilities:
                capabilities = self.edmx_capabilities[entity_set_name]
            else:
                # Check for navigational property paths by examining schema references
                entity_type_name = self._extract_entity_type_from_path_methods(path_obj, spec)
                if entity_type_name and entity_type_name in self.entity_type_capabilities:
                    capabilities = self.entity_type_capabilities[entity_type_name]
                else:
                    # Direct path-based detection for restricted entities
                    # Look for paths that end with these restricted entity types
                    path_segments = path.rstrip('/').split('/')
                    if path_segments:
                        last_segment = path_segments[-1]
                        # Handle parameterized segments by extracting the base entity name
                        if '(' in last_segment:
                            last_segment = last_segment.split('(')[0]
                        
                        # Check if the last segment matches any restricted entity type
                        if last_segment in self.entity_type_capabilities:
                            capabilities = self.entity_type_capabilities[last_segment]
            
            # Override capabilities for any restricted entities found in the path
            # This ensures we catch complex navigational property paths
            # Apply this regardless of whether capabilities were already found
            for entity_type_name, entity_capabilities in self.entity_type_capabilities.items():
                # Only apply override if the entity actually has restrictions
                if (f'/{entity_type_name}' in path and 
                    not all(entity_capabilities.values())):  # Has at least one restriction
                    capabilities = entity_capabilities
                    break
            
            if capabilities:
                # Remove POST if insertable is false
                if not capabilities['insertable'] and 'post' in path_obj:
                    del path_obj['post']
                    methods_removed += 1
                    print(f"Removed POST from {path} (insertable=false)")
                
                # Remove PATCH if updatable is false
                if not capabilities['updatable'] and 'patch' in path_obj:
                    del path_obj['patch']
                    methods_removed += 1
                    print(f"Removed PATCH from {path} (updatable=false)")
                
                # Remove DELETE if deletable is false
                if not capabilities['deletable'] and 'delete' in path_obj:
                    del path_obj['delete']
                    methods_removed += 1
                    print(f"Removed DELETE from {path} (deletable=false)")

        
        if methods_removed > 0:
            print(f"Enforced EDMX capabilities: removed {methods_removed} HTTP methods that violate EntitySet annotations")
        else:
            print("No HTTP methods needed to be removed for EDMX capability compliance")

    def _extract_entity_set_from_path(self, path: str) -> str:
        """Extract EntitySet name from an OpenAPI path."""
        # Remove leading slash and parameters in curly braces
        path_clean = path.lstrip('/')
        
        # Handle company-scoped paths: /companies({id})/entitySet
        if path_clean.startswith('companies('):
            # Find the part after the company parameter
            parts = path_clean.split('/')
            if len(parts) >= 2:
                # Second part should be the entity set
                entity_part = parts[1]
                # Remove any parameters like (key=value)
                if '(' in entity_part:
                    entity_part = entity_part.split('(')[0]
                return entity_part
        else:
            # Handle root-level paths: /entitySet
            parts = path_clean.split('/')
            if parts:
                entity_part = parts[0]
                # Remove any parameters like (key=value)
                if '(' in entity_part:
                    entity_part = entity_part.split('(')[0]
                return entity_part
        
        return None

    def _extract_entity_type_from_path_methods(self, path_obj: Dict[str, Any], spec: Dict[str, Any]) -> str:
        """Extract EntityType name from path methods by examining schema references."""
        # Look for schema references in GET, PATCH methods
        for method_name in ['get', 'patch']:
            if method_name not in path_obj:
                continue
                
            method_obj = path_obj[method_name]
            
            # Check GET response schema
            if method_name == 'get' and 'responses' in method_obj:
                schema_ref = self._extract_schema_ref_from_responses(method_obj['responses'])
                if schema_ref:
                    entity_type = self._schema_ref_to_entity_type(schema_ref)
                    if entity_type:
                        return entity_type
            
            # Check PATCH request body schema
            if method_name == 'patch' and 'requestBody' in method_obj:
                schema_ref = self._extract_schema_ref_from_request_body(method_obj['requestBody'])
                if schema_ref:
                    # PATCH typically uses -update schemas, extract base type
                    entity_type = self._schema_ref_to_entity_type(schema_ref)
                    if entity_type:
                        return entity_type
        
        return None

    def _extract_schema_ref_from_responses(self, responses: Dict[str, Any]) -> str:
        """Extract $ref from response schema."""
        if '200' in responses and 'content' in responses['200']:
            content = responses['200']['content']
            if 'application/json' in content and 'schema' in content['application/json']:
                schema = content['application/json']['schema']
                if '$ref' in schema:
                    return schema['$ref']
        return None

    def _extract_schema_ref_from_request_body(self, request_body: Dict[str, Any]) -> str:
        """Extract $ref from request body schema."""
        if 'content' in request_body and 'application/json' in request_body['content']:
            content = request_body['content']['application/json']
            if 'schema' in content and '$ref' in content['schema']:
                return content['schema']['$ref']
        return None

    def _schema_ref_to_entity_type(self, schema_ref: str) -> str:
        """Convert schema reference to EntityType name."""
        if not schema_ref.startswith('#/components/schemas/'):
            return None
        
        schema_name = schema_ref.replace('#/components/schemas/', '')
        
        # Handle Microsoft.NAV.entityType format
        if schema_name.startswith('Microsoft.NAV.'):
            entity_type = schema_name.replace('Microsoft.NAV.', '')
            
            # Remove -create, -update suffixes
            if entity_type.endswith('-create') or entity_type.endswith('-update'):
                entity_type = entity_type.rsplit('-', 1)[0]
            
            return entity_type
        
        return None

    def _remove_unused_schema_variants(self, spec: Dict[str, Any]) -> None:
        """Remove unused 'for create' and 'for update' schema variants that are not referenced by POST/PATCH methods."""
        
        def extract_schema_refs(obj):
            """Recursively extract all $ref schema references from an object."""
            refs = set()
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == '$ref' and isinstance(value, str) and value.startswith('#/components/schemas/'):
                        refs.add(value.replace('#/components/schemas/', ''))
                    else:
                        refs.update(extract_schema_refs(value))
            elif isinstance(obj, list):
                for item in obj:
                    refs.update(extract_schema_refs(item))
            return refs
        
        if 'paths' not in spec or 'components' not in spec or 'schemas' not in spec['components']:
            return
        
        # Find all schemas referenced by POST and PATCH methods
        schemas_used_by_post = set()
        schemas_used_by_patch = set()
        
        for path, path_obj in spec['paths'].items():
            if 'post' in path_obj:
                refs = extract_schema_refs(path_obj['post'])
                schemas_used_by_post.update(refs)
            
            if 'patch' in path_obj:
                refs = extract_schema_refs(path_obj['patch'])
                schemas_used_by_patch.update(refs)
        
        # Get all schemas that end with -create or -update
        all_schemas = list(spec['components']['schemas'].keys())
        create_schemas = [s for s in all_schemas if s.endswith('-create')]
        update_schemas = [s for s in all_schemas if s.endswith('-update')]
        
        # Find unused create/update schemas
        unused_create_schemas = [s for s in create_schemas if s not in schemas_used_by_post]
        unused_update_schemas = [s for s in update_schemas if s not in schemas_used_by_patch]
        
        # Also remove schemas for entities that don't allow the operation based on EDMX capabilities
        capability_based_removals = []
        
        for schema in create_schemas:
            # Extract base entity name
            base_name = schema.replace('-create', '')
            if base_name.startswith('Microsoft.NAV.'):
                base_name = base_name[len('Microsoft.NAV.'):]
            
            # Check if entity doesn't allow insertable
            if base_name in self.entity_type_capabilities:
                capabilities = self.entity_type_capabilities[base_name]
                if not capabilities.get('insertable', True):
                    capability_based_removals.append(schema)
        
        for schema in update_schemas:
            # Extract base entity name  
            base_name = schema.replace('-update', '')
            if base_name.startswith('Microsoft.NAV.'):
                base_name = base_name[len('Microsoft.NAV.'):]
            
            # Check if entity doesn't allow updatable
            if base_name in self.entity_type_capabilities:
                capabilities = self.entity_type_capabilities[base_name]
                if not capabilities.get('updatable', True):
                    capability_based_removals.append(schema)
        
        # Combine all schemas to remove
        all_schemas_to_remove = set(unused_create_schemas + unused_update_schemas + capability_based_removals)
        
        # Force remove schemas for entities that have capability restrictions
        force_remove_schemas = []
        for schema_name in spec['components']['schemas'].keys():
            # Check if this is a create/update schema for a restricted entity
            if schema_name.startswith('Microsoft.NAV.') and (schema_name.endswith('-create') or schema_name.endswith('-update')):
                # Extract the entity type name
                if schema_name.endswith('-create'):
                    entity_type = schema_name[len('Microsoft.NAV.'):-len('-create')]
                else:  # ends with '-update'
                    entity_type = schema_name[len('Microsoft.NAV.'):-len('-update')]
                
                # Check if this entity has capability restrictions
                if entity_type in self.entity_type_capabilities:
                    capabilities = self.entity_type_capabilities[entity_type]
                    # Remove create schemas for non-insertable entities
                    if schema_name.endswith('-create') and not capabilities.get('insertable', True):
                        force_remove_schemas.append(schema_name)
                    # Remove update schemas for non-updatable entities
                    elif schema_name.endswith('-update') and not capabilities.get('updatable', True):
                        force_remove_schemas.append(schema_name)
        
        # Combine all schemas to remove (including force removals)
        all_schemas_to_remove = set(list(all_schemas_to_remove) + force_remove_schemas)
        
        # Remove schemas
        removed_count = 0
        
        for schema in all_schemas_to_remove:
            if schema in spec['components']['schemas']:
                del spec['components']['schemas'][schema]
                removed_count += 1
        
        if removed_count > 0:
            print(f"Removed {removed_count} unused schema variants ({len(unused_create_schemas)} create, {len(unused_update_schemas)} update)")
        else:
            print("No unused schema variants found to remove")

def main():
    """Main function to handle command line arguments and execute conversion."""
    parser = argparse.ArgumentParser(
        description='Convert EDMX files to enhanced OpenAPI 3.1.1 JSON format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python edmx_to_enhanced_openapi.py api.xml api.json
  python edmx_to_enhanced_openapi.py api.xml api.json --title "My API" --description "Custom API description"
  python edmx_to_enhanced_openapi.py api.xml api.json --api-name "MyApp" --api-version "v1.0"
  python edmx_to_enhanced_openapi.py api.xml api.json --tenant-placeholder "{{tenant_id}}"

Requirements:
  - npm install -g odata-openapi

This script first uses the odata-openapi3 tool to convert the EDMX to a base OpenAPI file,
then enhances it with Business Central specific configurations.
        """
    )
    
    parser.add_argument('input_file', help='Input EDMX file path')
    parser.add_argument('output_file', help='Output OpenAPI JSON file path')
    parser.add_argument('--title', help='API title (optional)')
    parser.add_argument('--description', help='API description (optional)')
    parser.add_argument('--api-name', help='API name for URLs and documentation (e.g., "produceLinc", "myApp")')
    parser.add_argument('--api-version', help='API version for URLs (e.g., "v1.0", "v2.0")')
    parser.add_argument('--tenant-placeholder', help='Tenant ID placeholder for OAuth URLs (e.g., "{tenant_id}", "{{tenant_id}}")')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not Path(args.input_file).exists():
        print(f"Error: Input file '{args.input_file}' not found.")
        sys.exit(1)
    
    # Check if odata-openapi3 is available
    try:
        subprocess.run(['npx', 'odata-openapi3', '--help'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: odata-openapi3 tool not found. Please install with: npm install -g odata-openapi")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        converter = EdmxToEnhancedOpenApiConverter()
        converter.convert(
            args.input_file, 
            args.output_file, 
            args.title, 
            args.description,
            args.api_name,
            args.api_version,
            args.tenant_placeholder
        )
    except Exception as e:
        print(f"Error during conversion: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()