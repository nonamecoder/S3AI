from langchain.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field
import json
from typing import Optional

class CountPublicS3BucketsInput(BaseModel):
    region: Optional[str] = Field(default="all", description="The AWS region to scan. If not provided or set to 'all', scans all regions.")

class CountPublicS3Buckets(BaseTool):
    name: str = "CountPublicS3Buckets"
    description: str = "Counts the number of public S3 buckets in one or all AWS regions. If no region is specified, scans all regions."
    args_schema: Optional[type[BaseModel]] = CountPublicS3BucketsInput
    
    def _run(self, region: Optional[str] = "all"):
        """
        Runs the tool to count public S3 buckets in the specified region or all regions.
        Checks both ACLs and bucket policies to determine if a bucket is public.

        Args:
            region (str, optional): The AWS region to scan. If "all", scans all regions.

        Returns:
            str: The count of public S3 buckets or an error message.
        """
        import boto3
        
        # Initialize counters and results
        public_buckets = 0
        public_bucket_names = []
        
        # If scanning all regions, get list of all regions
        if region == "all":
            try:
                ec2_client = boto3.client('ec2', region_name='us-east-1')
                all_regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
            except Exception as e:
                return f"Error retrieving AWS regions: {str(e)}"
        else:
            all_regions = [region]
        
        # Get all buckets
        s3 = boto3.client("s3")
        try:
            response = s3.list_buckets()
            
            for bucket in response["Buckets"]:
                bucket_name = bucket["Name"]
                try:
                    # Check bucket location to filter by region
                    bucket_location = s3.get_bucket_location(Bucket=bucket_name)
                    bucket_region = bucket_location["LocationConstraint"]
                    
                    # AWS returns None for us-east-1
                    if bucket_region is None:
                        bucket_region = "us-east-1"
                        
                    # Skip if not in our regions list
                    if region != "all" and bucket_region != region:
                        continue

                    is_public = False
                    
                    # Check 1: ACL method
                    try:
                        acl = s3.get_bucket_acl(Bucket=bucket_name)
                        for grant in acl["Grants"]:
                            grantee = grant.get("Grantee", {})
                            if grant["Permission"] in ["READ", "WRITE", "READ_ACP", "WRITE_ACP", "FULL_CONTROL"]:
                                if grantee.get("Type") == "Group" and "AllUsers" in grantee.get("URI", ""):
                                    is_public = True
                                    break
                    except Exception as acl_err:
                        print(f"Error checking ACL for {bucket_name}: {acl_err}")
                    
                    # Check 2: Bucket Policy method
                    if not is_public:
                        try:
                            policy = s3.get_bucket_policy(Bucket=bucket_name)
                            policy_str = policy.get("Policy", "{}")
                            policy_json = json.loads(policy_str)
                            
                            # Check for public access in policy
                            for statement in policy_json.get("Statement", []):
                                principal = statement.get("Principal", {})
                                if principal == "*" or principal.get("AWS") == "*":
                                    if statement.get("Effect") == "Allow":
                                        is_public = True
                                        break
                                        
                        except s3.exceptions.NoSuchBucketPolicy:
                            # No policy is fine, just continue
                            pass
                        except Exception as policy_err:
                            print(f"Error checking policy for {bucket_name}: {policy_err}")
                    
                    # Check 3: Public access block settings
                    try:
                        public_access = s3.get_public_access_block(Bucket=bucket_name)
                        block_settings = public_access.get("PublicAccessBlockConfiguration", {})
                        
                        # If any of these are False, the bucket could be public
                        if not all([
                            block_settings.get("BlockPublicAcls", False),
                            block_settings.get("IgnorePublicAcls", False), 
                            block_settings.get("BlockPublicPolicy", False),
                            block_settings.get("RestrictPublicBuckets", False)
                        ]):
                            # This alone doesn't make it public, but combined with earlier checks
                            if is_public:
                                public_buckets += 1
                                public_bucket_names.append(f"{bucket_name} ({bucket_region})")
                                
                    except Exception as block_err:
                        # If we can't check block settings but already know it's public
                        if is_public:
                            public_buckets += 1
                            public_bucket_names.append(f"{bucket_name} ({bucket_region})")
                            
                except Exception as e:
                    print(f"Error checking bucket {bucket_name}: {str(e)}")
            
            # Format the results
            if region == "all":
                result = f"There are {public_buckets} public S3 buckets across all AWS regions."
            else:
                result = f"There are {public_buckets} public S3 buckets in the {region} region."
                
            if public_buckets > 0:
                result += f" Public buckets: {', '.join(public_bucket_names)}"
                
            return result
            
        except Exception as e:
            return f"Error counting public S3 buckets: {str(e)}"
