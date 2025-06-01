#!/usr/bin/env python3
import logging
from botocore.exceptions import ClientError
from .base import BaseService

logger = logging.getLogger('aws-storage-mcp')

class SnowService(BaseService):
    """Handler for AWS Snow Family operations"""
    
    def list_jobs(self):
        """List all Snow Family jobs"""
        try:
            snow_client = self._get_client('snowball')
            response = snow_client.list_jobs()
            jobs = [{
                "id": job['JobId'],
                "state": job['JobState'],
                "type": job['JobType'],
                "creation_date": job['CreationDate'].isoformat(),
                "description": job.get('Description', ''),
                "snowball_type": job.get('SnowballType', '')
            } for job in response['JobListEntries']]
            return {"status": "success", "jobs": jobs}
        except ClientError as e:
            logger.error(f"Error listing Snow Family jobs: {e}")
            return {"status": "error", "message": str(e)}
    
    def describe_job(self, job_id):
        """Get detailed information about a Snow Family job"""
        try:
            snow_client = self._get_client('snowball')
            response = snow_client.describe_job(JobId=job_id)
            
            job_info = {
                "id": response['JobMetadata']['JobId'],
                "state": response['JobMetadata']['JobState'],
                "type": response['JobMetadata']['JobType'],
                "creation_date": response['JobMetadata']['CreationDate'].isoformat(),
                "description": response['JobMetadata'].get('Description', ''),
                "snowball_type": response['JobMetadata'].get('SnowballType', ''),
                "shipping_option": response['JobMetadata'].get('ShippingOption', ''),
                "snowball_capacity": response['JobMetadata'].get('SnowballCapacityPreference', ''),
                "address_id": response['JobMetadata'].get('AddressId', ''),
                "kms_key_arn": response['JobMetadata'].get('KmsKeyARN', '')
            }
            
            return {"status": "success", "job": job_info}
        except ClientError as e:
            logger.error(f"Error describing Snow Family job {job_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def list_clusters(self):
        """List all Snow Family clusters"""
        try:
            snow_client = self._get_client('snowball')
            response = snow_client.list_clusters()
            
            clusters = [{
                "id": cluster['ClusterId'],
                "state": cluster['ClusterState'],
                "creation_date": cluster['CreationDate'].isoformat(),
                "description": cluster.get('Description', '')
            } for cluster in response['ClusterListEntries']]
            
            return {"status": "success", "clusters": clusters}
        except ClientError as e:
            logger.error(f"Error listing Snow Family clusters: {e}")
            return {"status": "error", "message": str(e)}
