from discord import Intents, Client, Message
from dotenv import load_dotenv
from base_chatbot import Pixy, Deps, get_memory, append_message
import os

# Load environment variables
load_dotenv()

DISCORD_KEY = os.getenv("DISCORD_TOKEN")
if not DISCORD_KEY:
    raise ValueError("DISCORD_TOKEN is not set in your environment variables.")

# Setup Intents
intents = Intents.default()
intents.message_content = True
client = Client(intents=intents)

async def send_message(message: Message, deps: Deps, user_message: str, user_id: str) -> None:
    """
    Handles sending a message to the Discord channel.
    Args:
        message (Message): The incoming Discord message object.
        user_message (str): The content of the user's message.
        thread_id (str): The unique identifier for the conversation thread.
    """
    if not user_message:
        print("(Message was empty because intents might not be enabled.)")
        return
    try:
        memory = await get_memory(deps=deps, user_id=user_id, limit=30)
        response = await Pixy.run(deps=deps, user_prompt=user_message, message_history=memory)
        await message.channel.send(response.data) if response else message.channel.send("Sorry, I couldn't process that.")
        await append_message(deps=deps, user_id=user_id,role= "bot", content=response.data)

    except Exception as e:
        print(f"Error sending message: {e}")
        await message.channel.send("An error occurred while processing your request.")

@client.event
async def on_ready() -> None:
    """
    Triggered when the bot successfully connects to Discord.
    """
    print(f"{client.user} is now running...")

@client.event
async def on_message(message: Message) -> None:
    """
    Triggered whenever a message is sent in a Discord channel.
    Args:
        message (Message): The incoming Discord message object.
    """
    if message.author == client.user:
        return  # Ignore the bot's own messages

    user_message = message.content
    user_id = str(message.author.id)  # Use Discord user ID as the thread_id
    await append_message(deps=Deps, user_id=user_id, role= "user", content=user_message)
    await send_message(deps=Deps, message=message, user_message=user_message, user_id=user_id)

def main() -> None:
    """
    Main function to start the Discord bot.
    """
    client.run(DISCORD_KEY)

if __name__ == "__main__":
    main()
