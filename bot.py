import discord
import aiofiles
from os import path, remove
from re import search
from aiohttp import ClientSession
from nudenet import NudeClassifier
from config import API_TOKEN

classfier = NudeClassifier()
client = discord.Client()

THRESHOLD = .90

# Add numbers to duplicately named files to save them to different files
def get_filename(name):
    filename = f'images/{name}' + "0"
    count = 1
    while path.isfile(filename):
        filename = filename[:-1] + str(count)
        count += 1
    return filename

# Downloads a request from an embed
async def save_embed(url, path):
    async with ClientSession() as session:
        async with session.get(url) as response:
            async with aiofiles.open(path, 'wb') as file:
                await file.write(await response.read())

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # List of files downloaded from this message
    filenames = []
    # Only images and videos have a height
    for attachment in message.attachments:
        if attachment.height is not None:
            path = get_filename(attachment.filename)
            filenames.append(path)
            await attachment.save(path)

    # Checks if a token is an image url
    regex = r'https?:(?:%|\/|.|\w|-)*\.(?:jpg|gif|png|jpeg)(?:\?(?:\w|=|&|%)+?)?'
    urls = [url for url in message.content.split(" ") if search(regex, url)]
    for url in urls:
        path = get_filename(url.split("/")[-1])
        filenames.append(path)
        await save_embed(url, path)

    for file in filenames:
        prob = classfier.classify(file)[file]
        if prob['unsafe'] >= THRESHOLD:
            await message.channel.send(f'Sorry {message.author.mention}')
            await message.delete()

        remove(file)

client.run(API_TOKEN)
