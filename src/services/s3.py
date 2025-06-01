#!/usr/bin/env python3
import json
import logging
import uuid
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
    
    def get_bucket_replication(self, bucket_name):
        """Get replication configuration for an S3 bucket"""
        try:
            s3_client = self._get_client('s3')
            response = s3_client.get_bucket_replication(Bucket=bucket_name)
            return {"status": "success", "replication_config": response.get('ReplicationConfiguration', {})}
        except ClientError as e:
            if e.response['Error']['Code'] == 'ReplicationConfigurationNotFoundError':
                return {"status": "success", "replication_config": None, "message": "No replication configuration exists for this bucket"}
            logger.error(f"Error getting replication configuration for bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def create_replication(self, source_bucket, destination_bucket, destination_region=None, prefix=None, replication_type="CRR"):
        """
        Create S3 bucket replication (Cross-Region or Same-Region)
        
        Args:
            source_bucket (str): Source bucket name
            destination_bucket (str): Destination bucket name
            destination_region (str): Destination region (for CRR)
            prefix (str): Optional prefix filter for objects to replicate
            replication_type (str): Type of replication - "CRR" (Cross-Region) or "SRR" (Same-Region)
        """
        # Request confirmation before creating replication
        params = {
            "source_bucket": source_bucket,
            "destination_bucket": destination_bucket,
            "replication_type": replication_type
        }
        
        if destination_region:
            params["destination_region"] = destination_region
        if prefix:
            params["prefix"] = prefix
            
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="S3 bucket replication",
            params=params
        )
        
        if confirmation:
            return confirmation
            
        try:
            s3_client = self._get_client('s3')
            
            # Get source bucket location
            source_location_response = s3_client.get_bucket_location(Bucket=source_bucket)
            source_region = source_location_response.get('LocationConstraint') or 'us-east-1'
            
            # Determine destination region
            if not destination_region:
                if replication_type == "CRR":
                    # For CRR, use a different region than source
                    destination_region = 'us-west-2' if source_region != 'us-west-2' else 'us-east-1'
                else:
                    # For SRR, use the same region as source
                    destination_region = source_region
            
            # Enable versioning on source bucket (required for replication)
            s3_client.put_bucket_versioning(
                Bucket=source_bucket,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Enable versioning on destination bucket (required for replication)
            dest_s3_client = self._get_client('s3') if destination_region == source_region else boto3.client(
                's3', 
                region_name=destination_region,
                aws_access_key_id=s3_client._request_signer._credentials.access_key,
                aws_secret_access_key=s3_client._request_signer._credentials.secret_key,
                aws_session_token=s3_client._request_signer._credentials.token
            )
            
            dest_s3_client.put_bucket_versioning(
                Bucket=destination_bucket,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Create IAM role for replication
            role_name = f"s3-replication-role-{uuid.uuid4().hex[:8]}"
            iam_client = self._get_client('iam')
            
            # Create trust policy for S3 service
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "s3.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            # Create the IAM role
            role_response = iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy)
            )
            
            role_arn = role_response['Role']['Arn']
            
            # Create policy document for replication permissions
            policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:GetReplicationConfiguration",
                            "s3:ListBucket"
                        ],
                        "Resource": [
                            f"arn:aws:s3:::{source_bucket}"
                        ]
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:GetObjectVersion",
                            "s3:GetObjectVersionAcl"
                        ],
                        "Resource": [
                            f"arn:aws:s3:::{source_bucket}/*"
                        ]
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:ReplicateObject",
                            "s3:ReplicateDelete"
                        ],
                        "Resource": f"arn:aws:s3:::{destination_bucket}/*"
                    }
                ]
            }
            
            # Attach policy to role
            policy_name = f"s3-replication-policy-{uuid.uuid4().hex[:8]}"
            policy_response = iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document)
            )
            
            policy_arn = policy_response['Policy']['Arn']
            
            iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            
            # Create replication configuration
            replication_config = {
                'Role': role_arn,
                'Rules': [
                    {
                        'ID': f"{replication_type}-{uuid.uuid4().hex[:8]}",
                        'Status': 'Enabled',
                        'Destination': {
                            'Bucket': f"arn:aws:s3:::{destination_bucket}"
                        }
                    }
                ]
            }
            
            # Add prefix filter if specified
            if prefix:
                replication_config['Rules'][0]['Filter'] = {
                    'Prefix': prefix
                }
            
            # Wait for IAM role to propagate
            import time
            time.sleep(10)
            
            # Apply replication configuration
            s3_client.put_bucket_replication(
                Bucket=source_bucket,
                ReplicationConfiguration=replication_config
            )
            
            return {
                "status": "success",
                "message": f"{replication_type} replication configured from {source_bucket} to {destination_bucket}",
                "details": {
                    "source_bucket": source_bucket,
                    "destination_bucket": destination_bucket,
                    "destination_region": destination_region,
                    "replication_role": role_arn
                }
            }
            
        except ClientError as e:
            logger.error(f"Error creating {replication_type} replication for bucket {source_bucket}: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_replication(self, bucket_name):
        """Delete replication configuration from an S3 bucket"""
        try:
            s3_client = self._get_client('s3')
            s3_client.delete_bucket_replication(Bucket=bucket_name)
            return {"status": "success", "message": f"Replication configuration deleted from bucket {bucket_name}"}
        except ClientError as e:
            logger.error(f"Error deleting replication configuration for bucket {bucket_name}: {e}")
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
