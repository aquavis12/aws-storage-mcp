#!/usr/bin/env python3
import json
import os
import sys
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('aws-storage-mcp')

# Import services
from services import (
    BaseService,
    S3Service,
    EBSService,
    EFSService,
    FSxService,
    StorageGatewayService,
    GlacierService,
    SnowService,
    BackupService,
    S3ObjectLambdaService
)

class MCPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MCP server"""
    
    def __init__(self, *args, **kwargs):
        # Initialize service handlers
        self.base_service = BaseService()
        self.s3_service = S3Service()
        self.ebs_service = EBSService()
        self.efs_service = EFSService()
        self.fsx_service = FSxService()
        self.storage_gateway_service = StorageGatewayService()
        self.glacier_service = GlacierService()
        self.snow_service = SnowService()
        self.backup_service = BackupService()
        self.s3_object_lambda_service = S3ObjectLambdaService()
        
        super().__init__(*args, **kwargs)
    
    def _send_response(self, status_code, response_data):
        """Send HTTP response with JSON data"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode('utf-8'))
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Simple health check endpoint
            if self.path == '/health':
                self._send_response(200, {"status": "success", "message": "Server is running"})
                return
                
            # API documentation endpoint
            if self.path == '/api' or self.path == '/api/':
                api_docs = {
                    "status": "success",
                    "server": "AWS Storage MCP Server",
                    "version": "1.0.0",
                    "endpoints": {
                        "/": "Main API endpoint (POST requests)",
                        "/health": "Health check endpoint (GET request)",
                        "/api": "API documentation (GET request)"
                    },
                    "supported_services": [
                        "Amazon S3",
                        "Amazon EBS",
                        "Amazon EFS",
                        "Amazon FSx",
                        "AWS Storage Gateway",
                        "Amazon S3 Glacier",
                        "AWS Snow Family",
                        "AWS Backup",
                        "Amazon S3 Object Lambda",
                        "Amazon S3 Glacier Deep Archive"
                    ]
                }
                self._send_response(200, api_docs)
                return
                
            # Handle unknown GET paths
            self._send_response(404, {"status": "error", "message": f"Endpoint not found: {self.path}"})
            
        except Exception as e:
            logger.error(f"Error processing GET request: {e}")
            self._send_response(500, {"status": "error", "message": str(e)})
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
    def _set_profile_for_all_services(self, profile_name):
        """Set the AWS profile for all service handlers"""
        result = self.base_service.set_profile(profile_name)
        if result['status'] == 'success':
            self.s3_service.profile_name = profile_name
            self.ebs_service.profile_name = profile_name
            self.efs_service.profile_name = profile_name
            self.fsx_service.profile_name = profile_name
            self.storage_gateway_service.profile_name = profile_name
            self.glacier_service.profile_name = profile_name
            self.snow_service.profile_name = profile_name
            self.backup_service.profile_name = profile_name
            self.s3_object_lambda_service.profile_name = profile_name
        return result
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            request = json.loads(post_data)
            action = request.get('action')
            params = request.get('params', {})
            
            logger.info(f"Received request: {action} with params: {params}")
            
            # Set AWS profile if provided
            if 'profile_name' in params:
                profile_result = self._set_profile_for_all_services(params['profile_name'])
                if profile_result['status'] == 'error':
                    self._send_response(400, profile_result)
                    return
            
            # Route to appropriate handler method
            if action == 'list_aws_profiles':
                result = self.base_service.list_aws_profiles()
            elif action == 'set_profile':
                result = self._set_profile_for_all_services(params.get('profile_name'))
            
            # S3 operations
            elif action == 's3_list_buckets':
                result = self.s3_service.list_buckets()
            elif action == 's3_list_objects':
                result = self.s3_service.list_objects(params.get('bucket_name'), params.get('prefix', ''))
            elif action == 's3_get_bucket_location':
                result = self.s3_service.get_bucket_location(params.get('bucket_name'))
            elif action == 's3_get_bucket_policy':
                result = self.s3_service.get_bucket_policy(params.get('bucket_name'))
            elif action == 's3_get_bucket_versioning':
                result = self.s3_service.get_bucket_versioning(params.get('bucket_name'))
            elif action == 's3_get_object_acl':
                result = self.s3_service.get_object_acl(params.get('bucket_name'), params.get('object_key'))
            elif action == 's3_create_bucket':
                result = self.s3_service.create_bucket(params.get('bucket_name'))
            elif action == 's3_delete_bucket':
                result = self.s3_service.delete_bucket(params.get('bucket_name'))
            
            # EBS operations
            elif action == 'ebs_list_volumes':
                result = self.ebs_service.list_volumes()
            elif action == 'ebs_create_volume':
                result = self.ebs_service.create_volume(
                    params.get('size'), 
                    params.get('volume_type', 'gp3'),
                    params.get('availability_zone')
                )
            elif action == 'ebs_delete_volume':
                result = self.ebs_service.delete_volume(params.get('volume_id'))
            elif action == 'ebs_create_snapshot':
                result = self.ebs_service.create_snapshot(
                    params.get('volume_id'),
                    params.get('description', '')
                )
            elif action == 'ebs_list_snapshots':
                result = self.ebs_service.list_snapshots(params.get('owner_id', 'self'))
            
            # EFS operations
            elif action == 'efs_list_filesystems':
                result = self.efs_service.list_filesystems()
            elif action == 'efs_create_filesystem':
                result = self.efs_service.create_filesystem(params.get('name'))
            elif action == 'efs_delete_filesystem':
                result = self.efs_service.delete_filesystem(params.get('filesystem_id'))
            elif action == 'efs_create_mount_target':
                result = self.efs_service.create_mount_target(
                    params.get('filesystem_id'),
                    params.get('subnet_id'),
                    params.get('security_groups')
                )
            elif action == 'efs_list_mount_targets':
                result = self.efs_service.list_mount_targets(params.get('filesystem_id'))
            
            # FSx operations
            elif action == 'fsx_list_filesystems':
                result = self.fsx_service.list_filesystems()
            elif action == 'fsx_describe_filesystem':
                result = self.fsx_service.describe_filesystem(params.get('filesystem_id'))
            elif action == 'fsx_create_backup':
                result = self.fsx_service.create_backup(
                    params.get('filesystem_id'),
                    params.get('backup_name')
                )
            elif action == 'fsx_list_backups':
                result = self.fsx_service.list_backups()
            
            # Storage Gateway operations
            elif action == 'storage_gateway_list_gateways':
                result = self.storage_gateway_service.list_gateways()
            elif action == 'storage_gateway_list_volumes':
                result = self.storage_gateway_service.list_volumes(params.get('gateway_id'))
            elif action == 'storage_gateway_describe_gateway':
                result = self.storage_gateway_service.describe_gateway(params.get('gateway_id'))
            elif action == 'storage_gateway_list_file_shares':
                result = self.storage_gateway_service.list_file_shares(params.get('gateway_id'))
            
            # Glacier operations
            elif action == 'glacier_list_vaults':
                result = self.glacier_service.list_vaults()
            elif action == 'glacier_create_vault':
                result = self.glacier_service.create_vault(params.get('vault_name'))
            elif action == 'glacier_delete_vault':
                result = self.glacier_service.delete_vault(params.get('vault_name'))
            elif action == 'glacier_describe_vault':
                result = self.glacier_service.describe_vault(params.get('vault_name'))
            elif action == 'glacier_initiate_job':
                result = self.glacier_service.initiate_job(
                    params.get('vault_name'),
                    params.get('job_type'),
                    params.get('description', '')
                )
            elif action == 'glacier_list_jobs':
                result = self.glacier_service.list_jobs(params.get('vault_name'))
            elif action == 'glacier_deep_archive_list_vaults':
                result = self.glacier_service.list_deep_archive_vaults()
            
            # Snow Family operations
            elif action == 'snow_list_jobs':
                result = self.snow_service.list_jobs()
            elif action == 'snow_describe_job':
                result = self.snow_service.describe_job(params.get('job_id'))
            elif action == 'snow_list_clusters':
                result = self.snow_service.list_clusters()
            
            # AWS Backup operations
            elif action == 'backup_list_backup_vaults':
                result = self.backup_service.list_backup_vaults()
            elif action == 'backup_list_backup_plans':
                result = self.backup_service.list_backup_plans()
            elif action == 'backup_list_recovery_points':
                result = self.backup_service.list_recovery_points(params.get('backup_vault_name'))
            
            # S3 Object Lambda operations
            elif action == 's3_object_lambda_list_access_points':
                result = self.s3_object_lambda_service.list_access_points()
            
            else:
                result = {"status": "error", "message": f"Unknown action: {action}"}
            
            self._send_response(200, result)
        except json.JSONDecodeError:
            self._send_response(400, {"status": "error", "message": "Invalid JSON"})
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            self._send_response(500, {"status": "error", "message": str(e)})


def run_server(host='localhost', port=8080):
    """Run the MCP server"""
    server_address = (host, port)
    httpd = HTTPServer(server_address, MCPRequestHandler)
    logger.info(f"Starting AWS Storage MCP server on {host}:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    # Get host and port from command line arguments if provided
    host = 'localhost'
    port = 8080
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    
    run_server(host, port)
