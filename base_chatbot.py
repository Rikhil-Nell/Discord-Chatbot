import os
from dataclasses import dataclass
from typing import Any, List
from dotenv import load_dotenv
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.usage import UsageLimits
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, UserPromptPart, TextPart
from supabase import create_client
from together import Together

# Load environment variables
load_dotenv()

# Initialize Together AI client
api_key = os.getenv("TOGETHER_API_KEY")
client = Together(api_key=api_key)

# Define the LLM model
llm = "llama-3.3-70b-versatile"

# Initialize Groq model
model = GroqModel(
    model_name=llm,
    api_key=os.getenv("GROQ_API_KEY"),
)

# Define dependencies
@dataclass
class Deps:
    supabase_url: str = os.getenv("SUPABASE_URL")
    supabase_key: str = os.getenv("SUPABASE_KEY")
    supabase_client: Any = create_client(supabase_url, supabase_key)

# Load the system prompt
with open("prompt.txt", "r") as file:
    prompt = file.read()

# Define usage limits
usage_limits = UsageLimits(response_tokens_limit=1500)

# Initialize the Pixy agent
Pixy = Agent(
    model=model,
    system_prompt=prompt,
    deps_type=Deps,
    retries=ModelRetry(3)
)

# Define the message handler
async def message_handler(response: List[Any]) -> List[ModelMessage]:
    messages: List[ModelMessage] = []
    
    for item in response:
        role = item['role']
        content = item['content']

        if role == 'user':
            messages.append(
                ModelRequest(parts=[UserPromptPart(content=content)])
            )
        elif role == 'bot':
            messages.append(
                ModelResponse(parts=[TextPart(content=content)])
            )
    return messages

# Fetch memory from Supabase
async def get_memory(deps: Deps, user_id: str, limit: int) -> List[ModelMessage]:
    supabase = deps.supabase_client

    # Fetch the latest messages from Supabase
    response = supabase.table('memory').select('role, content').eq('user_id', user_id).order('timestamp', desc=True).limit(limit).execute()
    response = list(reversed(response.data))  # Reverse for chronological order

    messages = await message_handler(response)
    
    return messages

# Append a message to Supabase
async def append_message(deps: Deps, user_id: str, role: str, content: str) -> None:
    supabase_client = deps.supabase_client

    supabase_client.table('memory').insert({
        'user_id': user_id,
        'role': role,
        'content': content,
    }).execute()

async def image_generation(prompt: str) -> str:
    imageCompletion = client.images.generate(
        model="black-forest-labs/FLUX.1-schnell-Free",
        width=1024,
        height=768,
        steps=4,
        prompt=prompt
    )

    return imageCompletion.data[0].url