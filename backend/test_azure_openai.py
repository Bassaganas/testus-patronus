import os
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables
load_dotenv()

# Initialize the Azure OpenAI client
client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)

def test_connection():
    try:
        # Test the connection with a simple query
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant.",
                },
                {
                    "role": "user",
                    "content": "Hello! Can you confirm that the connection is working?",
                }
            ],
            max_tokens=100,
            temperature=0.7,
            top_p=1.0,
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        )
        
        print("Connection successful!")
        print("Response:", response.choices[0].message.content)
        return True
    except Exception as e:
        print("Connection failed!")
        print("Error:", str(e))
        return False

if __name__ == "__main__":
    test_connection() 