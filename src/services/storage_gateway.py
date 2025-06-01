#!/usr/bin/env python3
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
