#!/usr/bin/env python3
import json
import logging
from botocore.exceptions import ClientError
from .base import BaseService

logger = logging.getLogger('aws-storage-mcp')

class S3Service(BaseService):
    """Handler for Amazon S3 operations"""
    
    def list_buckets(self):
        """List all S3 buckets"""
        try:
            s3_client = self._get_client('s3')
            response = s3_client.list_buckets()
            buckets = [{"name": bucket['Name'], "creation_date": bucket['CreationDate'].isoformat()} 
                      for bucket in response['Buckets']]
            return {"status": "success", "buckets": buckets}
        except ClientError as e:
            logger.error(f"Error listing S3 buckets: {e}")
            return {"status": "error", "message": str(e)}
    
    def list_objects(self, bucket_name, prefix=""):
        """List objects in an S3 bucket with optional prefix"""
        try:
            s3_client = self._get_client('s3')
            response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            
            if 'Contents' in response:
                objects = [{"key": obj['Key'], "size": obj['Size'], "last_modified": obj['LastModified'].isoformat()} 
                          for obj in response['Contents']]
                return {"status": "success", "objects": objects}
            return {"status": "success", "objects": []}
        except ClientError as e:
            logger.error(f"Error listing objects in bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_bucket_location(self, bucket_name):
        """Get the region where a bucket is located"""
        try:
            s3_client = self._get_client('s3')
            response = s3_client.get_bucket_location(Bucket=bucket_name)
            location = response.get('LocationConstraint') or 'us-east-1'  # Default to us-east-1 if None
            return {"status": "success", "location": location}
        except ClientError as e:
            logger.error(f"Error getting location for bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_bucket_policy(self, bucket_name):
        """Get the policy for an S3 bucket"""
        try:
            s3_client = self._get_client('s3')
            response = s3_client.get_bucket_policy(Bucket=bucket_name)
            return {"status": "success", "policy": json.loads(response['Policy'])}
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                return {"status": "success", "policy": None, "message": "No policy exists for this bucket"}
            logger.error(f"Error getting policy for bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def create_bucket(self, bucket_name):
        """Create a new S3 bucket"""
        # Request confirmation before creating the bucket
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="S3 bucket",
            params={"bucket_name": bucket_name, "region": self.region}
        )
        
        if confirmation:
            return confirmation
            
        try:
            s3_client = self._get_client('s3')
            
            # Different create_bucket syntax for us-east-1
            if self.region == 'us-east-1':
                response = s3_client.create_bucket(Bucket=bucket_name)
            else:
                response = s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            return {"status": "success", "message": f"Bucket {bucket_name} created successfully"}
        except ClientError as e:
            logger.error(f"Error creating bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_bucket(self, bucket_name):
        """Delete an S3 bucket"""
        try:
            s3_client = self._get_client('s3')
            s3_client.delete_bucket(Bucket=bucket_name)
            return {"status": "success", "message": f"Bucket {bucket_name} deleted successfully"}
        except ClientError as e:
            logger.error(f"Error deleting bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_object_acl(self, bucket_name, object_key):
        """Get the ACL for an S3 object"""
        try:
            s3_client = self._get_client('s3')
            response = s3_client.get_object_acl(Bucket=bucket_name, Key=object_key)
            grants = []
            for grant in response.get('Grants', []):
                grantee = grant.get('Grantee', {})
                grants.append({
                    "permission": grant.get('Permission'),
                    "grantee_type": grantee.get('Type'),
                    "grantee_id": grantee.get('ID', ''),
                    "display_name": grantee.get('DisplayName', '')
                })
            return {"status": "success", "grants": grants}
        except ClientError as e:
            logger.error(f"Error getting ACL for object {object_key} in bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_bucket_versioning(self, bucket_name):
        """Get versioning status for an S3 bucket"""
        try:
            s3_client = self._get_client('s3')
            response = s3_client.get_bucket_versioning(Bucket=bucket_name)
            status = response.get('Status', 'NotEnabled')
            return {"status": "success", "versioning": status}
        except ClientError as e:
            logger.error(f"Error getting versioning for bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
