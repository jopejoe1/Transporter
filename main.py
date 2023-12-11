import asyncio
import discord
import tomllib

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
locked = []

with open("config.toml", "rb") as f:
    settings = tomllib.load(f)

audio_enabled = settings["settings"]["audio"]


async def process_lock_unlock_commands(message):
    for role in settings["roles"]["lock"]:
        if role in message.author.roles:
            for channel_selector in settings["channels"]["lock"]:
                if channel_selector in message.channel.name.lower():
                    for action, command_list in [("lock", settings["commands"]["lock"]),
                                                 ("unlock", settings["commands"]["unlock"])]:
                        for prefix in command_list:
                            if prefix in message.content.lower():
                                category_id = message.channel.category_id
                                if action == "lock" and category_id not in locked:
                                    locked.append(category_id)
                                elif action == "unlock" and category_id in locked:
                                    locked.remove(category_id)


async def play_audio_files(voice_client, sound_list):
    for sound in sound_list:
        voice_client.play(discord.FFmpegOpusAudio(executable="ffmpeg", source=sound))
        while voice_client.is_playing():
            await asyncio.sleep(0.1)


async def handle_error(message, error_type):
    global audio_enabled
    error_settings = settings["messages"][error_type]
    embed_message = discord.Embed(
        title=error_settings["title"],
        description=error_settings["text"],
        color=error_settings["color"]
    )
    await message.channel.send(embed=embed_message)

    if audio_enabled:
        audio_enabled = False
        voice_client = await message.channel.connect()
        sound_list = settings["sounds"][error_type]
        await play_audio_files(voice_client, sound_list)
        await voice_client.disconnect()
        audio_enabled = True


async def handle_successful_move(message, channel):
    global audio_enabled
    success_settings = settings["messages"]["moving"]
    embed_message = discord.Embed(
        title=success_settings["title"],
        description=success_settings["text"],
        color=success_settings["color"]
    )
    await message.channel.send(embed=embed_message)

    if audio_enabled:
        audio_enabled = False
        voice_client = await message.channel.connect()
        sound_list = settings["sounds"]["moving"]
        await play_audio_files(voice_client, sound_list)
        await voice_client.disconnect()
        audio_enabled = True
    await message.author.move_to(channel)


async def move_to_category(message, category):
    for channel in category.voice_channels:
        for channel_selector in settings["channels"]["move"]:
            if channel_selector in channel.name.lower():
                if channel.permissions_for(message.author).connect:
                    await handle_successful_move(message, channel)
                    return
                else:
                    await handle_error(message, "no_permissions")
                    return
    await handle_error(message, "channel_not_found")


async def handle_locked(message):
    global audio_enabled
    locked_settings = settings["messages"]["locked"]
    embed_message = discord.Embed(
        title=locked_settings["title"],
        description=locked_settings["text"],
        color=locked_settings["color"]
    )
    await message.channel.send(embed=embed_message)

    if audio_enabled:
        audio_enabled = False
        voice_client = await message.channel.connect()
        sound_list = settings["sounds"]["locked"]
        await play_audio_files(voice_client, sound_list)
        await voice_client.disconnect()
        audio_enabled = True


async def handle_moving(message, prefix):
    name = message.content.lower().split(prefix, 1)[1].strip()

    for category in message.guild.categories:
        if name in category.name.lower():
            if category.id in locked or message.channel.category.id in locked:
                await handle_locked(message)
                return
            else:
                await move_to_category(message, category)
                return


async def process_move_commands(message):
    for channel_selector in settings["channels"]["move"]:
        if channel_selector in message.channel.name.lower() and message.author in message.channel.members:
            for prefix in settings["commands"]["move"]:
                if prefix in message.content.lower():
                    await handle_moving(message, prefix)


class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        if message.author.id == self.user.id:
            return

        await process_lock_unlock_commands(message)
        await process_move_commands(message)


client = MyClient(intents=intents)
client.run(settings["settings"]["token"])
