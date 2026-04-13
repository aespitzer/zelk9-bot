import os
import discord
from anthropic import Anthropic

ZELK9_PROMPT = open("zelk9_persona.md").read()

discord_client = discord.Client(intents=discord.Intents(
    guilds=True,
    guild_messages=True,
    message_content=True,
))
anthropic_client = Anthropic(api_key=os.environ["zelk_claude"])

# Per-channel conversation history
histories = {}

@discord_client.event
async def on_ready():
    print(f"Zelk9 online as {discord_client.user}")

@discord_client.event
async def on_message(message):
    if message.author.bot:
        return
    if discord_client.user not in message.mentions:
        return

    channel_id = message.channel.id
    if channel_id not in histories:
        histories[channel_id] = []

    user_text = message.content.replace(f"<@{discord_client.user.id}>", "").strip()
    histories[channel_id].append({"role": "user", "content": user_text})

    async with message.channel.typing():
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=ZELK9_PROMPT,
            messages=histories[channel_id],
        )

    reply = response.content[0].text
    histories[channel_id].append({"role": "assistant", "content": reply})

    # Trim history to last 20 messages to avoid token bloat
    if len(histories[channel_id]) > 20:
        histories[channel_id] = histories[channel_id][-20:]

    # Respect Discord's 2000 char limit
    for chunk in [reply[i:i+2000] for i in range(0, len(reply), 2000)]:
        await message.channel.send(chunk)

discord_client.run(os.environ["zelk_discord"])
