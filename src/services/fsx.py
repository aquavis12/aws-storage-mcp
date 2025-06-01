#!/usr/bin/env python3
import logging
from botocore.exceptions import ClientError
from .base import BaseService

logger = logging.getLogger('aws-storage-mcp')

class FSxService(BaseService):
    """Handler for Amazon FSx operations"""
    
    def list_filesystems(self):
        """List all FSx file systems"""
        try:
            fsx_client = self._get_client('fsx')
            response = fsx_client.describe_file_systems()
            filesystems = [{
                "id": fs['FileSystemId'],
                "type": fs['FileSystemType'],
                "storage_capacity": fs['StorageCapacity'],
                "lifecycle": fs['Lifecycle'],
                "dns_name": fs.get('DNSName', ''),
                "network_interface_ids": fs.get('NetworkInterfaceIds', []),
                "storage_type": fs.get('StorageType', '')
            } for fs in response['FileSystems']]
            return {"status": "success", "filesystems": filesystems}
        except ClientError as e:
            logger.error(f"Error listing FSx file systems: {e}")
            return {"status": "error", "message": str(e)}
    
    def describe_filesystem(self, filesystem_id):
        """Get detailed information about an FSx file system"""
        try:
            fsx_client = self._get_client('fsx')
            response = fsx_client.describe_file_systems(FileSystemIds=[filesystem_id])
            
            if not response['FileSystems']:
                return {"status": "error", "message": f"FSx file system {filesystem_id} not found"}
                
            fs = response['FileSystems'][0]
            details = {
                "id": fs['FileSystemId'],
                "type": fs['FileSystemType'],
                "storage_capacity": fs['StorageCapacity'],
                "lifecycle": fs['Lifecycle'],
                "dns_name": fs.get('DNSName', ''),
                "network_interface_ids": fs.get('NetworkInterfaceIds', []),
                "storage_type": fs.get('StorageType', ''),
                "vpc_id": fs.get('VpcId', ''),
                "subnet_ids": fs.get('SubnetIds', []),
                "kms_key_id": fs.get('KmsKeyId', ''),
                "creation_time": fs.get('CreationTime', '').isoformat() if fs.get('CreationTime') else ''
            }
            
            # Add file system type specific details
            if fs['FileSystemType'] == 'WINDOWS':
                windows = fs.get('WindowsConfiguration', {})
                details["windows"] = {
                    "throughput_capacity": windows.get('ThroughputCapacity', 0),
                    "active_directory_id": windows.get('ActiveDirectoryId', ''),
                    "automatic_backup_retention_days": windows.get('AutomaticBackupRetentionDays', 0)
                }
            elif fs['FileSystemType'] == 'LUSTRE':
                lustre = fs.get('LustreConfiguration', {})
                details["lustre"] = {
                    "deployment_type": lustre.get('DeploymentType', ''),
                    "per_unit_storage_throughput": lustre.get('PerUnitStorageThroughput', 0),
                    "mount_name": lustre.get('MountName', '')
                }
            
            return {"status": "success", "filesystem": details}
        except ClientError as e:
            logger.error(f"Error describing FSx file system {filesystem_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def create_backup(self, filesystem_id, backup_name):
        """Create a backup of an FSx file system"""
        try:
            fsx_client = self._get_client('fsx')
            response = fsx_client.create_backup(
                FileSystemId=filesystem_id,
                Tags=[
                    {
                        'Key': 'Name',
                        'Value': backup_name
                    }
                ]
            )
            
            return {
                "status": "success",
                "backup_id": response['Backup']['BackupId'],
                "message": f"Backup {response['Backup']['BackupId']} created successfully"
            }
        except ClientError as e:
            logger.error(f"Error creating backup for FSx file system {filesystem_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def list_backups(self):
        """List all FSx backups"""
        try:
            fsx_client = self._get_client('fsx')
            response = fsx_client.describe_backups()
            
            backups = [{
                "id": backup['BackupId'],
                "filesystem_id": backup.get('FileSystemId', ''),
                "type": backup['BackupType'],
                "lifecycle": backup['Lifecycle'],
                "creation_time": backup['CreationTime'].isoformat(),
                "filesystem_type": backup.get('FileSystemType', '')
            } for backup in response['Backups']]
            
            return {"status": "success", "backups": backups}
        except ClientError as e:
            logger.error(f"Error listing FSx backups: {e}")
            return {"status": "error", "message": str(e)}
