"""
AWS Storage Services package
"""

from .base import BaseService
from .s3 import S3Service
from .ebs import EBSService
from .efs import EFSService
from .fsx import FSxService
from .storage_gateway import StorageGatewayService
from .glacier import GlacierService
from .snow import SnowService
from .backup import BackupService
from .s3_object_lambda import S3ObjectLambdaService

__all__ = [
    'BaseService',
    'S3Service',
    'EBSService',
    'EFSService',
    'FSxService',
    'StorageGatewayService',
    'GlacierService',
    'SnowService',
    'BackupService',
    'S3ObjectLambdaService'
]
