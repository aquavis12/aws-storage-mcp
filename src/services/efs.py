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
        # Request confirmation before creating the file system
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="EFS file system",
            params={
                "name": name,
                "performance_mode": "generalPurpose",
                "encrypted": "True"
            }
        )
        
        if confirmation:
            return confirmation
            
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
        # Request confirmation before creating the mount target
        params_dict = {
            "filesystem_id": filesystem_id,
            "subnet_id": subnet_id
        }
        if security_groups:
            params_dict["security_groups"] = security_groups
            
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="EFS mount target",
            params=params_dict
        )
        
        if confirmation:
            return confirmation
            
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
    def create_replication(self, source_filesystem_id, destination_region=None):
        """
        Create EFS replication configuration
        
        Args:
            source_filesystem_id (str): ID of the source EFS file system
            destination_region (str): Destination region for replication (if None, a different region will be selected)
        """
        # Request confirmation before creating replication
        params = {
            "source_filesystem_id": source_filesystem_id
        }
        
        if destination_region:
            params["destination_region"] = destination_region
            
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="EFS replication",
            params=params
        )
        
        if confirmation:
            return confirmation
            
        try:
            efs_client = self._get_client('efs')
            
            # Get source file system details
            source_fs = efs_client.describe_file_systems(FileSystemId=source_filesystem_id)['FileSystems'][0]
            
            # Determine destination region if not provided
            if not destination_region:
                # Get current region
                source_region = self.region
                
                # Choose a different region for replication
                regions = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'eu-west-1']
                destination_region = next((r for r in regions if r != source_region), 'us-west-2')
            
            # Create replication configuration
            response = efs_client.create_replication_configuration(
                SourceFileSystemId=source_filesystem_id,
                Destinations=[
                    {
                        'Region': destination_region
                    }
                ]
            )
            
            return {
                "status": "success",
                "source_filesystem_id": source_filesystem_id,
                "destination_region": destination_region,
                "replication_configuration": {
                    "original_source_id": response['SourceFileSystemId'],
                    "creation_time": response['CreationTime'].isoformat(),
                    "destinations": [
                        {
                            "status": dest['Status'],
                            "region": dest['Region'],
                            "filesystem_id": dest.get('FileSystemId', 'Creating...')
                        } for dest in response['Destinations']
                    ]
                },
                "message": f"EFS replication configuration created successfully"
            }
        except ClientError as e:
            logger.error(f"Error creating EFS replication for {source_filesystem_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_replication(self, filesystem_id):
        """Delete EFS replication configuration"""
        try:
            efs_client = self._get_client('efs')
            efs_client.delete_replication_configuration(SourceFileSystemId=filesystem_id)
            return {"status": "success", "message": f"EFS replication configuration deleted for {filesystem_id}"}
        except ClientError as e:
            logger.error(f"Error deleting EFS replication for {filesystem_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def describe_replication(self, filesystem_id):
        """Get details about an EFS replication configuration"""
        try:
            efs_client = self._get_client('efs')
            response = efs_client.describe_replication_configurations(FileSystemId=filesystem_id)
            
            if not response['Replications']:
                return {"status": "success", "message": f"No replication configuration found for {filesystem_id}", "replication": None}
            
            replication = response['Replications'][0]
            
            return {
                "status": "success",
                "replication": {
                    "source_filesystem_id": replication['SourceFileSystemId'],
                    "creation_time": replication['CreationTime'].isoformat(),
                    "destinations": [
                        {
                            "status": dest['Status'],
                            "region": dest['Region'],
                            "filesystem_id": dest.get('FileSystemId', '')
                        } for dest in replication['Destinations']
                    ]
                }
            }
        except ClientError as e:
            logger.error(f"Error describing EFS replication for {filesystem_id}: {e}")
            return {"status": "error", "message": str(e)}
