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
    def put_bucket_lifecycle_configuration(self, bucket_name, lifecycle_rules):
        """
        Add or update lifecycle configuration for an S3 bucket
        
        Args:
            bucket_name (str): Name of the S3 bucket
            lifecycle_rules (list): List of lifecycle rules
        """
        # Request confirmation before setting lifecycle configuration
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="S3 bucket lifecycle configuration",
            params={
                "bucket_name": bucket_name,
                "rules_count": len(lifecycle_rules)
            }
        )
        
        if confirmation:
            return confirmation
            
        try:
            s3_client = self._get_client('s3')
            
            # Format the lifecycle configuration
            lifecycle_config = {
                'Rules': lifecycle_rules
            }
            
            s3_client.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration=lifecycle_config
            )
            
            return {
                "status": "success",
                "message": f"Lifecycle configuration applied to bucket {bucket_name} successfully"
            }
        except ClientError as e:
            logger.error(f"Error setting lifecycle configuration for bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_bucket_lifecycle_configuration(self, bucket_name):
        """Get lifecycle configuration for an S3 bucket"""
        try:
            s3_client = self._get_client('s3')
            response = s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
            return {"status": "success", "lifecycle_configuration": response.get('Rules', [])}
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
                return {"status": "success", "lifecycle_configuration": [], "message": "No lifecycle configuration exists for this bucket"}
            logger.error(f"Error getting lifecycle configuration for bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_bucket_lifecycle_configuration(self, bucket_name):
        """Delete lifecycle configuration from an S3 bucket"""
        try:
            s3_client = self._get_client('s3')
            s3_client.delete_bucket_lifecycle(Bucket=bucket_name)
            return {"status": "success", "message": f"Lifecycle configuration deleted from bucket {bucket_name}"}
        except ClientError as e:
            logger.error(f"Error deleting lifecycle configuration for bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def put_bucket_policy(self, bucket_name, policy):
        """
        Add or update policy for an S3 bucket
        
        Args:
            bucket_name (str): Name of the S3 bucket
            policy (dict): Bucket policy document
        """
        # Request confirmation before setting bucket policy
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="S3 bucket policy",
            params={
                "bucket_name": bucket_name
            }
        )
        
        if confirmation:
            return confirmation
            
        try:
            s3_client = self._get_client('s3')
            
            # Convert policy dict to JSON string
            policy_str = json.dumps(policy)
            
            s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=policy_str
            )
            
            return {
                "status": "success",
                "message": f"Policy applied to bucket {bucket_name} successfully"
            }
        except ClientError as e:
            logger.error(f"Error setting policy for bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_bucket_policy(self, bucket_name):
        """Delete policy from an S3 bucket"""
        try:
            s3_client = self._get_client('s3')
            s3_client.delete_bucket_policy(Bucket=bucket_name)
            return {"status": "success", "message": f"Policy deleted from bucket {bucket_name}"}
        except ClientError as e:
            logger.error(f"Error deleting policy for bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def put_public_access_block(self, bucket_name, block_public_acls=True, ignore_public_acls=True, 
                               block_public_policy=True, restrict_public_buckets=True):
        """
        Configure block public access settings for an S3 bucket
        
        Args:
            bucket_name (str): Name of the S3 bucket
            block_public_acls (bool): Block public ACLs
            ignore_public_acls (bool): Ignore public ACLs
            block_public_policy (bool): Block public policy
            restrict_public_buckets (bool): Restrict public buckets
        """
        # Request confirmation before setting public access block
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="S3 public access block",
            params={
                "bucket_name": bucket_name,
                "block_public_acls": block_public_acls,
                "ignore_public_acls": ignore_public_acls,
                "block_public_policy": block_public_policy,
                "restrict_public_buckets": restrict_public_buckets
            }
        )
        
        if confirmation:
            return confirmation
            
        try:
            s3_client = self._get_client('s3')
            
            s3_client.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': block_public_acls,
                    'IgnorePublicAcls': ignore_public_acls,
                    'BlockPublicPolicy': block_public_policy,
                    'RestrictPublicBuckets': restrict_public_buckets
                }
            )
            
            return {
                "status": "success",
                "message": f"Public access block settings applied to bucket {bucket_name} successfully"
            }
        except ClientError as e:
            logger.error(f"Error setting public access block for bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_public_access_block(self, bucket_name):
        """Get block public access settings for an S3 bucket"""
        try:
            s3_client = self._get_client('s3')
            response = s3_client.get_public_access_block(Bucket=bucket_name)
            return {
                "status": "success", 
                "public_access_block": response.get('PublicAccessBlockConfiguration', {})
            }
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                return {"status": "success", "public_access_block": None, "message": "No public access block configuration exists for this bucket"}
            logger.error(f"Error getting public access block for bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_public_access_block(self, bucket_name):
        """Delete block public access settings from an S3 bucket"""
        try:
            s3_client = self._get_client('s3')
            s3_client.delete_public_access_block(Bucket=bucket_name)
            return {"status": "success", "message": f"Public access block settings deleted from bucket {bucket_name}"}
        except ClientError as e:
            logger.error(f"Error deleting public access block for bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
            
    def get_object(self, bucket_name, object_key):
        """
        Get an object from an S3 bucket
        
        Args:
            bucket_name (str): Name of the S3 bucket
            object_key (str): Key of the object to retrieve
        """
        try:
            s3_client = self._get_client('s3')
            response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
            
            # Read the object content
            content = response['Body'].read()
            
            # Try to decode as text if possible
            try:
                content_str = content.decode('utf-8')
                is_text = True
            except UnicodeDecodeError:
                content_str = None
                is_text = False
            
            result = {
                "status": "success",
                "metadata": {
                    "content_type": response.get('ContentType'),
                    "content_length": response.get('ContentLength'),
                    "last_modified": response.get('LastModified').isoformat() if response.get('LastModified') else None,
                    "etag": response.get('ETag'),
                    "is_text": is_text
                }
            }
            
            # Include content if it's text and not too large
            if is_text and len(content_str) < 1024 * 1024:  # Limit to 1MB
                result["content"] = content_str
            elif is_text:
                result["message"] = "Content too large to display (> 1MB). Use a more specific operation to download."
            else:
                result["message"] = "Binary content. Use a more specific operation to download."
                
            return result
            
        except ClientError as e:
            logger.error(f"Error getting object {object_key} from bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def put_object(self, bucket_name, object_key, content, content_type=None):
        """
        Put an object into an S3 bucket
        
        Args:
            bucket_name (str): Name of the S3 bucket
            object_key (str): Key for the object
            content (str): Content to upload
            content_type (str): Content type of the object (optional)
        """
        # Request confirmation before uploading object
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="S3 object",
            params={
                "bucket_name": bucket_name,
                "object_key": object_key,
                "content_type": content_type or "application/octet-stream"
            }
        )
        
        if confirmation:
            return confirmation
            
        try:
            s3_client = self._get_client('s3')
            
            # Prepare parameters
            params = {
                'Bucket': bucket_name,
                'Key': object_key,
                'Body': content
            }
            
            # Add content type if provided
            if content_type:
                params['ContentType'] = content_type
                
            # Upload the object
            s3_client.put_object(**params)
            
            return {
                "status": "success",
                "message": f"Object {object_key} uploaded to bucket {bucket_name} successfully"
            }
        except ClientError as e:
            logger.error(f"Error uploading object {object_key} to bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_object(self, bucket_name, object_key):
        """
        Delete an object from an S3 bucket
        
        Args:
            bucket_name (str): Name of the S3 bucket
            object_key (str): Key of the object to delete
        """
        try:
            s3_client = self._get_client('s3')
            s3_client.delete_object(Bucket=bucket_name, Key=object_key)
            return {
                "status": "success",
                "message": f"Object {object_key} deleted from bucket {bucket_name} successfully"
            }
        except ClientError as e:
            logger.error(f"Error deleting object {object_key} from bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def put_bucket_website(self, bucket_name, index_document, error_document=None, redirect_all_requests_to=None):
        """
        Configure static website hosting for an S3 bucket
        
        Args:
            bucket_name (str): Name of the S3 bucket
            index_document (str): Index document suffix (e.g., 'index.html')
            error_document (str): Error document key (e.g., 'error.html')
            redirect_all_requests_to (dict): Redirect configuration
        """
        # Request confirmation before setting website configuration
        params = {
            "bucket_name": bucket_name,
            "index_document": index_document
        }
        if error_document:
            params["error_document"] = error_document
        if redirect_all_requests_to:
            params["redirect_all_requests_to"] = redirect_all_requests_to
            
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="S3 website configuration",
            params=params
        )
        
        if confirmation:
            return confirmation
            
        try:
            s3_client = self._get_client('s3')
            
            website_config = {}
            
            if redirect_all_requests_to:
                website_config['RedirectAllRequestsTo'] = redirect_all_requests_to
            else:
                website_config['IndexDocument'] = {'Suffix': index_document}
                if error_document:
                    website_config['ErrorDocument'] = {'Key': error_document}
            
            s3_client.put_bucket_website(
                Bucket=bucket_name,
                WebsiteConfiguration=website_config
            )
            
            # Get the website endpoint
            region = self.get_bucket_location(bucket_name).get('location')
            if region == 'us-east-1':
                website_endpoint = f"http://{bucket_name}.s3-website-{region}.amazonaws.com"
            else:
                website_endpoint = f"http://{bucket_name}.s3-website.{region}.amazonaws.com"
            
            return {
                "status": "success",
                "message": f"Website configuration applied to bucket {bucket_name} successfully",
                "website_endpoint": website_endpoint
            }
        except ClientError as e:
            logger.error(f"Error setting website configuration for bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_bucket_website(self, bucket_name):
        """Get website configuration for an S3 bucket"""
        try:
            s3_client = self._get_client('s3')
            response = s3_client.get_bucket_website(Bucket=bucket_name)
            
            # Remove ResponseMetadata
            if 'ResponseMetadata' in response:
                del response['ResponseMetadata']
                
            return {"status": "success", "website_configuration": response}
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchWebsiteConfiguration':
                return {"status": "success", "website_configuration": None, "message": "No website configuration exists for this bucket"}
            logger.error(f"Error getting website configuration for bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_bucket_website(self, bucket_name):
        """Delete website configuration from an S3 bucket"""
        try:
            s3_client = self._get_client('s3')
            s3_client.delete_bucket_website(Bucket=bucket_name)
            return {"status": "success", "message": f"Website configuration deleted from bucket {bucket_name}"}
        except ClientError as e:
            logger.error(f"Error deleting website configuration for bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def put_bucket_acl(self, bucket_name, acl='private'):
        """
        Set the access control list (ACL) for an S3 bucket
        
        Args:
            bucket_name (str): Name of the S3 bucket
            acl (str): Canned ACL to apply (private, public-read, public-read-write, etc.)
        """
        # Request confirmation before setting bucket ACL
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="S3 bucket ACL",
            params={
                "bucket_name": bucket_name,
                "acl": acl
            }
        )
        
        if confirmation:
            return confirmation
            
        try:
            s3_client = self._get_client('s3')
            
            s3_client.put_bucket_acl(
                Bucket=bucket_name,
                ACL=acl
            )
            
            return {
                "status": "success",
                "message": f"ACL '{acl}' applied to bucket {bucket_name} successfully"
            }
        except ClientError as e:
            logger.error(f"Error setting ACL for bucket {bucket_name}: {e}")
            return {"status": "error", "message": str(e)}
