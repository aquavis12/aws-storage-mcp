# Usage Guide

This guide provides examples and instructions for using the AWS Storage MCP Server with Amazon Q CLI.

## Basic Usage

Once you have installed and configured the AWS Storage MCP Server, you can interact with AWS storage services using natural language commands through Amazon Q CLI.

### General Format

```bash
q "Your natural language request about AWS storage services"
```

## Examples by Service

### Amazon S3

#### List all S3 buckets
```bash
q "List all my S3 buckets"
q "Show me my S3 buckets"
```

#### Get bucket details
```bash
q "Get details about my bucket named example-bucket"
q "What region is my bucket example-bucket in?"
q "Is versioning enabled on my bucket example-bucket?"
```

#### List objects in a bucket
```bash
q "List objects in my bucket example-bucket"
q "Show me the contents of example-bucket"
q "What files are in my S3 bucket example-bucket?"
```

#### Create a new bucket
```bash
q "Create a new S3 bucket named new-example-bucket"
q "Make a new S3 bucket called new-example-bucket in us-west-2"
```

#### Delete a bucket
```bash
q "Delete my S3 bucket named old-example-bucket"
q "Remove the bucket old-example-bucket"
```

### Amazon EBS

#### List volumes
```bash
q "List all my EBS volumes"
q "Show me my EBS volumes in us-east-1"
q "What EBS volumes do I have?"
```

#### Get volume details
```bash
q "Get details about volume vol-12345abcdef"
q "Tell me about my EBS volume vol-12345abcdef"
```

#### Create a snapshot
```bash
q "Create a snapshot of volume vol-12345abcdef"
q "Take a snapshot of my EBS volume vol-12345abcdef"
```

#### List snapshots
```bash
q "List all my EBS snapshots"
q "Show me snapshots for volume vol-12345abcdef"
```

### Amazon EFS

#### List file systems
```bash
q "List all my EFS file systems"
q "Show me my EFS file systems"
```

#### Get file system details
```bash
q "Get details about file system fs-12345abc"
q "Tell me about my EFS file system fs-12345abc"
```

#### List mount targets
```bash
q "List mount targets for file system fs-12345abc"
q "How can I mount my EFS file system fs-12345abc?"
```

### Amazon FSx

#### List file systems
```bash
q "List all my FSx file systems"
q "Show me my FSx file systems"
```

#### List backups
```bash
q "List all my FSx backups"
q "Show me backups for FSx file system fs-12345abc"
```

## Direct API Usage

You can also interact with the server directly using curl:

```bash
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{"action": "s3_list_buckets", "params": {}}'
```

### Common API Actions

#### S3 Actions
- `s3_list_buckets`: List all S3 buckets
- `s3_get_bucket_location`: Get bucket location
  ```json
  {"action": "s3_get_bucket_location", "params": {"bucket_name": "example-bucket"}}
  ```
- `s3_list_objects`: List objects in a bucket
  ```json
  {"action": "s3_list_objects", "params": {"bucket_name": "example-bucket"}}
  ```

#### EBS Actions
- `ebs_list_volumes`: List all EBS volumes
- `ebs_describe_volume`: Get volume details
  ```json
  {"action": "ebs_describe_volume", "params": {"volume_id": "vol-12345abcdef"}}
  ```

#### EFS Actions
- `efs_list_file_systems`: List all EFS file systems
- `efs_list_mount_targets`: List mount targets for a file system
  ```json
  {"action": "efs_list_mount_targets", "params": {"file_system_id": "fs-12345abc"}}
  ```

## Tips for Effective Usage

1. **Be specific**: Include resource names, IDs, and regions when possible
2. **Use natural language**: The MCP server understands conversational requests
3. **Check permissions**: Ensure your AWS credentials have the necessary permissions
4. **Explore capabilities**: Try different phrasings to discover what the server can do
