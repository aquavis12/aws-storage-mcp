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
        # Request confirmation before creating the backup
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="FSx backup",
            params={
                "filesystem_id": filesystem_id,
                "backup_name": backup_name
            }
        )
        
        if confirmation:
            return confirmation
            
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
    def create_replication(self, source_filesystem_id, destination_region=None, deployment_type=None):
        """
        Create FSx replication configuration
        
        Args:
            source_filesystem_id (str): ID of the source FSx file system
            destination_region (str): Destination region for replication (if None, a different region will be selected)
            deployment_type (str): Deployment type for the destination file system (if None, will match source)
        """
        # Request confirmation before creating replication
        params = {
            "source_filesystem_id": source_filesystem_id
        }
        
        if destination_region:
            params["destination_region"] = destination_region
        if deployment_type:
            params["deployment_type"] = deployment_type
            
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="FSx replication",
            params=params
        )
        
        if confirmation:
            return confirmation
            
        try:
            fsx_client = self._get_client('fsx')
            
            # Get source file system details
            source_response = fsx_client.describe_file_systems(FileSystemIds=[source_filesystem_id])
            
            if not source_response['FileSystems']:
                return {"status": "error", "message": f"FSx file system {source_filesystem_id} not found"}
                
            source_fs = source_response['FileSystems'][0]
            
            # Check if file system type supports replication
            if source_fs['FileSystemType'] not in ['WINDOWS', 'LUSTRE', 'ONTAP']:
                return {"status": "error", "message": f"FSx file system type {source_fs['FileSystemType']} does not support replication"}
            
            # Determine destination region if not provided
            if not destination_region:
                # Get current region
                source_region = self.region
                
                # Choose a different region for replication
                regions = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'eu-west-1']
                destination_region = next((r for r in regions if r != source_region), 'us-west-2')
            
            # Create replication configuration based on file system type
            if source_fs['FileSystemType'] == 'WINDOWS':
                # For Windows File Server
                response = fsx_client.create_file_system_from_backup(
                    BackupId=self._create_backup_for_replication(source_filesystem_id, "ReplicationBackup"),
                    FileSystemType='WINDOWS',
                    StorageType=source_fs.get('StorageType', 'SSD'),
                    StorageCapacity=source_fs['StorageCapacity'],
                    SubnetIds=[source_fs['SubnetIds'][0]],  # Use first subnet ID
                    SecurityGroupIds=source_fs.get('SecurityGroupIds', []),
                    WindowsConfiguration={
                        'ThroughputCapacity': source_fs.get('WindowsConfiguration', {}).get('ThroughputCapacity', 8),
                        'ActiveDirectoryId': source_fs.get('WindowsConfiguration', {}).get('ActiveDirectoryId', '')
                    },
                    Tags=[
                        {'Key': 'Name', 'Value': f"Replica-{source_filesystem_id}"},
                        {'Key': 'ReplicaOf', 'Value': source_filesystem_id}
                    ]
                )
                
                replica_id = response['FileSystem']['FileSystemId']
                
            elif source_fs['FileSystemType'] == 'LUSTRE':
                # For Lustre
                lustre_config = source_fs.get('LustreConfiguration', {})
                
                # Use provided deployment type or match source
                if not deployment_type:
                    deployment_type = lustre_config.get('DeploymentType', 'SCRATCH_1')
                
                response = fsx_client.create_file_system(
                    FileSystemType='LUSTRE',
                    StorageCapacity=source_fs['StorageCapacity'],
                    SubnetIds=[source_fs['SubnetIds'][0]],  # Use first subnet ID
                    SecurityGroupIds=source_fs.get('SecurityGroupIds', []),
                    LustreConfiguration={
                        'DeploymentType': deployment_type,
                        'PerUnitStorageThroughput': lustre_config.get('PerUnitStorageThroughput', 50),
                        'CopyTagsToBackups': True
                    },
                    Tags=[
                        {'Key': 'Name', 'Value': f"Replica-{source_filesystem_id}"},
                        {'Key': 'ReplicaOf', 'Value': source_filesystem_id}
                    ]
                )
                
                replica_id = response['FileSystem']['FileSystemId']
                
            elif source_fs['FileSystemType'] == 'ONTAP':
                # For NetApp ONTAP
                ontap_config = source_fs.get('OntapConfiguration', {})
                
                response = fsx_client.create_file_system(
                    FileSystemType='ONTAP',
                    StorageCapacity=source_fs['StorageCapacity'],
                    SubnetIds=source_fs['SubnetIds'],
                    SecurityGroupIds=source_fs.get('SecurityGroupIds', []),
                    OntapConfiguration={
                        'DeploymentType': ontap_config.get('DeploymentType', 'MULTI_AZ_1'),
                        'ThroughputCapacity': ontap_config.get('ThroughputCapacity', 128),
                        'PreferredSubnetId': source_fs['SubnetIds'][0]
                    },
                    Tags=[
                        {'Key': 'Name', 'Value': f"Replica-{source_filesystem_id}"},
                        {'Key': 'ReplicaOf', 'Value': source_filesystem_id}
                    ]
                )
                
                replica_id = response['FileSystem']['FileSystemId']
            
            return {
                "status": "success",
                "source_filesystem_id": source_filesystem_id,
                "replica_filesystem_id": replica_id,
                "destination_region": destination_region,
                "message": f"FSx replication created successfully with replica file system {replica_id}"
            }
        except ClientError as e:
            logger.error(f"Error creating FSx replication for {source_filesystem_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def _create_backup_for_replication(self, filesystem_id, backup_name):
        """Create a backup for replication and return the backup ID"""
        try:
            fsx_client = self._get_client('fsx')
            response = fsx_client.create_backup(
                FileSystemId=filesystem_id,
                Tags=[
                    {
                        'Key': 'Name',
                        'Value': backup_name
                    },
                    {
                        'Key': 'Purpose',
                        'Value': 'Replication'
                    }
                ]
            )
            
            backup_id = response['Backup']['BackupId']
            
            # Wait for backup to complete
            waiter = fsx_client.get_waiter('backup_available')
            waiter.wait(BackupIds=[backup_id])
            
            return backup_id
        except ClientError as e:
            logger.error(f"Error creating backup for replication of {filesystem_id}: {e}")
            raise
    
    def delete_replication(self, replica_filesystem_id):
        """Delete an FSx replica file system"""
        try:
            fsx_client = self._get_client('fsx')
            fsx_client.delete_file_system(FileSystemId=replica_filesystem_id)
            return {"status": "success", "message": f"FSx replica file system {replica_filesystem_id} deletion initiated"}
        except ClientError as e:
            logger.error(f"Error deleting FSx replica {replica_filesystem_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def list_replicas(self, source_filesystem_id=None):
        """List FSx replicas, optionally filtered by source file system ID"""
        try:
            fsx_client = self._get_client('fsx')
            response = fsx_client.describe_file_systems()
            
            # Filter for replicas based on tags
            replicas = []
            for fs in response['FileSystems']:
                # Check if this is a replica
                is_replica = False
                replica_of = None
                
                for tag in fs.get('Tags', []):
                    if tag['Key'] == 'ReplicaOf':
                        is_replica = True
                        replica_of = tag['Value']
                        break
                
                # If source_filesystem_id is provided, filter by it
                if is_replica and (not source_filesystem_id or replica_of == source_filesystem_id):
                    replicas.append({
                        "id": fs['FileSystemId'],
                        "source_filesystem_id": replica_of,
                        "type": fs['FileSystemType'],
                        "storage_capacity": fs['StorageCapacity'],
                        "lifecycle": fs['Lifecycle'],
                        "region": self.region
                    })
            
            return {"status": "success", "replicas": replicas}
        except ClientError as e:
            logger.error(f"Error listing FSx replicas: {e}")
            return {"status": "error", "message": str(e)}
