#!/bin/bash

echo "Setting up AWS Storage MCP server..."

# Detect OS and set AWS credentials path
if grep -q Microsoft /proc/version; then
  # WSL detected
  WIN_USERNAME=$(cmd.exe /c echo %USERNAME% 2>/dev/null | tr -d '\r')
  DEFAULT_AWS_PATH="/mnt/c/Users/${WIN_USERNAME}/.aws"
  echo "Windows WSL detected. Default AWS credentials path: ${DEFAULT_AWS_PATH}"
else
  # Linux/Mac
  DEFAULT_AWS_PATH="$HOME/.aws"
  echo "Linux/Mac detected. Default AWS credentials path: ${DEFAULT_AWS_PATH}"
fi

# Ask user to confirm or provide alternative path
read -p "AWS credentials path [${DEFAULT_AWS_PATH}]: " AWS_CREDENTIALS_PATH
AWS_CREDENTIALS_PATH=${AWS_CREDENTIALS_PATH:-$DEFAULT_AWS_PATH}

# Create docker-compose override file
cat > docker-compose.override.yml << EOF
services:
  aws-storage-mcp:
    volumes:
      - ${AWS_CREDENTIALS_PATH}:/root/.aws:ro
EOF

echo "Configuration complete. AWS credentials will be mounted from: ${AWS_CREDENTIALS_PATH}"
echo "You can now start the server with: ./start-docker.sh"
