from discord import Intents, Client, Message
from dotenv import load_dotenv
from base_chatbot import get_response
import os

load_dotenv()

os.environ["DISCORD_KEY"] = os.getenv("DISCORD_TOKEN")

# Setup Intents

intents :Intents = Intents.default()
intents.message_content = True
client :Client = Client(intents=intents)

# Message Functionality
async def send_message(message: Message, user_message:str) -> None:
    if not user_message:
        print('(Meesage was empty because intents were not enabled probably)')
        return
    
    try:
        reponse:str = get_response(user_message)
        await message.channel.send(reponse)
    except Exception as e:
        print(e)
    
# Handling startup for the bot

@client.event
async def on_ready() -> None:
    print(f"{client.user} is now running...")


# Handling incoming messages

@client.event
async def on_message(message : Message) -> None:
    if message.author == client.user:
        return
    
    username: str = str(message.author)
    user_message: str = str(message.content)
    channel: str = str(message.channel.name)
    print(f"{username} said: '{user_message}' ({channel})")
    await send_message(message, user_message)

# Running the bot
def main() -> None:
    client.run(token= os.getenv("DISCORD_KEY"))

if __name__ == "__main__":
    main()