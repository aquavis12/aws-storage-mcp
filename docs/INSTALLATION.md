# Installation Guide

This guide provides detailed instructions for installing and configuring the AWS Storage MCP Server.

## Prerequisites

Before you begin, ensure you have the following installed:

### Docker and Docker Compose

#### For Ubuntu/Debian:
```bash
# Update package index
sudo apt update

# Install prerequisites
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# Add Docker repository
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add your user to the docker group to run Docker without sudo
sudo usermod -aG docker $USER
```

#### For macOS:
1. Download and install Docker Desktop from [Docker's website](https://www.docker.com/products/docker-desktop)
2. Start Docker Desktop

#### For Windows:
1. Download and install Docker Desktop from [Docker's website](https://www.docker.com/products/docker-desktop)
2. Enable WSL 2 integration in Docker Desktop settings
3. Start Docker Desktop

### AWS CLI

#### For Ubuntu/Debian:
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

#### For macOS:
```bash
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
```

#### For Windows:
```powershell
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi
```

### Amazon Q CLI

Follow the installation instructions for Amazon Q CLI from the [official documentation](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/command-line-installation.html).

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/aquavis12/aws-storage-mcp.git
cd aws-storage-mcp
```

### 2. Configure AWS Credentials

If you haven't already configured AWS credentials, run:

```bash
aws configure
```

You'll be prompted to enter:
- AWS Access Key ID
- AWS Secret Access Key
- Default region name (e.g., us-east-1)
- Default output format (e.g., json)

### 3. Run the Setup Script

```bash
./setup.sh
```

This script will:
- Detect your environment (Windows WSL, Linux, or Mac)
- Configure the correct path to your AWS credentials
- Create a Docker Compose override file with your specific configuration

### 4. Start the MCP Server

```bash
./start-docker.sh
```

This will build and start a Docker container running the MCP server on port 8080.

### 5. Register with Amazon Q CLI

```bash
q mcp add --name aws-storage --command "docker compose -f $(pwd)/docker-compose.yml up" --scope global
```

### 6. Verify Registration

```bash
q mcp list
```

You should see `aws-storage` listed in the output.

## Troubleshooting

### Docker Issues

If you encounter Docker-related issues:

1. Ensure Docker is running:
   ```bash
   docker info
   ```

2. Check if the container is running:
   ```bash
   docker ps | grep aws-storage-mcp
   ```

3. View container logs:
   ```bash
   docker compose logs -f
   ```

### AWS Credentials Issues

If you encounter AWS credentials issues:

1. Verify your credentials are correctly configured:
   ```bash
   aws sts get-caller-identity
   ```

2. Check if the credentials are mounted correctly in the container:
   ```bash
   docker exec aws-storage-mcp-aws-storage-mcp-1 ls -la /root/.aws/
   ```

### MCP Registration Issues

If you encounter issues with MCP registration:

1. Check if the MCP server is already registered:
   ```bash
   q mcp list
   ```

2. Remove and re-add the MCP server:
   ```bash
   q mcp remove --name aws-storage
   q mcp add --name aws-storage --command "docker compose -f $(pwd)/docker-compose.yml up" --scope global
   ```
