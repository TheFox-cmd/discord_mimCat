import discord

art_keywords = ["art", "画", "绘画", "绘", "艺术", "艺术品", "画作", "画家", "画廊","好看"]
art_emoji = None

async def art_react(message):
    """Add art reaction to a message."""
    global art_emoji
    # If the emoji isn't loaded yet, load it from the guild's custom emojis
    if not art_emoji:
        guild = message.guild
        print(guild.emojis)
        art_emoji = discord.utils.get(guild.emojis, name="nino")  # Replace 'emoji_name' with the name of the emoji

    # Check if the message contains any of the art-related keywords
    if any(word in message.content.lower() for word in art_keywords):
        # React to the message with the dedicated emoji
        await message.add_reaction(art_emoji)

