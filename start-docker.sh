#!/bin/bash

# Check if setup has been run
if [ ! -f "docker-compose.override.yml" ]; then
  echo "Please run ./setup.sh first to configure AWS credentials path"
  exit 1
fi

# Build and start the Docker container for AWS Storage MCP server
echo "Building and starting AWS Storage MCP server in Docker..."
docker compose up --build -d

echo ""
echo "AWS Storage MCP server is now running at http://localhost:8080"
echo "To view logs: docker compose logs -f"
echo "To stop the server: docker compose down"
echo ""
echo "To register with Amazon Q CLI:"
echo "q mcp add --name aws-storage --command \"docker compose -f $(pwd)/docker-compose.yml up\" --scope global"
