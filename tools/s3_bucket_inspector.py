from langchain.tools import BaseTool
from typing import Optional
import boto3
import json

class S3BucketInspector(BaseTool):
    name: str = "S3BucketInspector"
    description: str = "Inspects the contents of an S3 bucket to determine what type of data it contains."
    
    def _run(self, bucket_name: str) -> str:
        """
        Inspects the contents of an S3 bucket to determine what type of data it contains.
        
        Args:
            bucket_name (str): The name of the S3 bucket to inspect.
            
        Returns:
            str: A description of the bucket contents or an error message.
        """
        try:
            s3 = boto3.client("s3")
            response = s3.list_objects_v2(Bucket=bucket_name)
            if "Contents" in response:
                contents = [obj["Key"] for obj in response["Contents"]]
                return f"Contents of bucket {bucket_name}: {', '.join(contents)}"
            return f"The bucket {bucket_name} is empty."
        except Exception as e:
            return f"Error inspecting S3 bucket: {str(e)}"
