from discord import Intents, Client, Message
from dotenv import load_dotenv
from bot import get_response
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

async def send_message(message: Message, user_message: str, thread_id: str) -> None:
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

    # Prepare state
    passed_state = {
        "messages": [{"role": "user", "content": user_message}],
        "thread_id": thread_id,
    }

    try:
        # Pass state to the chatbot for response
        response = await get_response(passed_state)
        if response:
            await message.channel.send(response[-1].content)
        else:
            await message.channel.send("Sorry, I couldn't generate a response.")
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
    thread_id = str(message.author.id)  # Use Discord user ID as the thread_id
    await send_message(message, user_message, thread_id)


def main() -> None:
    """
    Main function to start the Discord bot.
    """
    client.run(DISCORD_KEY)

if __name__ == "__main__":
    main()
