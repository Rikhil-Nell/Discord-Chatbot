import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from base_chatbot import Pixy, Deps, usage_limits, get_memory, append_message, image_generation
import os
import requests

# Load environment variables
load_dotenv()
DISCORD_KEY = os.getenv("DISCORD_TOKEN")
if not DISCORD_KEY:
    raise ValueError("DISCORD_TOKEN is not set in your environment variables.")

# Setup bot with command tree for slash commands
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def send_message(message: discord.Message, deps: Deps, user_message: str, user_id: str) -> None:
    """
    Handles sending a message to the Discord channel.
    """
    if not user_message:
        print("(Message was empty because intents might not be enabled.)")
        return
    try:
        memory = await get_memory(deps=deps, user_id=user_id, limit=30)
        response = await Pixy.run(deps=deps, user_prompt=user_message, message_history=memory, usage_limits=usage_limits)
        await message.channel.send(response.data if response else "Sorry, I couldn't process that.")
        await append_message(deps=deps, user_id=user_id, role="bot", content=response.data)
    except Exception as e:
        print(f"Error sending message: {e}")
        await message.channel.send("An error occurred while processing your request.")

@bot.event
async def on_ready():
    """Triggered when the bot successfully connects to Discord."""
    print(f"{bot.user} is now running...")
    await bot.tree.sync()  # Sync slash commands globally

@bot.event
async def on_message(message: discord.Message):
    """
    Triggered whenever a message is sent in a Discord channel.
    """
    if message.author == bot.user:
        return  # Ignore the bot's own messages

    user_message = message.content
    user_id = str(message.author.id)  # Use Discord user ID as the thread_id
    await append_message(deps=Deps, user_id=user_id, role="user", content=user_message)
    await send_message(message=message, deps=Deps, user_message=user_message, user_id=user_id)

# Slash command for generating images
@bot.tree.command(name="generate", description="Generate an AI image from a prompt.")
@app_commands.describe(prompt="Describe the image you want to generate")
async def generate(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer()  # Acknowledge the command to prevent timeout

    try:
        # Generate the image
        image_url = await image_generation(prompt)  # Assuming this returns a URL
        
        # Download the image
        response = requests.get(image_url)
        if response.status_code != 200:
            await interaction.followup.send("Failed to retrieve the image.")
            return
        
        # Save image locally
        os.makedirs("images", exist_ok=True)
        image_path = f"images/generated_image.png"
        with open(image_path, "wb") as f:
            f.write(response.content)

        # Send the image back
        await interaction.followup.send(file=discord.File(image_path))

    except Exception as e:
        print(f"Error generating image: {e}")
        await interaction.followup.send("An error occurred while generating the image.")

def main():
    bot.run(DISCORD_KEY)

if __name__ == "__main__":
    main()
