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
        # If no AZ provided, get the first AZ in the region
        ec2_client = self._get_client('ec2')
        if not availability_zone:
            azs = ec2_client.describe_availability_zones()
            availability_zone = azs['AvailabilityZones'][0]['ZoneName']
        
        # Request confirmation before creating the volume
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="EBS volume",
            params={
                "size": f"{size} GiB", 
                "volume_type": volume_type,
                "availability_zone": availability_zone
            }
        )
        
        if confirmation:
            return confirmation
            
        try:
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
        # Request confirmation before creating the snapshot
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="EBS snapshot",
            params={
                "volume_id": volume_id,
                "description": description
            }
        )
        
        if confirmation:
            return confirmation
            
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
    def create_volume_replica(self, source_volume_id, destination_az=None):
        """
        Create a replica of an EBS volume in a different Availability Zone
        
        Args:
            source_volume_id (str): ID of the source volume to replicate
            destination_az (str): Destination Availability Zone (if None, a different AZ will be selected)
        """
        # Request confirmation before creating the volume replica
        params = {
            "source_volume_id": source_volume_id
        }
        
        if destination_az:
            params["destination_az"] = destination_az
            
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="EBS volume replica",
            params=params
        )
        
        if confirmation:
            return confirmation
            
        try:
            ec2_client = self._get_client('ec2')
            
            # Get source volume details
            source_volume = ec2_client.describe_volumes(VolumeIds=[source_volume_id])['Volumes'][0]
            source_az = source_volume['AvailabilityZone']
            source_size = source_volume['Size']
            source_type = source_volume['VolumeType']
            source_encrypted = source_volume['Encrypted']
            
            # If no destination AZ provided, select a different one
            if not destination_az:
                azs = ec2_client.describe_availability_zones()['AvailabilityZones']
                available_azs = [az['ZoneName'] for az in azs if az['ZoneName'] != source_az]
                if not available_azs:
                    return {"status": "error", "message": "No alternative Availability Zones available"}
                destination_az = available_azs[0]
            
            # Create a snapshot of the source volume
            snapshot_response = ec2_client.create_snapshot(
                VolumeId=source_volume_id,
                Description=f"Snapshot for volume replica of {source_volume_id}"
            )
            
            snapshot_id = snapshot_response['SnapshotId']
            
            # Wait for the snapshot to complete
            waiter = ec2_client.get_waiter('snapshot_completed')
            waiter.wait(SnapshotIds=[snapshot_id])
            
            # Create a new volume from the snapshot in the destination AZ
            volume_params = {
                'SnapshotId': snapshot_id,
                'AvailabilityZone': destination_az,
                'VolumeType': source_type,
                'Encrypted': source_encrypted
            }
            
            # Add IOPS if needed for io1/io2 volume types
            if source_type in ['io1', 'io2'] and 'Iops' in source_volume:
                volume_params['Iops'] = source_volume['Iops']
            
            # Add throughput if needed for gp3 volume type
            if source_type == 'gp3' and 'Throughput' in source_volume:
                volume_params['Throughput'] = source_volume['Throughput']
            
            # Create the replica volume
            replica_response = ec2_client.create_volume(**volume_params)
            
            # Add tags to the replica volume
            ec2_client.create_tags(
                Resources=[replica_response['VolumeId']],
                Tags=[
                    {'Key': 'ReplicaOf', 'Value': source_volume_id},
                    {'Key': 'Name', 'Value': f"Replica-{source_volume_id}"}
                ]
            )
            
            return {
                "status": "success",
                "source_volume_id": source_volume_id,
                "replica_volume_id": replica_response['VolumeId'],
                "snapshot_id": snapshot_id,
                "destination_az": destination_az,
                "message": f"Volume replica {replica_response['VolumeId']} created successfully"
            }
        except ClientError as e:
            logger.error(f"Error creating EBS volume replica for {source_volume_id}: {e}")
            return {"status": "error", "message": str(e)}
