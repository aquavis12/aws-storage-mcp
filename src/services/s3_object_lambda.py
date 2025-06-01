#!/usr/bin/env python3
import logging
from botocore.exceptions import ClientError
from .base import BaseService

logger = logging.getLogger('aws-storage-mcp')

class S3ObjectLambdaService(BaseService):
    """Handler for Amazon S3 Object Lambda operations"""
    
    def list_access_points(self):
        """List all S3 Object Lambda Access Points"""
        try:
            s3control_client = self._get_client('s3control')
            sts_client = self._get_client('sts')
            account_id = sts_client.get_caller_identity().get('Account')
            
            response = s3control_client.list_access_points_for_object_lambda(AccountId=account_id)
            
            access_points = [{
                "name": ap['Name'],
                "arn": ap['ObjectLambdaAccessPointArn'],
                "alias": ap.get('Alias', '')
            } for ap in response.get('ObjectLambdaAccessPoints', [])]
            
            return {"status": "success", "object_lambda_access_points": access_points}
        except ClientError as e:
            logger.error(f"Error listing S3 Object Lambda Access Points: {e}")
            return {"status": "error", "message": str(e)}
