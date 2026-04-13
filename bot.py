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

import datetime
import asyncio

TARGET_CHANNEL_ID = 1493051329676050442

@discord_client.event
async def on_ready():
    print(f"Zelk9 online as {discord_client.user}")
    discord_client.loop.create_task(scheduled_message())

async def scheduled_message():
    await discord_client.wait_until_ready()
    while not discord_client.is_closed():
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-6)))  # CST
        if 9 <= now.hour < 21:
            channel = discord_client.get_channel(TARGET_CHANNEL_ID)
            if channel:
                response = anthropic_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    system=ZELK9_PROMPT,
                    messages=[{"role": "user", "content": "Send your operative an unsolicited check-in message. You have been observing or doing something. Issue a directive or update. Be brief."}],
                )
                await channel.send(response.content[0].text)
        await asyncio.sleep(4 * 60 * 60)  # wait 4 hours