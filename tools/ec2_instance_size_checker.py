from langchain.tools import BaseTool
import boto3
import json
from typing import Dict, Union, Optional

class EC2InstanceSizeChecker(BaseTool):
    name: str = "EC2InstanceSizeChecker"
    description: str = "Checks the instance type and size of an EC2 instance given its IP address. Use 'details: true' for full information."
    
    def _run(self, ip_address: str, details: bool = False) -> str:
        """
        Checks the instance type and size of an EC2 instance given its IP address.
        
        Args:
            ip_address (str): The IP address of the EC2 instance to check.
            details (bool, optional): Whether to return detailed information about the instance. Default is False.
            
        Returns:
            str: Information about the EC2 instance or an error message.
        """
        if not ip_address:
            return "Error: IP address is required."

        ec2 = boto3.client("ec2")
        try:
            # Try both private and public IP address filters
            private_response = ec2.describe_instances(
                Filters=[{"Name": "private-ip-address", "Values": [ip_address]}]
            )
            
            # Check if we found an instance with the private IP
            instance_found = False
            instance_type = None
            instance_id = None
            instance_info = {}
            
            for reservation in private_response.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instance_found = True
                    instance_type = instance.get("InstanceType")
                    instance_id = instance.get("InstanceId")
                    instance_info = instance
                    break
                if instance_found:
                    break
                    
            # If not found by private IP, try public IP
            if not instance_found:
                public_response = ec2.describe_instances(
                    Filters=[{"Name": "ip-address", "Values": [ip_address]}]
                )
                
                for reservation in public_response.get("Reservations", []):
                    for instance in reservation.get("Instances", []):
                        instance_found = True
                        instance_type = instance.get("InstanceType")
                        instance_id = instance.get("InstanceId")
                        instance_info = instance
                        break
                    if instance_found:
                        break
            
            if instance_found:
                # Get EBS volume information
                storage_info = []
                root_device_name = instance_info.get("RootDeviceName", "")
                
                # Process block device mappings
                for block_device in instance_info.get("BlockDeviceMappings", []):
                    device_name = block_device.get("DeviceName", "")
                    ebs_info = block_device.get("Ebs", {})
                    volume_id = ebs_info.get("VolumeId", "")
                    
                    if volume_id:
                        # Get detailed volume info
                        try:
                            volume_response = ec2.describe_volumes(VolumeIds=[volume_id])
                            for volume in volume_response.get("Volumes", []):
                                size_gb = volume.get("Size", 0)
                                volume_type = volume.get("VolumeType", "")
                                iops = volume.get("Iops", "N/A")
                                
                                is_root = "(Root)" if device_name == root_device_name else ""
                                storage_info.append(f"{device_name} {is_root}: {size_gb} GB ({volume_type}, IOPS: {iops})")
                        except Exception as vol_err:
                            storage_info.append(f"{device_name}: Error retrieving volume details")
                
                # Get instance type memory information dynamically from AWS
                try:
                    instance_type_response = ec2.describe_instance_types(InstanceTypes=[instance_type])
                    if instance_type_response.get('InstanceTypes'):
                        instance_info_details = instance_type_response['InstanceTypes'][0]
                        memory_info = instance_info_details.get('MemoryInfo', {})
                        memory_size_mib = memory_info.get('SizeInMiB')
                        if memory_size_mib:
                            memory = f"{memory_size_mib/1024:.1f} GB"
                        else:
                            memory = "Memory information unavailable"
                    else:
                        memory = "Memory information unavailable"
                except Exception as mem_err:
                    memory = f"Unable to retrieve memory information: {str(mem_err)}"
                
                # Format the results
                result = f"EC2 instance {instance_id} with IP {ip_address}:\n"
                result += f"- Type: {instance_type}\n"
                result += f"- Memory: {memory}\n"
                result += f"- Storage:\n"
                
                if storage_info:
                    for storage in storage_info:
                        result += f"  • {storage}\n"
                else:
                    result += "  • No storage information available\n"
                
                return result
            else:
                return f"No EC2 instance found with IP address {ip_address}"
                
        except Exception as e:
            return f"Error retrieving EC2 instance details: {str(e)}"
