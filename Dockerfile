FROM node:18-alpine

# Install Python and required system dependencies
RUN apk add --no-cache python3 py3-pip bash

# Install odata-openapi globally
RUN npm install -g odata-openapi

# Set working directory
WORKDIR /action

# Copy the converter scripts
COPY edmx_to_enhanced_openapi.py /action/
COPY convert.sh /action/

# Make script executable
RUN chmod +x /action/convert.sh

# Set the entrypoint
ENTRYPOINT ["/action/convert.sh"]