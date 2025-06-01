#!/usr/bin/env python3
import json
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
    def create_backup_vault(self, vault_name, encryption_key_arn=None, tags=None):
        """
        Create a new AWS Backup vault
        
        Args:
            vault_name (str): Name of the backup vault
            encryption_key_arn (str): ARN of the KMS key for encryption
            tags (dict): Tags to apply to the backup vault
        """
        # Request confirmation before creating backup vault
        params = {
            "vault_name": vault_name
        }
        if encryption_key_arn:
            params["encryption_key_arn"] = encryption_key_arn
            
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="AWS Backup vault",
            params=params
        )
        
        if confirmation:
            return confirmation
            
        try:
            backup_client = self._get_client('backup')
            
            create_params = {
                'BackupVaultName': vault_name
            }
            
            if encryption_key_arn:
                create_params['EncryptionKeyArn'] = encryption_key_arn
                
            if tags:
                create_params['BackupVaultTags'] = tags
            
            response = backup_client.create_backup_vault(**create_params)
            
            return {
                "status": "success",
                "vault_name": vault_name,
                "vault_arn": response.get('BackupVaultArn', ''),
                "message": f"Backup vault {vault_name} created successfully"
            }
        except ClientError as e:
            logger.error(f"Error creating backup vault {vault_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_backup_vault(self, vault_name):
        """Delete an AWS Backup vault"""
        try:
            backup_client = self._get_client('backup')
            backup_client.delete_backup_vault(BackupVaultName=vault_name)
            return {"status": "success", "message": f"Backup vault {vault_name} deleted successfully"}
        except ClientError as e:
            logger.error(f"Error deleting backup vault {vault_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def create_backup_plan(self, plan_name, backup_rules):
        """
        Create a new AWS Backup plan
        
        Args:
            plan_name (str): Name of the backup plan
            backup_rules (list): List of backup rules
        """
        # Request confirmation before creating backup plan
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="AWS Backup plan",
            params={
                "plan_name": plan_name,
                "rules_count": len(backup_rules)
            }
        )
        
        if confirmation:
            return confirmation
            
        try:
            backup_client = self._get_client('backup')
            
            # Format the backup plan
            backup_plan = {
                'BackupPlanName': plan_name,
                'Rules': backup_rules
            }
            
            response = backup_client.create_backup_plan(
                BackupPlan=backup_plan,
                BackupPlanTags={'Name': plan_name}
            )
            
            return {
                "status": "success",
                "plan_id": response['BackupPlanId'],
                "plan_arn": response['BackupPlanArn'],
                "plan_version": response['VersionId'],
                "message": f"Backup plan {plan_name} created successfully"
            }
        except ClientError as e:
            logger.error(f"Error creating backup plan {plan_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_backup_plan(self, plan_id):
        """Delete an AWS Backup plan"""
        try:
            backup_client = self._get_client('backup')
            backup_client.delete_backup_plan(BackupPlanId=plan_id)
            return {"status": "success", "message": f"Backup plan {plan_id} deleted successfully"}
        except ClientError as e:
            logger.error(f"Error deleting backup plan {plan_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def create_backup_selection(self, plan_id, selection_name, resources, iam_role_arn=None):
        """
        Create a resource selection for an AWS Backup plan
        
        Args:
            plan_id (str): ID of the backup plan
            selection_name (str): Name of the selection
            resources (list): List of resource ARNs to back up
            iam_role_arn (str): ARN of the IAM role for AWS Backup
        """
        # Request confirmation before creating backup selection
        confirmation = self._request_confirmation(
            operation_type="create",
            resource_type="AWS Backup selection",
            params={
                "plan_id": plan_id,
                "selection_name": selection_name,
                "resources_count": len(resources)
            }
        )
        
        if confirmation:
            return confirmation
            
        try:
            backup_client = self._get_client('backup')
            
            # If no IAM role ARN provided, create or get a default one
            if not iam_role_arn:
                iam_role_arn = self._get_or_create_backup_role()
            
            # Format the backup selection
            backup_selection = {
                'SelectionName': selection_name,
                'IamRoleArn': iam_role_arn,
                'Resources': resources
            }
            
            response = backup_client.create_backup_selection(
                BackupPlanId=plan_id,
                BackupSelection=backup_selection
            )
            
            return {
                "status": "success",
                "selection_id": response['SelectionId'],
                "message": f"Backup selection {selection_name} created successfully for plan {plan_id}"
            }
        except ClientError as e:
            logger.error(f"Error creating backup selection for plan {plan_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_backup_selection(self, plan_id, selection_id):
        """Delete a resource selection from an AWS Backup plan"""
        try:
            backup_client = self._get_client('backup')
            backup_client.delete_backup_selection(
                BackupPlanId=plan_id,
                SelectionId=selection_id
            )
            return {"status": "success", "message": f"Backup selection {selection_id} deleted successfully from plan {plan_id}"}
        except ClientError as e:
            logger.error(f"Error deleting backup selection {selection_id} from plan {plan_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def _get_or_create_backup_role(self):
        """Get or create a default IAM role for AWS Backup"""
        try:
            iam_client = self._get_client('iam')
            role_name = 'AWSBackupDefaultServiceRole'
            
            try:
                # Try to get the role if it exists
                role_response = iam_client.get_role(RoleName=role_name)
                return role_response['Role']['Arn']
            except ClientError:
                # Create the role if it doesn't exist
                trust_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "backup.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }
                    ]
                }
                
                role_response = iam_client.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description='Default role for AWS Backup'
                )
                
                # Attach the AWS Backup service role policy
                iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn='arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup'
                )
                
                return role_response['Role']['Arn']
        except ClientError as e:
            logger.error(f"Error creating default backup role: {e}")
            raise
