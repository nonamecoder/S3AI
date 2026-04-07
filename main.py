import os
# warnings is only used once to suppress DeprecationWarnings
import warnings
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import AgentType, initialize_agent, Tool
from langchain.memory import ConversationBufferMemory
from langchain_core.tools import BaseTool
from langchain.tools import StructuredTool

from tools.count_public_s3_buckets import CountPublicS3Buckets
from tools.s3_bucket_inspector import S3BucketInspector
from tools.ec2_instance_size_checker import EC2InstanceSizeChecker
from tools.iam_user_permission_checker import IAMUserPermissionChecker
from tools.region_discovery import RegionDiscoveryTool

# This could be commented out if DeprecationWarnings aren't problematic
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Load environment variables from .env file if it exists
load_dotenv()

# Set up AWS credentials from environment variables
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")  # optional
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    raise ValueError("AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in the .env file.")

os.environ["AWS_ACCESS_KEY_ID"] = AWS_ACCESS_KEY_ID
os.environ["AWS_SECRET_ACCESS_KEY"] = AWS_SECRET_ACCESS_KEY
if AWS_SESSION_TOKEN:
    os.environ["AWS_SESSION_TOKEN"] = AWS_SESSION_TOKEN
os.environ["AWS_DEFAULT_REGION"] = AWS_REGION

# Set up OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found. Please set it in the .env file.")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Initialize LLM
llm = ChatOpenAI(
    #model_name="gpt-4o-mini",
    model_name="gpt-3.5-turbo",
    temperature=0
)

# Convert LangChain tool classes to regular Tool objects
def convert_to_langchain_tool(tool_instance: BaseTool) -> Tool:
    if tool_instance.__class__.__name__ == "CountPublicS3Buckets":
        # Special handling for CountPublicS3Buckets with optional parameter
        return StructuredTool.from_function(
            func=tool_instance._run,
            name=tool_instance.name,
            description=tool_instance.description,
            args_schema=tool_instance.args_schema,
            return_direct=False
        )
    else:
        # Regular handling for other tools
        return Tool(
            name=tool_instance.name,
            description=tool_instance.description,
            func=tool_instance._run
        )

# Instantiate tools
tool_instances = [
    CountPublicS3Buckets(),
    S3BucketInspector(),
    EC2InstanceSizeChecker(),
    IAMUserPermissionChecker(),
    RegionDiscoveryTool(),
]

# Convert to LangChain tools
tools = [convert_to_langchain_tool(tool) for tool in tool_instances]

# System message for the agent
SYSTEM_MESSAGE = """You are an AWS assistant that provides information about AWS resources.
You have access to tools for checking S3 buckets, EC2 instances, and IAM permissions.
When asked about AWS resources, ALWAYS use the appropriate tool to get accurate information.

For S3 bucket questions:
- Use the RegionDiscoveryTool with 's3' parameter to find regions with S3 buckets.
  Example: "Where do I have S3 buckets deployed?"
- Use the CountPublicS3Buckets tool to check for public S3 buckets. No region parameter is needed as it can scan all regions automatically.
  Example: "How many S3 buckets are exposed to the public across my account?"
- If you want to check a specific region, you can provide a region parameter.
  Example: "How many S3 buckets are exposed to the public in us-east-1?"
- Use the S3BucketInspector tool when asked about the contents of a specific bucket.
  Example: "What data does the S3 bucket example-bucket hold?"

For EC2 questions:
- Use the RegionDiscoveryTool with 'ec2' parameter to find regions with EC2 instances.
  Example: "In which regions do I have EC2 instances?"
- Use the EC2InstanceSizeChecker tool to get information about EC2 instances.
  Example: "What is the size of the EC2 instance with IP 10.0.0.1?"
- When asked for full details about an EC2 instance (type, memory, vCPUs), add 'details: true' parameter
  Example: "Tell me all the details about the EC2 instance with IP 10.0.0.1"

For IAM questions:
- Use the IAMUserPermissionChecker tool to check permissions for IAM users.
  Example: "What permissions does the user admin have?"

Never guess or make up information about the user's AWS resources. Always use the appropriate tool to get accurate data."""

def create_agent():
    # Create conversation memory
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    # Initialize agent with tools
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=False,  # Change from True to False to hide execution traces
        memory=memory,
        handle_parsing_errors=True,
        agent_kwargs={
            "system_message": SYSTEM_MESSAGE
        }
    )
    
    return agent

def main():
    print("Welcome to the S3AI Chatbot! Ask AI your questions or type 'exit' to quit.")
    print("You can ask about your AWS configs now!\n")
    # Create the agent
    agent = create_agent()
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
            
        try:
            # Execute the agent (not using ainvoke since initialize_agent doesn't support it directly)
            response = agent.run(user_input)
            
            # Print the response
            print(f"Bot: {response}\n")
            
        except Exception as e:
            print(f"An error occurred: {e}\n")

if __name__ == "__main__":
    main()
