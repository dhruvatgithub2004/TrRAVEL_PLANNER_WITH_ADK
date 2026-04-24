import asyncio
import os
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.models.llm_request import LlmRequest
from google.genai.types import Content, Part

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "travel_planner", ".env"))

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if DEEPSEEK_API_KEY:
    os.environ["DEEPSEEK_API_KEY"] = DEEPSEEK_API_KEY

print(f"API Key loaded: {'Yes' if DEEPSEEK_API_KEY else 'No'}")

# Initialize the LLM
llm = LiteLlm(model="deepseek/deepseek-chat")

async def test_agent():
    # Create the conversation contents
    contents = [
        Content(
            role="user",
            parts=[Part(text="Hello, how are you?")]
        )
    ]

    # Create LlmRequest
    llm_request = LlmRequest(
        contents=contents,
        config={"temperature": 0.7, "max_output_tokens": 1000}
    )

    print("Making LLM request...")

    try:
        # Generate response
        response_generator = llm.generate_content_async(llm_request)

        # Extract text from response
        full_response = ""
        async for resp in response_generator:
            print(f"LLM Response object: {type(resp)}")
            print(f"Response has text attr: {hasattr(resp, 'text')}")
            if hasattr(resp, 'text'):
                print(f"Text value: {repr(resp.text)}")
                if resp.text:
                    full_response = resp.text
                    print(f"Extracted text: {full_response[:100]}...")
                    break
            else:
                print(f"Response object: {resp}")
                print(f"Response dir: {[attr for attr in dir(resp) if not attr.startswith('_')]}")

        if not full_response:
            print("No text extracted from LLM response")
        else:
            print(f"Final response: {full_response}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_agent())