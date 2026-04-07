# S3AI - AWS Security Analysis and Resource Management Assistant

S3AI is an intelligent AWS assistant that provides enhanced security analysis and resource management capabilities through conversational AI. It leverages OpenAI's language models(tested with GPT3.5 Turbo or 4.0-mini) and the LangChain framework to help AWS administrators and security professionals analyze their AWS environment, with a special focus on security-related concerns.
Currently limited to AWS S3, EC2 and IAM analysis.
## Features

- **S3 Bucket Security Analysis**:
  - Count public S3 buckets across all regions
  - Inspect the contents of S3 buckets

- **EC2 Instance Management**:
  - Discover EC2 instances across all regions
  - Check EC2 instance sizes and specifications
  - Get information about EC2 instances

- **IAM User Permissions Analysis**:
  - Check permissions assigned to IAM user

- **Multi-Region Support**:
  - Automatically discover AWS resources across all available regions

## Prerequisites

- Python 3.10+
- AWS account with appropriate permissions
- OpenAI API key

## Installation

1. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your AWS and OpenAI credentials:
   ```
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   AWS_SESSION_TOKEN=your_session_token_if_using_temporary_credentials
   AWS_REGION=default_region_e.g._us-east-1
   OPENAI_API_KEY=your_openai_api_key
   ```

## Sample Output

Note: Screenshots provided under the screenshot folder for each question!
```
(.venv) ayyappan@iyapun-ubuntu:~/Documents/GitHub/S3AI$ /home/ayyappan/Documents/GitHub/S3AI/.venv/bin/python /home/ayyappan/Documents/GitHub/S3AI/main.py
Welcome to the S3AI Chatbot! Ask AI your questions or type 'exit' to quit.
You can ask about your AWS configs now!

You: Who are you?
Bot: I am an AWS assistant that provides information about AWS resources. If you have any questions related to S3 buckets, EC2 instances, or IAM permissions, feel free to ask, and I will use the appropriate tools to provide you with accurate information.

You:  How many S3 buckets are exposed to the public?
Bot: There is 1 public S3 bucket exposed across all AWS regions. The public bucket is named "this-bucket-is-malloc-free" and is located in the us-east-1 region.

You: What data does the S3 bucket this-bucket-is-malloc-free hold?
Bot: The S3 bucket "this-bucket-is-malloc-free" holds the following data:
- ayyappan.txt
- sample.txt
- supersecret.txt

You: What is the size of the EC2 instance with IP 13.218.82.203?
Bot: The EC2 instance with IP address 13.218.82.203 is a t2.micro instance with 1.0 GB of memory and 8 GB of storage for the root volume.

You: What permissions does the user iyapun have?
Bot: The user "iyapun" has the following permissions:
1. AmazonEC2ReadOnlyAccess
2. IAMReadOnlyAccess
3. AmazonS3ReadOnlyAccess

You: What AWS resources do I have?
Bot: Based on the information from AWS tools:
S3 Buckets:
- Region: us-east-1
  - Bucket Name: this-bucket-is-malloc-free- You have 1 EC2 instance deployed in the us-east-1 region with the following details:

EC2 Instances:
- Region: us-east-1
  - Instance ID: i-0a5aa834f03ec3bbb
  - Type: t2.micro
  - State: running
  - Public IP: 13.218.82.203
  - Private IP: 172.31.90.227

If you need more specific details about any of these resources, feel free to ask!

You: Show me all EC2 instances with their public IPs
Bot: I found an EC2 instance in the region us-east-1 with the following details:
- Instance ID: i-0a5aa834f03ec3bbb
- Type: t2.micro
- State: running
- Public IP: 13.218.82.203
- Private IP: 172.31.90.227

This is the only EC2 instance I found with a public IP address.

You: exit
Goodbye!
(.venv) ayyappan@iyapun-ubuntu:~/Documents/GitHub/S3AI$ 
```

## Usage

Run the application:
```
python main.py
```

Once the application starts, you can interact with it by asking questions about your AWS resources!

- "How many S3 buckets are exposed to the public?"
- "What data does the S3 bucket <insert the name of an S3 bucket that has a few files here> hold?"
- "What is the size of the EC2 instance with IP <insert the IP of an EC2 instance in your test account here>?"
- "What permissions does the user <insert an IAM user in the account here> have?"


Bonus Questions

- "What AWS resources do I have?"
- "Show me all EC2 instances with their public IPs"


## Future Work: AWS Security Scanner (Experimental)

Out of curiosity to try and automate security scanning for the whole enviornment, I wrote an experimental addition to this to try and automate the whole thing in one go.

Can be useful to look for unencrypted S3 buckets and more!

The questions it tested with it are as follows

    - "What ports are open on my EC2 instances?"
    - "Perform a security scan of all my AWS resources"

Note: Example output provided in Screenshots folder! 

Lastly, another future development could be to pull in exposed S3 buckets from greyhatwarfare, and have an AI chatbot find sensitive files for me automatically!