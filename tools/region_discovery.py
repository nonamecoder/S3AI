from langchain.tools import BaseTool
import boto3
from typing import Optional, List, Dict, Any

class RegionDiscoveryTool(BaseTool):
    name: str = "RegionDiscoveryTool"
    description: str = "Discovers AWS regions where EC2 and S3 resources are deployed."
    
    def _run(self, query: str = "") -> str:
        """
        Discovers AWS regions where EC2 and S3 resources are deployed.
        
        Args:
            query (str): Optional query string (not used, but required for LangChain tool interface)
            
        Returns:
            str: A summary of EC2 and S3 resources found across all regions.
        """
        try:
            # First, get all available AWS regions
            ec2_client = boto3.client('ec2', region_name='us-east-1')  # Use us-east-1 as default for listing regions
            all_regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
            
            # Initialize results storage
            results = {
                's3': {'active_regions': [], 'resource_counts': {}, 'details': {}},
                'ec2': {'active_regions': [], 'resource_counts': {}, 'details': {}}
            }
            
            # Check S3 buckets (global service with regional buckets)
            try:
                s3_client = boto3.client('s3')
                # Get all buckets
                all_buckets = s3_client.list_buckets()
                
                # Group buckets by region
                for bucket in all_buckets.get('Buckets', []):
                    bucket_name = bucket['Name']
                    try:
                        # Get bucket location
                        location = s3_client.get_bucket_location(Bucket=bucket_name)
                        region = location['LocationConstraint']
                        
                        # AWS returns None for us-east-1
                        if region is None:
                            region = 'us-east-1'
                        
                        # Count buckets per region
                        if region in results['s3']['resource_counts']:
                            results['s3']['resource_counts'][region] += 1
                        else:
                            results['s3']['resource_counts'][region] = 1
                            results['s3']['active_regions'].append(region)
                            
                        # Store bucket details
                        if region not in results['s3']['details']:
                            results['s3']['details'][region] = []
                        results['s3']['details'][region].append(bucket_name)
                            
                    except Exception as e:
                        print(f"Error getting location for bucket {bucket_name}: {str(e)}")
            except Exception as e:
                print(f"Error checking S3 resources: {str(e)}")
            
            # Check EC2 instances across all regions
            try:
                for region in all_regions:
                    try:
                        # Create EC2 client for this region
                        ec2_client = boto3.client('ec2', region_name=region)
                        
                        # Get all instances in the region
                        response = ec2_client.describe_instances()
                        reservations = response.get('Reservations', [])
                        
                        # Skip regions with no instances
                        if not reservations:
                            continue
                            
                        # Track instances in this region
                        instances_in_region = []
                        
                        # Extract instance details
                        for reservation in reservations:
                            for instance in reservation.get('Instances', []):
                                instance_id = instance.get('InstanceId')
                                instance_type = instance.get('InstanceType')
                                state = instance.get('State', {}).get('Name')
                                public_ip = instance.get('PublicIpAddress', 'No public IP')
                                private_ip = instance.get('PrivateIpAddress', 'No private IP')
                                
                                # Add instance details to the list
                                instances_in_region.append({
                                    'id': instance_id,
                                    'type': instance_type,
                                    'state': state,
                                    'public_ip': public_ip,
                                    'private_ip': private_ip
                                })
                        
                        # If instances found, save details
                        if instances_in_region:
                            if region not in results['ec2']['details']:
                                results['ec2']['details'][region] = []
                            results['ec2']['details'][region].extend(instances_in_region)
                            results['ec2']['active_regions'].append(region)
                            results['ec2']['resource_counts'][region] = len(instances_in_region)
                            
                    except Exception as e:
                        print(f"Error checking EC2 resources in {region}: {str(e)}")
            except Exception as e:
                print(f"Error checking EC2 resources: {str(e)}")
            
            # Format the final result
            final_result = "AWS Resource Summary:\n\n"
            
            # Add S3 results
            if results['s3']['active_regions']:
                s3_regions = len(results['s3']['active_regions'])
                s3_total = sum(results['s3']['resource_counts'].values())
                final_result += f"S3: Found {s3_total} bucket(s) in {s3_regions} region(s)\n"
                for region in results['s3']['active_regions']:
                    bucket_count = results['s3']['resource_counts'][region]
                    final_result += f"- {region}: {bucket_count} bucket(s)\n"
                    for bucket_name in results['s3']['details'][region]:
                        final_result += f"  * {bucket_name}\n"
            else:
                final_result += "S3: No buckets found in any region\n"
            
            final_result += "\n"
            
            # Add EC2 results
            if results['ec2']['active_regions']:
                ec2_regions = len(results['ec2']['active_regions'])
                ec2_total = sum(results['ec2']['resource_counts'].values())
                final_result += f"EC2: Found {ec2_total} instance(s) in {ec2_regions} region(s)\n"
                for region in results['ec2']['active_regions']:
                    instance_count = results['ec2']['resource_counts'][region]
                    final_result += f"\nRegion: {region} ({instance_count} instance(s))\n"
                    for instance in results['ec2']['details'][region]:
                        final_result += f"- Instance ID: {instance['id']}\n"
                        final_result += f"  Type: {instance['type']}\n"
                        final_result += f"  State: {instance['state']}\n"
                        final_result += f"  Public IP: {instance['public_ip']}\n"
                        final_result += f"  Private IP: {instance['private_ip']}\n"
            else:
                final_result += "EC2: No instances found in any region\n"
            
            return final_result

        except Exception as e:
            return f"Error discovering AWS resources: {str(e)}"