# AWS Storage MCP Server - Quick Start Guide

This guide demonstrates how to use the AWS Storage MCP server with Amazon Q CLI for natural language interactions with AWS storage services.

## Setup

1. **Start the MCP Server**
   ```bash
   # Clone the repository
   git clone https://github.com/aquavis12/aws-storage-mcp.git
   cd aws-storage-mcp
   
   # Build and start the Docker container
   docker compose build
   docker compose up -d
   ```

2. **Register with Amazon Q CLI**
   ```bash
   q mcp add --name aws-storage --command "docker compose -f $(pwd)/docker-compose.yml up" --scope global
   ```

## Usage Examples

Start the Amazon Q CLI chat interface:
```bash
q chat
```

### Example 1: List S3 Buckets

**User Input:**
```
List my S3 buckets
```

**Response:**
```
I've found your S3 buckets:

1. amplify-eco-images-2024
   - Created on: November 16, 2024

2. htmlreportdemo2025
   - Created on: May 7, 2025

3. vishniterraform3036
   - Created on: May 13, 2025
```

### Example 2: Check Bucket Versioning Status

**User Input:**
```
Get versioning status for an S3 bucket
```

**Response:**
```
I've checked the versioning status for the S3 bucket "amplify-eco-images-2024" and found that:

Versioning Status: Enabled

This means that:
- The bucket is configured to keep multiple versions of objects
- When objects are overwritten or deleted, previous versions are retained
- You can retrieve older versions of objects if needed
- This provides protection against accidental deletions or overwrites
```

### Example 3: Create a New S3 Bucket

**User Input:**
```
Create a new S3 bucket with name my-test-bucket-2025 in us-west-1 region
```

**Response:**
```
Great! I've successfully created a new S3 bucket for you with your specified parameters:

Bucket Name: my-test-bucket-2025
Region: us-west-1 (US West - N. California)
Status: Created successfully

The bucket has been created in the US West (N. California) region as requested.
```

### Example 4: List Objects in a Bucket

**User Input:**
```
List objects in an S3 bucket
```

**Response:**
```
I've retrieved the objects in the "amplify-eco-images-2024" bucket. Here's what's in the bucket:

Bucket: amplify-eco-images-2024

1. Demo.mp4
   - Size: 145,208,606 bytes (approximately 138.5 MB)
   - Last Modified: November 22, 2024 at 15:52:14 UTC

2. Ewaste.pptx
   - Size: 1,424,512 bytes (approximately 1.4 MB)
   - Last Modified: November 23, 2024 at 08:14:45 UTC
```

### Example 5: Check EBS Snapshots

**User Input:**
```
List EBS snapshots in us-east-1
```

**Response:**
```
I found 1 EBS snapshot in the us-east-1 region:

Snapshot Details:
- ID: snap-0e6bc837abeb716bb
- Volume ID: vol-09460e50ce3b2d348
- State: completed
- Progress: 100%
- Start Time: November 9, 2024 at 11:42:47 UTC
- Description: Created by CreateImage(i-09ad8bbfd34c74292) for ami-061f7cd48c3fd7a47
```

### Example 6: Delete S3 Buckets

**User Input:**
```
Delete the S3 bucket named my-test-bucket-2025
```

**Response:**
```
The S3 bucket has been successfully deleted:

Bucket Name: my-test-bucket-2025
Status: Deleted successfully

The bucket has been completely removed from your AWS account.
```

## Available Services

The AWS Storage MCP server supports natural language interactions with:
- Amazon S3
- Amazon EBS
- Amazon EFS
- Amazon FSx
- AWS Storage Gateway
- Amazon S3 Glacier
- AWS Snow Family
- AWS Backup
- Amazon S3 Object Lambda

## Troubleshooting

If you encounter issues:

1. Check if the server is running:
   ```bash
   curl -s -X GET http://localhost:8080/health
   ```

2. View server logs:
   ```bash
   docker logs aws-storage-mcp-aws-storage-mcp-1
   ```

3. Check available API endpoints:
   ```bash
   curl -s -X GET http://localhost:8080/api
   ```
