# Usage Guide for AWS Storage MCP Server

This guide provides detailed instructions on how to use the AWS Storage MCP Server with Amazon Q CLI.

## Getting Started

After completing the installation steps in the [Installation Guide](INSTALLATION.md), you can start using the AWS Storage MCP Server to interact with AWS storage services using natural language.

### Starting the Server

1. **Start the Docker container**:
   ```bash
   cd /path/to/aws-storage-mcp
   docker compose up -d
   ```

2. **Verify the server is running**:
   ```bash
   docker ps | grep aws-storage
   ```
   
   You should see output similar to:
   ```
   6ac8abe70c80   aws-storage-mcp-aws-storage-mcp   "python src/server.p…"   7 seconds ago   Up 6 seconds   0.0.0.0:8080->8080/tcp, [::]:8080->8080/tcp   aws-storage-mcp-aws-storage-mcp-1
   ```

3. **Test the server health**:
   ```bash
   curl http://localhost:8080/health
   ```
   
   You should receive a response like:
   ```json
   {"status": "success", "message": "Server is running"}
   ```

### Using with Amazon Q CLI

1. **Start Amazon Q Chat**:
   ```bash
   q chat
   ```

2. **Enter natural language queries** about AWS storage services:
   ```
   List my S3 buckets
   ```
   
   ```
   Show me my EBS volumes
   ```

## Example Commands

### Amazon S3

#### List all S3 buckets
```
List my S3 buckets
```

#### List objects in a bucket
```
Show me the contents of my bucket named example-bucket
```

#### Get bucket details
```
What region is my bucket example-bucket in?
```

#### Create a new bucket
```
Create a new S3 bucket called my-new-bucket
```

### Amazon EBS

#### List all EBS volumes
```
List my EBS volumes
```

#### Create a snapshot
```
Create a snapshot of my EBS volume vol-12345abcdef
```

### Amazon EFS

#### List file systems
```
Show me my EFS file systems
```

#### List mount targets
```
How can I mount my EFS file system fs-12345abc?
```

## Testing the API Directly

You can also interact with the MCP server directly using curl commands:

### List AWS Profiles
```bash
curl -s -X POST -H "Content-Type: application/json" -d '{"tool_name": "list_aws_profiles", "parameters": {}}' http://localhost:8080/invoke
```

### List S3 Buckets
```bash
curl -s -X POST -H "Content-Type: application/json" -d '{"tool_name": "s3_list_buckets", "parameters": {}}' http://localhost:8080/invoke
```

### List Objects in a Bucket
```bash
curl -s -X POST -H "Content-Type: application/json" -d '{"tool_name": "s3_list_objects", "parameters": {"bucket_name": "example-bucket"}}' http://localhost:8080/invoke
```

## Troubleshooting

### Common Issues

1. **"Unknown action" error**:
   If you receive an error like `{"status": "error", "message": "Unknown action: None"}`, make sure you're using the correct format for your requests:
   
   ```bash
   curl -s -X POST -H "Content-Type: application/json" -d '{"tool_name": "list_aws_profiles", "parameters": {}}' http://localhost:8080/invoke
   ```

2. **AWS credential errors**:
   If you see errors related to AWS credentials, check:
   - Your AWS credentials file contains valid credentials
   - The Docker container has access to your credentials
   - The volume mapping in `docker-compose.override.yml` is correct

3. **Container not starting**:
   If the Docker container fails to start, check:
   - Docker logs: `docker logs aws-storage-mcp-aws-storage-mcp-1`
   - Docker-compose configuration: `docker-compose.yml` and `docker-compose.override.yml`

### Restarting the Server

If you need to restart the server:

```bash
docker compose restart
```

Or to completely rebuild and restart:

```bash
docker compose down
docker compose build
docker compose up -d
```

## Advanced Usage

### Using Different AWS Profiles

To use a different AWS profile:

```bash
curl -s -X POST -H "Content-Type: application/json" -d '{"tool_name": "set_profile", "parameters": {"profile_name": "production"}}' http://localhost:8080/invoke
```

Then subsequent commands will use that profile:

```bash
curl -s -X POST -H "Content-Type: application/json" -d '{"tool_name": "s3_list_buckets", "parameters": {}}' http://localhost:8080/invoke
```

### API Documentation

To view the API documentation:

```bash
curl http://localhost:8080/api
```

## Security Considerations

- The MCP server runs with your AWS credentials
- All operations are executed with your permissions
- Consider using IAM roles with least privilege principles
- Review the code before running in production environments

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review the Docker logs: `docker logs aws-storage-mcp-aws-storage-mcp-1`
3. Open an issue on the GitHub repository
