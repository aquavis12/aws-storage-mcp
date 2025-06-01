# AWS Storage MCP Server

![AWS Storage](https://img.shields.io/badge/AWS-Storage-orange)
![MCP](https://img.shields.io/badge/MCP-Server-blue)
![License](https://img.shields.io/badge/License-MIT-green)

A Model Context Protocol (MCP) server that enables natural language interactions with AWS storage services through Amazon Q CLI.

## What is MCP?

The Model Context Protocol (MCP) is an open protocol that standardizes how applications provide context to Large Language Models (LLMs). MCP enables communication between LLMs like Amazon Q and locally running MCP servers that provide additional tools and capabilities.

### Why Use MCP?

- **Natural Language Interface**: Interact with AWS services using plain English instead of complex CLI commands
- **Simplified Workflows**: Perform complex operations with simple queries like "list my S3 buckets"
- **Contextual Understanding**: MCP servers provide domain-specific knowledge to LLMs
- **Extended Capabilities**: Add new functionalities to your LLM without retraining the model
- **Local Execution**: Operations execute on your local machine with your credentials

## What This Project Does

This AWS Storage MCP server connects Amazon Q to your AWS storage services, allowing you to:

1. **Query AWS storage resources** using natural language
2. **Perform operations** on AWS storage services without remembering complex commands
3. **Get information** about your storage resources in a conversational manner
4. **Manage multiple storage services** from a single interface

## Architecture
[Architecture](/docs/arch.drawio.png)

## Supported AWS Storage Services

- **Amazon S3**: Object storage for any type of data
- **Amazon EBS**: Block storage for EC2 instances
- **Amazon EFS**: Scalable file storage for EC2 instances
- **Amazon FSx**: Fully managed file storage built on Windows Server
- **AWS Storage Gateway**: Hybrid cloud storage that connects on-premises environments with cloud storage
- **Amazon S3 Glacier**: Low-cost archive storage
- **AWS Snow Family**: Physical devices for data migration and edge computing
- **AWS Backup**: Centralized backup service
- **Amazon S3 Object Lambda**: Process S3 data during retrieval
- **Amazon S3 Glacier Deep Archive**: Lowest-cost archive storage class

## Prerequisites

- Docker and Docker Compose
- AWS CLI configured with valid credentials
- Amazon Q CLI installed

## Quick Start

- **For detailed installation instructions, please refer to the [Installation Guide](docs/INSTALLATION.md).
- **For detailed usage examples, please refer to the [Usage Guide](docs/USAGE.md).
- **For practical examples and demonstrations, see the [Examples Guide](docs/EXAMPLES.md).**

## Architecture

The AWS Storage MCP server follows a modular architecture that enables natural language interactions with AWS storage services:

![AWS Storage MCP Architecture](docs/aws-storage-mcp-architecture.drawio)

For a detailed view of the architecture, open the diagram file in [draw.io](https://app.diagrams.net/).

## Troubleshooting

If you encounter issues:

1. **Check Docker Container Status**
   ```bash
   docker ps | grep aws-storage
   ```

2. **View Container Logs**
   ```bash
   docker logs aws-storage-mcp-aws-storage-mcp-1
   ```

3. **Test the API Directly**
   ```bash
   curl -s -X POST -H "Content-Type: application/json" -d '{"tool_name": "list_aws_profiles", "parameters": {}}' http://localhost:8080/invoke
   ```

4. **Verify AWS Credentials**
   Make sure your AWS credentials are valid and have the necessary permissions.

5. **Restart the Container**
   ```bash
   docker compose restart
   ```

## Project Structure

```
aws-storage-mcp/
├── README.md               # This documentation
├── requirements.txt        # Python dependencies
├── mcp-manifest.json       # MCP server manifest
├── docker-compose.yml      # Docker configuration
├── docker-compose.override.yml # Volume mapping for AWS credentials
├── Dockerfile              # Docker build instructions
├── setup.sh                # Environment setup script
├── start-docker.sh         # Server startup script
└── src/                    # Source code
    ├── server.py           # MCP server implementation
    └── services/           # AWS service modules
        ├── __init__.py
        ├── base.py         # Base service class
        ├── s3.py           # S3 operations
        ├── ebs.py          # EBS operations
        ├── efs.py          # EFS operations
        └── ...             # Other service modules
```

## Documentation

- [Installation Guide](docs/INSTALLATION.md) - Detailed installation instructions
- [Usage Guide](docs/USAGE.md) - Examples and usage instructions
- [Contributing Guide](CONTRIBUTING.md) - How to contribute to this project
- [Code of Conduct](CODE_OF_CONDUCT.md) - Community guidelines

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and suggest enhancements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security Notes

- This MCP server runs with your AWS credentials
- All operations are executed with your permissions
- Review the code before running in production environments
- Consider using IAM roles with least privilege principles
