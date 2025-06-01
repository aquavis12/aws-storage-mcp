#!/usr/bin/env python3
import logging
from botocore.exceptions import ClientError
from .base import BaseService

logger = logging.getLogger('aws-storage-mcp')

class GlacierService(BaseService):
    """Handler for Amazon S3 Glacier operations"""
    
    def list_vaults(self):
        """List all Glacier vaults"""
        try:
            glacier_client = self._get_client('glacier')
            response = glacier_client.list_vaults()
            vaults = [{
                "name": vault['VaultName'],
                "arn": vault['VaultARN'],
                "size_bytes": vault['SizeInBytes'],
                "number_of_archives": vault['NumberOfArchives'],
                "creation_date": vault['CreationDate'],
                "last_inventory_date": vault.get('LastInventoryDate', '')
            } for vault in response['VaultList']]
            return {"status": "success", "vaults": vaults}
        except ClientError as e:
            logger.error(f"Error listing Glacier vaults: {e}")
            return {"status": "error", "message": str(e)}
    
    def create_vault(self, vault_name):
        """Create a new Glacier vault"""
        # Request confirmation before creating the vault
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="Glacier vault",
            params={"vault_name": vault_name}
        )
        
        if confirmation:
            return confirmation
            
        try:
            glacier_client = self._get_client('glacier')
            response = glacier_client.create_vault(vaultName=vault_name)
            return {
                "status": "success",
                "location": response['location'],
                "message": f"Glacier vault {vault_name} created successfully"
            }
        except ClientError as e:
            logger.error(f"Error creating Glacier vault {vault_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_vault(self, vault_name):
        """Delete a Glacier vault"""
        try:
            glacier_client = self._get_client('glacier')
            glacier_client.delete_vault(vaultName=vault_name)
            return {"status": "success", "message": f"Glacier vault {vault_name} deleted successfully"}
        except ClientError as e:
            logger.error(f"Error deleting Glacier vault {vault_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def describe_vault(self, vault_name):
        """Get detailed information about a Glacier vault"""
        try:
            glacier_client = self._get_client('glacier')
            response = glacier_client.describe_vault(vaultName=vault_name)
            
            vault_info = {
                "name": response['VaultName'],
                "arn": response['VaultARN'],
                "size_bytes": response['SizeInBytes'],
                "number_of_archives": response['NumberOfArchives'],
                "creation_date": response['CreationDate'],
                "last_inventory_date": response.get('LastInventoryDate', '')
            }
            
            return {"status": "success", "vault": vault_info}
        except ClientError as e:
            logger.error(f"Error describing Glacier vault {vault_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def initiate_job(self, vault_name, job_type, description=""):
        """Initiate a Glacier job (inventory retrieval or archive retrieval)"""
        # Request confirmation before initiating the job
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="Glacier job",
            params={
                "vault_name": vault_name,
                "job_type": job_type,
                "description": description
            }
        )
        
        if confirmation:
            return confirmation
            
        try:
            glacier_client = self._get_client('glacier')
            
            job_parameters = {
                'Type': job_type,
                'Description': description
            }
            
            response = glacier_client.initiate_job(
                vaultName=vault_name,
                jobParameters=job_parameters
            )
            
            return {
                "status": "success",
                "job_id": response['jobId'],
                "message": f"Glacier job {response['jobId']} initiated successfully"
            }
        except ClientError as e:
            logger.error(f"Error initiating Glacier job for vault {vault_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def list_jobs(self, vault_name):
        """List Glacier jobs for a vault"""
        try:
            glacier_client = self._get_client('glacier')
            response = glacier_client.list_jobs(vaultName=vault_name)
            
            jobs = [{
                "id": job['JobId'],
                "type": job['Action'],
                "status": job['StatusCode'],
                "creation_date": job['CreationDate'],
                "completed": job['Completed'],
                "description": job.get('JobDescription', '')
            } for job in response['JobList']]
            
            return {"status": "success", "jobs": jobs}
        except ClientError as e:
            logger.error(f"Error listing Glacier jobs for vault {vault_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def list_deep_archive_vaults(self):
        """List all S3 Glacier Deep Archive vaults"""
        try:
            # S3 Glacier Deep Archive uses the same API as Glacier
            glacier_client = self._get_client('glacier')
            response = glacier_client.list_vaults()
            vaults = [{
                "name": vault['VaultName'],
                "arn": vault['VaultARN'],
                "size_bytes": vault['SizeInBytes'],
                "number_of_archives": vault['NumberOfArchives'],
                "creation_date": vault['CreationDate'],
                "last_inventory_date": vault.get('LastInventoryDate', '')
            } for vault in response['VaultList']]
            return {"status": "success", "vaults": vaults}
        except ClientError as e:
            logger.error(f"Error listing S3 Glacier Deep Archive vaults: {e}")
            return {"status": "error", "message": str(e)}
