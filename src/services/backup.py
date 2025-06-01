#!/usr/bin/env python3
import logging
from botocore.exceptions import ClientError
from .base import BaseService

logger = logging.getLogger('aws-storage-mcp')

class BackupService(BaseService):
    """Handler for AWS Backup operations"""
    
    def list_backup_vaults(self):
        """List all AWS Backup vaults"""
        try:
            backup_client = self._get_client('backup')
            response = backup_client.list_backup_vaults()
            
            vaults = [{
                "name": vault['BackupVaultName'],
                "arn": vault['BackupVaultArn'],
                "creation_date": vault['CreationDate'].isoformat()
            } for vault in response['BackupVaultList']]
            
            return {"status": "success", "backup_vaults": vaults}
        except ClientError as e:
            logger.error(f"Error listing AWS Backup vaults: {e}")
            return {"status": "error", "message": str(e)}
    
    def list_backup_plans(self):
        """List all AWS Backup plans"""
        try:
            backup_client = self._get_client('backup')
            response = backup_client.list_backup_plans()
            
            plans = [{
                "id": plan['BackupPlanId'],
                "name": plan['BackupPlanName'],
                "arn": plan['BackupPlanArn'],
                "creation_date": plan['CreationDate'].isoformat(),
                "version_id": plan['VersionId']
            } for plan in response['BackupPlansList']]
            
            return {"status": "success", "backup_plans": plans}
        except ClientError as e:
            logger.error(f"Error listing AWS Backup plans: {e}")
            return {"status": "error", "message": str(e)}
    
    def list_recovery_points(self, backup_vault_name):
        """List recovery points in an AWS Backup vault"""
        try:
            backup_client = self._get_client('backup')
            response = backup_client.list_recovery_points_by_backup_vault(BackupVaultName=backup_vault_name)
            
            recovery_points = [{
                "arn": point['RecoveryPointArn'],
                "resource_type": point['ResourceType'],
                "status": point['Status'],
                "creation_date": point['CreationDate'].isoformat(),
                "backup_size_in_bytes": point.get('BackupSizeInBytes', 0),
                "resource_arn": point.get('ResourceArn', '')
            } for point in response['RecoveryPoints']]
            
            return {"status": "success", "recovery_points": recovery_points}
        except ClientError as e:
            logger.error(f"Error listing recovery points for vault {backup_vault_name}: {e}")
            return {"status": "error", "message": str(e)}
