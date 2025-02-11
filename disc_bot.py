import os
import asyncio
from discord import Intents, Client, Message
from dotenv import load_dotenv
from base_chatbot import Pixy, Deps, get_memory, append_message

# Load environment variables
load_dotenv()
DISCORD_KEY = os.getenv("DISCORD_TOKEN")
if not DISCORD_KEY:
    raise ValueError("DISCORD_TOKEN is not set in environment variables.")

# Setup Discord client with intents
intents = Intents.default()
intents.message_content = True
client = Client(intents=intents)

# Initialize Dependencies
deps = Deps()

async def send_long_message(channel: Message.channel, text : str, limit=2000) -> None:
    """Splits long messages while keeping code blocks intact and preserving syntax highlighting."""
    parts = text.split("```")  # Splitting at code block markers
    chunks = []
    
    for i, part in enumerate(parts):
        if i % 2 == 1:  # Code blocks (odd-indexed parts)
            lines = part.split("\n")
            first_line = lines[0] if lines else ""  # Extract the first line (may contain language)
            language = first_line if first_line.isalpha() else ""  # Preserve if it's a language specifier
            code_content = "\n".join(lines[1:]) if language else part  # Remove the first line if it's a language

            if language:
                formatted_code = f"```{language}\n{code_content}```"
            else:
                formatted_code = f"```{part}```"

            if len(formatted_code) > limit:
                # If the code block is too long, split inside it
                code_lines = code_content.split("\n")
                temp_chunk = f"```{language}\n" if language else "```"
                for line in code_lines:
                    if len(temp_chunk) + len(line) + 1 > limit:
                        temp_chunk += "```"
                        chunks.append(temp_chunk)
                        temp_chunk = f"```{language}\n" + line + "\n" if language else "```" + line + "\n"
                    else:
                        temp_chunk += line + "\n"
                temp_chunk += "```"
                chunks.append(temp_chunk)
            else:
                chunks.append(formatted_code)
        else:  # Normal text (even-indexed parts)
            words = part.split(" ")
            temp_chunk = ""
            for word in words:
                if len(temp_chunk) + len(word) + 1 > limit:
                    chunks.append(temp_chunk)
                    temp_chunk = word + " "
                else:
                    temp_chunk += word + " "
            if temp_chunk:
                chunks.append(temp_chunk)

    # Send all chunks
    for chunk in chunks:
        await channel.send(chunk)


async def process_message(message: Message, user_message: str, user_id: str) -> None:
    """
    Processes user message and responds.
    """
    if not user_message:
        print("Warning: Empty message received (Intents issue?)")
        return
    try:
        memory = await get_memory(deps=deps, user_id=user_id, limit=30)
        response = await Pixy.run(deps=deps, user_prompt=user_message, message_history=memory)

        if response:
            await send_long_message(message.channel, response.data)
            await append_message(deps=deps, user_id=user_id, role="bot", content=response.data)
        else:
            await message.channel.send("Sorry, I couldn't process that.")

    except Exception as e:
        print(f"Error processing message: {e}")
        await message.channel.send("An error occurred while processing your request.")

@client.event
async def on_ready() -> None:
    """Triggered when the bot successfully connects to Discord."""
    print(f"{client.user} is now running...")

@client.event
async def on_message(message: Message) -> None:
    """Handles new messages."""
    if message.author == client.user:
        return  # Ignore bot's own messages

    user_message = message.content
    user_id = str(message.author.id)

    await append_message(deps=deps, user_id=user_id, role="user", content=user_message)
    await process_message(message, user_message, user_id)

async def main():
    """Starts the bot asynchronously."""
    async with client:
        await client.start(DISCORD_KEY)

if __name__ == "__main__":
    asyncio.run(main())  # Ensures async execution
