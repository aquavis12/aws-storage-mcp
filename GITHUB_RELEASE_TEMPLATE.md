# AWS Storage MCP Server v1.0.0

First stable release of AWS Storage MCP Server with S3 object-level operations.

## Features

- **S3 Object Operations**: Get, put, and delete objects in S3 buckets
- **Comprehensive AWS Storage Support**: Full support for all major AWS storage services
- **Natural Language Interface**: Interact with AWS storage services using plain English
- **Secure Operations**: Confirmation prompts for resource creation and modification

## Installation

```bash
# Clone the repository
git clone https://github.com/aquavis12/aws-storage-mcp.git
cd aws-storage-mcp

# Start the server
./start-docker.sh
```

For detailed instructions, see the [Installation Guide](docs/INSTALLATION.md).

## Documentation

- [Usage Guide](docs/USAGE.md)
- [Examples](docs/EXAMPLES.md)
- [Full Changelog](CHANGELOG.md)

## Known Issues

- Large binary files (>1MB) cannot be displayed directly when using `s3_get_object`
- Some advanced FSx operations may require additional IAM permissions
