import discord
import aiofiles
from os import path
from aiohttp import ClientSession
from config import API_TOKEN

client = discord.Client()

# Add numbers to duplicately named files to save them to different files
def get_filename(name):
    filename = f'images/{name}' + "0"
    count = 1
    while path.isfile(filename):
        filename = filename[:-1] + str(count)
        count += 1
    return filename

# Downloads a request from an embed
async def save_embed(embed):
    async with ClientSession() as session:
        async with session.get(embed.url) as response:
            filename = get_filename(embed.url.split("/")[-1])
            async with aiofiles.open(filename, 'wb') as file:
                await file.write(await response.read())

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Only images and videos have a height
    for attachment in message.attachments:
        if attachment.height is not None:
            await attachment.save(get_filename(attachment.filename))

    for embed in message.embeds:
        if embed.type == "image":
            await save_embed(embed)

client.run(API_TOKEN)
