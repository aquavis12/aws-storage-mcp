#!/usr/bin/env python3
import json
import logging
from botocore.exceptions import ClientError
from .base import BaseService

logger = logging.getLogger('aws-storage-mcp')

class StorageGatewayService(BaseService):
    """Handler for AWS Storage Gateway operations"""
    
    def list_gateways(self):
        """List all Storage Gateways"""
        try:
            sg_client = self._get_client('storagegateway')
            response = sg_client.list_gateways()
            gateways = [{
                "id": gw['GatewayId'],
                "name": gw['GatewayName'],
                "type": gw['GatewayType'],
                "status": gw['GatewayOperationalState'],
                "ec2_instance_id": gw.get('Ec2InstanceId', ''),
                "endpoint_type": gw.get('GatewayEndpoint', '')
            } for gw in response['Gateways']]
            return {"status": "success", "gateways": gateways}
        except ClientError as e:
            logger.error(f"Error listing Storage Gateways: {e}")
            return {"status": "error", "message": str(e)}
    
    def list_volumes(self, gateway_id=None):
        """List Storage Gateway volumes, optionally filtered by gateway ID"""
        try:
            sg_client = self._get_client('storagegateway')
            
            if gateway_id:
                response = sg_client.list_volumes(GatewayARN=gateway_id)
            else:
                response = sg_client.list_volumes()
                
            volumes = [{
                "id": vol['VolumeARN'],
                "type": vol['VolumeType'],
                "size_in_bytes": vol['VolumeSizeInBytes'],
                "gateway_id": vol['GatewayARN'],
                "target_name": vol.get('TargetName', '')
            } for vol in response.get('VolumeInfos', [])]
            
            return {"status": "success", "volumes": volumes}
        except ClientError as e:
            logger.error(f"Error listing Storage Gateway volumes: {e}")
            return {"status": "error", "message": str(e)}
    
    def describe_gateway(self, gateway_id):
        """Get detailed information about a Storage Gateway"""
        try:
            sg_client = self._get_client('storagegateway')
            response = sg_client.describe_gateway_information(GatewayARN=gateway_id)
            
            gateway_info = {
                "id": response['GatewayARN'],
                "name": response['GatewayName'],
                "type": response['GatewayType'],
                "status": response.get('GatewayOperationalState', ''),
                "network_interfaces": response.get('GatewayNetworkInterfaces', []),
                "timezone": response.get('GatewayTimezone', ''),
                "ec2_instance_id": response.get('Ec2InstanceId', ''),
                "endpoint_type": response.get('GatewayEndpoint', ''),
                "host_environment": response.get('HostEnvironment', ''),
                "software_version": response.get('GatewaySoftwareVersion', '')
            }
            
            return {"status": "success", "gateway": gateway_info}
        except ClientError as e:
            logger.error(f"Error describing Storage Gateway {gateway_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def list_file_shares(self, gateway_id=None):
        """List Storage Gateway file shares, optionally filtered by gateway ID"""
        try:
            sg_client = self._get_client('storagegateway')
            
            if gateway_id:
                response = sg_client.list_file_shares(GatewayARN=gateway_id)
            else:
                response = sg_client.list_file_shares()
                
            file_shares = [{
                "id": share['FileShareARN'],
                "type": share['FileShareType'],
                "gateway_id": share['GatewayARN'],
                "path": share.get('Path', '')
            } for share in response.get('FileShareInfoList', [])]
            
            return {"status": "success", "file_shares": file_shares}
        except ClientError as e:
            logger.error(f"Error listing Storage Gateway file shares: {e}")
            return {"status": "error", "message": str(e)}
    def create_nfs_file_share(self, gateway_id, location_arn, client_token=None, role_arn=None, name=None):
        """
        Create an NFS file share on a Storage Gateway
        
        Args:
            gateway_id (str): The gateway ARN
            location_arn (str): The ARN of the S3 bucket or prefix
            client_token (str): A unique string to identify this request
            role_arn (str): The ARN of the IAM role for the gateway to access S3
            name (str): The name of the file share
        """
        # Request confirmation before creating the file share
        params = {
            "gateway_id": gateway_id,
            "location_arn": location_arn
        }
        
        if name:
            params["name"] = name
            
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="Storage Gateway NFS file share",
            params=params
        )
        
        if confirmation:
            return confirmation
            
        try:
            sg_client = self._get_client('storagegateway')
            
            # If no client token provided, generate one
            if not client_token:
                import uuid
                client_token = str(uuid.uuid4())
            
            # If no role ARN provided, use the default Storage Gateway role
            if not role_arn:
                iam_client = self._get_client('iam')
                try:
                    role_response = iam_client.get_role(RoleName='StorageGatewayS3Access')
                    role_arn = role_response['Role']['Arn']
                except ClientError:
                    # Create the role if it doesn't exist
                    trust_policy = {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"Service": "storagegateway.amazonaws.com"},
                                "Action": "sts:AssumeRole"
                            }
                        ]
                    }
                    
                    role_response = iam_client.create_role(
                        RoleName='StorageGatewayS3Access',
                        AssumeRolePolicyDocument=json.dumps(trust_policy),
                        Description='Role for Storage Gateway to access S3'
                    )
                    
                    # Attach the AmazonS3FullAccess policy
                    iam_client.attach_role_policy(
                        RoleName='StorageGatewayS3Access',
                        PolicyArn='arn:aws:iam::aws:policy/AmazonS3FullAccess'
                    )
                    
                    role_arn = role_response['Role']['Arn']
            
            # Create the NFS file share
            create_params = {
                'ClientToken': client_token,
                'GatewayARN': gateway_id,
                'LocationARN': location_arn,
                'Role': role_arn,
                'DefaultStorageClass': 'S3_STANDARD',
                'ObjectACL': 'private',
                'ReadOnly': False,
                'GuessMIMETypeEnabled': True,
                'RequesterPays': False,
                'Squash': 'RootSquash'
            }
            
            # Add name if provided
            if name:
                create_params['Tags'] = [{'Key': 'Name', 'Value': name}]
            
            response = sg_client.create_nfs_file_share(**create_params)
            
            return {
                "status": "success",
                "file_share_arn": response['FileShareARN'],
                "message": f"NFS file share created successfully"
            }
        except ClientError as e:
            logger.error(f"Error creating NFS file share on gateway {gateway_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def create_smb_file_share(self, gateway_id, location_arn, client_token=None, role_arn=None, name=None, password=None):
        """
        Create an SMB file share on a Storage Gateway
        
        Args:
            gateway_id (str): The gateway ARN
            location_arn (str): The ARN of the S3 bucket or prefix
            client_token (str): A unique string to identify this request
            role_arn (str): The ARN of the IAM role for the gateway to access S3
            name (str): The name of the file share
            password (str): The password for the guest access
        """
        # Request confirmation before creating the file share
        params = {
            "gateway_id": gateway_id,
            "location_arn": location_arn
        }
        
        if name:
            params["name"] = name
            
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="Storage Gateway SMB file share",
            params=params
        )
        
        if confirmation:
            return confirmation
            
        try:
            sg_client = self._get_client('storagegateway')
            
            # If no client token provided, generate one
            if not client_token:
                import uuid
                client_token = str(uuid.uuid4())
            
            # If no role ARN provided, use the default Storage Gateway role
            if not role_arn:
                iam_client = self._get_client('iam')
                try:
                    role_response = iam_client.get_role(RoleName='StorageGatewayS3Access')
                    role_arn = role_response['Role']['Arn']
                except ClientError:
                    # Create the role if it doesn't exist
                    trust_policy = {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"Service": "storagegateway.amazonaws.com"},
                                "Action": "sts:AssumeRole"
                            }
                        ]
                    }
                    
                    role_response = iam_client.create_role(
                        RoleName='StorageGatewayS3Access',
                        AssumeRolePolicyDocument=json.dumps(trust_policy),
                        Description='Role for Storage Gateway to access S3'
                    )
                    
                    # Attach the AmazonS3FullAccess policy
                    iam_client.attach_role_policy(
                        RoleName='StorageGatewayS3Access',
                        PolicyArn='arn:aws:iam::aws:policy/AmazonS3FullAccess'
                    )
                    
                    role_arn = role_response['Role']['Arn']
            
            # Create the SMB file share
            create_params = {
                'ClientToken': client_token,
                'GatewayARN': gateway_id,
                'LocationARN': location_arn,
                'Role': role_arn,
                'DefaultStorageClass': 'S3_STANDARD',
                'ObjectACL': 'private',
                'ReadOnly': False,
                'GuessMIMETypeEnabled': True,
                'RequesterPays': False,
                'Authentication': 'GuestAccess'
            }
            
            # Add password if provided
            if password:
                create_params['Authentication'] = 'Password'
                create_params['Password'] = password
            
            # Add name if provided
            if name:
                create_params['Tags'] = [{'Key': 'Name', 'Value': name}]
            
            response = sg_client.create_smb_file_share(**create_params)
            
            return {
                "status": "success",
                "file_share_arn": response['FileShareARN'],
                "message": f"SMB file share created successfully"
            }
        except ClientError as e:
            logger.error(f"Error creating SMB file share on gateway {gateway_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_file_share(self, file_share_arn):
        """Delete a Storage Gateway file share"""
        try:
            sg_client = self._get_client('storagegateway')
            sg_client.delete_file_share(FileShareARN=file_share_arn)
            return {"status": "success", "message": f"File share {file_share_arn} deleted successfully"}
        except ClientError as e:
            logger.error(f"Error deleting file share {file_share_arn}: {e}")
            return {"status": "error", "message": str(e)}
    
    def create_volume(self, gateway_id, target_name, size_in_bytes, volume_type='CACHED'):
        """
        Create a Storage Gateway volume
        
        Args:
            gateway_id (str): The gateway ARN
            target_name (str): The name of the iSCSI target
            size_in_bytes (int): The size of the volume in bytes
            volume_type (str): The type of volume (STORED, CACHED)
        """
        # Request confirmation before creating the volume
        params = {
            "gateway_id": gateway_id,
            "target_name": target_name,
            "size_in_bytes": size_in_bytes,
            "volume_type": volume_type
        }
            
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="Storage Gateway volume",
            params=params
        )
        
        if confirmation:
            return confirmation
            
        try:
            sg_client = self._get_client('storagegateway')
            
            # Create the volume based on type
            if volume_type == 'STORED':
                response = sg_client.create_stored_iscsi_volume(
                    GatewayARN=gateway_id,
                    DiskId='',  # This would need to be provided for a real implementation
                    TargetName=target_name,
                    NetworkInterfaceId='',  # This would need to be provided for a real implementation
                    PreserveExistingData=False,
                    VolumeSizeInBytes=size_in_bytes
                )
            else:  # CACHED
                response = sg_client.create_cached_iscsi_volume(
                    GatewayARN=gateway_id,
                    VolumeSizeInBytes=size_in_bytes,
                    TargetName=target_name,
                    NetworkInterfaceId='',  # This would need to be provided for a real implementation
                    SnapshotId='',  # Optional
                    SourceVolumeARN=''  # Optional
                )
            
            return {
                "status": "success",
                "volume_arn": response['VolumeARN'],
                "target_arn": response['TargetARN'],
                "message": f"Storage Gateway volume created successfully"
            }
        except ClientError as e:
            logger.error(f"Error creating volume on gateway {gateway_id}: {e}")
            return {"status": "error", "message": str(e)}
