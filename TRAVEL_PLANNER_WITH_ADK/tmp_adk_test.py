import asyncio
from google.adk.models.lite_llm import LiteLlm
from google.adk.models.llm_request import LlmRequest
from google.genai.types import Content, Part

async def test():
    llm = LiteLlm(model='deepseek/deepseek-chat')
    contents = [Content(role='user', parts=[Part(text='Hello, how are you?')])]
    request = LlmRequest(contents=contents)
    gen = llm.generate_content_async(request)
    count = 0
    async for resp in gen:
        print('RESP:', type(resp), resp)
        print('has text', hasattr(resp, 'text'))
        try:
            print('text', resp.text)
        except Exception as e:
            print('text error', e)
        count += 1
        if count >= 5:
            break

asyncio.run(test())
