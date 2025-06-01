#!/usr/bin/env python3
import os
import logging
import configparser
import boto3
from botocore.exceptions import ClientError, ProfileNotFound

logger = logging.getLogger('aws-storage-mcp')

class BaseService:
    """Base class for AWS Storage services"""
    
    def __init__(self, profile_name=None):
        self.region = os.environ.get('AWS_REGION', 'us-east-1')
        self.profile_name = profile_name
    
    def _get_client(self, service_name):
        """Create and return a boto3 client for the specified service"""
        if self.profile_name:
            session = boto3.Session(profile_name=self.profile_name)
            return session.client(service_name, region_name=self.region)
        return boto3.client(service_name, region_name=self.region)
    
    def _get_resource(self, service_name):
        """Create and return a boto3 resource for the specified service"""
        if self.profile_name:
            session = boto3.Session(profile_name=self.profile_name)
            return session.resource(service_name, region_name=self.region)
        return boto3.resource(service_name, region_name=self.region)
    
    def list_aws_profiles(self):
        """List all available AWS profiles"""
        try:
            # Check for AWS credentials file
            credentials_path = os.path.expanduser("~/.aws/credentials")
            config_path = os.path.expanduser("~/.aws/config")
            
            profiles = set()
            
            # Read profiles from credentials file
            if os.path.exists(credentials_path):
                config = configparser.ConfigParser()
                config.read(credentials_path)
                profiles.update([section.replace("profile ", "") if section.startswith("profile ") else section 
                               for section in config.sections()])
            
            # Read profiles from config file
            if os.path.exists(config_path):
                config = configparser.ConfigParser()
                config.read(config_path)
                profiles.update([section.replace("profile ", "") if section.startswith("profile ") else section 
                               for section in config.sections()])
            
            return {"status": "success", "profiles": list(profiles)}
        except Exception as e:
            logger.error(f"Error listing AWS profiles: {e}")
            return {"status": "error", "message": str(e)}
    
    def set_profile(self, profile_name):
        """Set the AWS profile to use for subsequent operations"""
        try:
            # Test if profile exists
            session = boto3.Session(profile_name=profile_name)
            # If we get here, profile exists
            self.profile_name = profile_name
            return {"status": "success", "message": f"AWS profile set to {profile_name}"}
        except ProfileNotFound as e:
            logger.error(f"AWS profile not found: {profile_name}")
            return {"status": "error", "message": f"AWS profile not found: {profile_name}"}
        except Exception as e:
            logger.error(f"Error setting AWS profile: {e}")
            return {"status": "error", "message": str(e)}
