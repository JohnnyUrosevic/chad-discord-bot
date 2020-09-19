import discord
from discord.ext import commands
import aiofiles
from os import path, remove, environ, mkdir
from re import search
from aiohttp import ClientSession, ClientTimeout
from lite import NudeClassifier

API_TOKEN = environ.get('API_TOKEN')

classfier = NudeClassifier()
client = commands.Bot(commands.when_mentioned)

# TODO: this should be server specific
threshold = .80

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
    timeout = ClientTimeout(total=0.5)
    async with ClientSession() as session:
        try:
            async with session.get(url, timeout=timeout) as response:
                async with aiofiles.open(path, 'wb') as file:
                    await file.write(await response.read())
        except TimeoutError:
            return

@client.event
async def on_ready():
    try:
        mkdir('images')
    except FileExistsError:
        print('Using existing images directory')
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
    regex = r'https?:(?:%|\/|\.|\w|-)*\.(?:jpg|gif|png|jpeg)(?:\?(?:\w|=|&|%)+?)?'
    urls = [url for url in message.content.split(" ") if search(regex, url)]
    for url in urls:
        path = get_filename(url.split("/")[-1])
        filenames.append(path)
        await save_embed(url, path)

    if not filenames:
        await client.process_commands(message)
        return

    prob = classfier.classify(filenames)
    unsafe_chance = max([v['unsafe'] for v in prob])
    print(unsafe_chance)
    global threshold
    if unsafe_chance >= threshold:
        await message.channel.send(f'Sorry {message.author.mention}')
        await message.delete()

    for file in filenames:
        remove(file)
        
@client.command(name="threshold")
@commands.has_permissions(administrator=True)
async def change_threshold(ctx, new: float):
    """Changes the threshold for what is considered a nude."""
    if new < .50 or new > 1.0:
        await ctx.send(f'The threshold must be a value between .5 and 1.0')
        return

    global threshold
    threshold = new
    await ctx.send(f'Changed the detection threshold to {int(threshold * 100)}%')

client.run(API_TOKEN)
