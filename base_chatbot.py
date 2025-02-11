import os
from dataclasses import dataclass
from typing import Any, List, Dict, Union
import json
from dotenv import load_dotenv

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, UserPromptPart, TextPart
from supabase import create_client

load_dotenv()

llm = "llama-3.3-70b-versatile"

model = GroqModel(
    model_name=llm,
    api_key=os.getenv("GROQ_API_KEY"),
)

@dataclass
class Deps:
    supabase_url: str = os.getenv("SUPABASE_URL")
    supabase_key: str = os.getenv("SUPABASE_KEY")
    supabase_client: Any = create_client(supabase_url, supabase_key)

with open ("prompt.txt", "r") as file:
    prompt = file.read()

Pixy = Agent(
    model = model,
    system_prompt= prompt,
    deps_type= Deps
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