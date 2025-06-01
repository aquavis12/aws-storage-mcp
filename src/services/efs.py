#!/usr/bin/env python3
import logging
from botocore.exceptions import ClientError
from .base import BaseService

logger = logging.getLogger('aws-storage-mcp')

class EFSService(BaseService):
    """Handler for Amazon EFS operations"""
    
    def list_filesystems(self):
        """List all EFS file systems"""
        try:
            efs_client = self._get_client('efs')
            response = efs_client.describe_file_systems()
            filesystems = [{
                "id": fs['FileSystemId'],
                "size": fs.get('SizeInBytes', {}).get('Value', 0),
                "state": fs['LifeCycleState'],
                "name": fs.get('Name', ''),
                "performance_mode": fs['PerformanceMode'],
                "encrypted": fs['Encrypted'],
                "throughput_mode": fs['ThroughputMode']
            } for fs in response['FileSystems']]
            return {"status": "success", "filesystems": filesystems}
        except ClientError as e:
            logger.error(f"Error listing EFS file systems: {e}")
            return {"status": "error", "message": str(e)}
    
    def create_filesystem(self, name):
        """Create a new EFS file system"""
        try:
            efs_client = self._get_client('efs')
            response = efs_client.create_file_system(
                PerformanceMode='generalPurpose',
                Encrypted=True,
                Tags=[
                    {
                        'Key': 'Name',
                        'Value': name
                    },
                ]
            )
            
            return {
                "status": "success", 
                "filesystem_id": response['FileSystemId'],
                "message": f"EFS file system {response['FileSystemId']} created successfully"
            }
        except ClientError as e:
            logger.error(f"Error creating EFS file system: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_filesystem(self, filesystem_id):
        """Delete an EFS file system"""
        try:
            efs_client = self._get_client('efs')
            efs_client.delete_file_system(FileSystemId=filesystem_id)
            return {"status": "success", "message": f"EFS file system {filesystem_id} deleted successfully"}
        except ClientError as e:
            logger.error(f"Error deleting EFS file system {filesystem_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def create_mount_target(self, filesystem_id, subnet_id, security_groups=None):
        """Create a mount target for an EFS file system"""
        try:
            efs_client = self._get_client('efs')
            params = {
                'FileSystemId': filesystem_id,
                'SubnetId': subnet_id
            }
            
            if security_groups:
                params['SecurityGroups'] = security_groups
                
            response = efs_client.create_mount_target(**params)
            
            return {
                "status": "success",
                "mount_target_id": response['MountTargetId'],
                "message": f"Mount target {response['MountTargetId']} created successfully"
            }
        except ClientError as e:
            logger.error(f"Error creating mount target for EFS {filesystem_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def list_mount_targets(self, filesystem_id):
        """List mount targets for an EFS file system"""
        try:
            efs_client = self._get_client('efs')
            response = efs_client.describe_mount_targets(FileSystemId=filesystem_id)
            
            mount_targets = [{
                "id": mt['MountTargetId'],
                "subnet_id": mt['SubnetId'],
                "ip_address": mt['IpAddress'],
                "state": mt['LifeCycleState'],
                "network_interface_id": mt.get('NetworkInterfaceId', '')
            } for mt in response['MountTargets']]
            
            return {"status": "success", "mount_targets": mount_targets}
        except ClientError as e:
            logger.error(f"Error listing mount targets for EFS {filesystem_id}: {e}")
            return {"status": "error", "message": str(e)}
