from langchain.tools import BaseTool
import boto3
import json

class IAMUserPermissionChecker(BaseTool):
    name: str = "IAMUserPermissionChecker"
    description: str = "Checks the permissions of an IAM user."
    
    def _run(self, username: str) -> str:
        """
        Checks the permissions of an IAM user.
        
        Args:
            username (str): The name of the IAM user to check.
            
        Returns:
            str: Information about the user's permissions or an error message.
        """
        try:
            iam = boto3.client("iam")
            response = iam.list_attached_user_policies(UserName=username)
            policies = [policy["PolicyName"] for policy in response["AttachedPolicies"]]
            return policies if policies else f"The user {username} has no attached policies."
        except Exception as e:
            return f"Error checking IAM user permissions: {str(e)}"
