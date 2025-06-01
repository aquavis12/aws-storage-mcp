#!/usr/bin/env python3
import logging
from botocore.exceptions import ClientError
from .base import BaseService

logger = logging.getLogger('aws-storage-mcp')

class EBSService(BaseService):
    """Handler for Amazon EBS operations"""
    
    def list_volumes(self):
        """List all EBS volumes"""
        try:
            ec2_client = self._get_client('ec2')
            response = ec2_client.describe_volumes()
            volumes = [{
                "id": vol['VolumeId'],
                "size": vol['Size'],
                "state": vol['State'],
                "type": vol['VolumeType'],
                "az": vol['AvailabilityZone'],
                "encrypted": vol['Encrypted'],
                "iops": vol.get('Iops', 0),
                "attachments": [{"instance_id": att['InstanceId'], "state": att['State']} 
                               for att in vol.get('Attachments', [])]
            } for vol in response['Volumes']]
            return {"status": "success", "volumes": volumes}
        except ClientError as e:
            logger.error(f"Error listing EBS volumes: {e}")
            return {"status": "error", "message": str(e)}
    
    def create_volume(self, size, volume_type="gp3", availability_zone=None):
        """Create a new EBS volume"""
        try:
            ec2_client = self._get_client('ec2')
            
            # If no AZ provided, get the first AZ in the region
            if not availability_zone:
                azs = ec2_client.describe_availability_zones()
                availability_zone = azs['AvailabilityZones'][0]['ZoneName']
            
            response = ec2_client.create_volume(
                Size=size,
                VolumeType=volume_type,
                AvailabilityZone=availability_zone
            )
            
            return {
                "status": "success", 
                "volume_id": response['VolumeId'],
                "message": f"Volume {response['VolumeId']} created successfully"
            }
        except ClientError as e:
            logger.error(f"Error creating EBS volume: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_volume(self, volume_id):
        """Delete an EBS volume"""
        try:
            ec2_client = self._get_client('ec2')
            ec2_client.delete_volume(VolumeId=volume_id)
            return {"status": "success", "message": f"Volume {volume_id} deleted successfully"}
        except ClientError as e:
            logger.error(f"Error deleting EBS volume {volume_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def create_snapshot(self, volume_id, description=""):
        """Create a snapshot of an EBS volume"""
        try:
            ec2_client = self._get_client('ec2')
            response = ec2_client.create_snapshot(
                VolumeId=volume_id,
                Description=description
            )
            return {
                "status": "success",
                "snapshot_id": response['SnapshotId'],
                "message": f"Snapshot {response['SnapshotId']} created successfully"
            }
        except ClientError as e:
            logger.error(f"Error creating snapshot for volume {volume_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def list_snapshots(self, owner_id="self"):
        """List EBS snapshots"""
        try:
            ec2_client = self._get_client('ec2')
            response = ec2_client.describe_snapshots(OwnerIds=[owner_id])
            snapshots = [{
                "id": snap['SnapshotId'],
                "volume_id": snap['VolumeId'],
                "state": snap['State'],
                "progress": snap['Progress'],
                "start_time": snap['StartTime'].isoformat(),
                "description": snap.get('Description', '')
            } for snap in response['Snapshots']]
            return {"status": "success", "snapshots": snapshots}
        except ClientError as e:
            logger.error(f"Error listing EBS snapshots: {e}")
            return {"status": "error", "message": str(e)}
