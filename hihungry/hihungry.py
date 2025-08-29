import re
from time import time
from random import random
import discord
import logging
from typing import Dict, Optional
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.utils.views import SimpleMenu

log = logging.getLogger("red.atnqty-cogs.hihungry")

class HiHungry(commands.Cog):
    """Make Hi Hungry I'm dad joke."""

    def __init__(self, bot: Red):
        super().__init__()
        self.bot = bot
        self.config = Config.get_conf(self, identifier=43628891)
        self.hhmaxlen: Dict[int, int] = {}
        self.hhchance: Dict[int, float] = {}
        self.hhsingle: Dict[int, bool] = {}
        self.config.register_guild(hhmaxlen=999, hhchance=0.1, hhsingle=False)

    async def cog_load(self):
        all_config = await self.config.all_guilds()
        self.hhmaxlen = {guild_id: conf['hhmaxlen'] for guild_id, conf in all_config.items()}
        self.hhchance = {guild_id: conf['hhchance'] for guild_id, conf in all_config.items()}
        self.hhsingle = {guild_id: conf['hhsingle'] for guild_id, conf in all_config.items()}

    # Listeners

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        if not await self.is_valid_red_message(message):
            return
        channel_perms = message.channel.permissions_for(message.guild.me)
        if not channel_perms.send_messages:
            return
        msg = message.content
        if not msg:
            return
        if msg.startswith('!'):
            return
        started = False
        buffer = ''
        words = 0
        # emote = False
        hhmaxlen = await self.config.guild(message.guild).hhmaxlen()
        hhchance = await self.config.guild(message.guild).hhchance()
        hhsingle = await self.config.guild(message.guild).hhsingle()
        for c in msg:
            # log.info(f"{words} {hhmaxlen} {buffer}")
            if started:
                if c == ' ':
                    if not buffer or buffer[-1] == ' ':
                        continue
                    else:
                        buffer += c
                        words += 1
                else:
                    if words >= hhmaxlen:
                        return
                    if c.isalnum() or c in "'-<>:()*~`_":
                        # if buffer and buffer[-1] == '<' and c == ':':
                        #     emote = True
                        # if c == '>':
                        #     emote = False
                        # if emote:
                        #     buffer += c
                        elif not buffer or buffer[-1] == ' ':
                            buffer += c.upper()
                        else:
                            buffer += c.lower()
                    else:
                        if hhsingle:
                            return
                        else:
                            break
            else:
                # detect "I'm" or "I am" at the start of the message
                if c == ' ':
                    if not buffer:
                        continue
                    if buffer.lower() in ["im","i'm","i am"]:
                        started = True
                        buffer = ''
                    else:
                        if buffer.lower() == "i":
                            buffer += c
                        else:
                            return
                else:
                    if c not in "i'am":
                        return
                    buffer += c
                    if buffer.lower() not in ["i","im","i'","i'm","i a","i am"]:
                        return
        if random() < hhchance:
            buffer = re.sub(r'\S*<a?:\S+:\d+>\S*', ' ', buffer) # remove emotes
            buffer = re.sub(r'[*~`]', '', buffer) # remove markdown
            buffer = re.sub(r'(?<!\w)_(?!\w)|(?<!\w)_(?=\W)|(?<=\W)_(?!\w)', '', buffer) # remove markdown underscore
            await message.reply(content=f'Hi {buffer.strip()}, I am {self.bot.user.name}', allowed_mentions=discord.AllowedMentions.none())

    async def is_valid_red_message(self, message: discord.Message) -> bool:
        return await self.bot.allowed_by_whitelist_blacklist(message.author) \
               and await self.bot.ignored_channel_or_guild(message) \
               and not await self.bot.cog_disabled_in_guild(self, message.guild)

    # Commands

    @commands.group(aliases=["hungry"], invoke_without_command=True)
    @commands.guild_only()
    async def hihungry(self, ctx: commands.Context):
        """Make Hi Hungry I'm dad joke."""
        await ctx.send_help()

    @hihungry.command()
    @commands.has_permissions(manage_guild=True)
    async def maxlen(self, ctx: commands.Context, numwords: Optional[int]):
        """Set the maximum words the massage can have to trigger response. Default 999."""
        if numwords is None:
            return await ctx.send(f"The current maximum for words is {self.hhmaxlen.get(ctx.guild.id, None)}")
        await self.config.guild(ctx.guild).hhmaxlen.set(numwords)
        self.hhmaxlen[ctx.guild.id] = numwords
        await ctx.send(f"✅ The new maximum for words is {numwords}")

    @hihungry.command()
    @commands.has_permissions(manage_guild=True)
    async def chance(self, ctx: commands.Context, fchance: Optional[float]):
        """Set the the chance of response between 0 to 1."""
        if fchance is None:
            return await ctx.send(f"The current chance is {self.hhchance.get(ctx.guild.id, None)}")
        await self.config.guild(ctx.guild).hhchance.set(fchance)
        self.hhchance[ctx.guild.id] = fchance
        await ctx.send(f"✅ The new chance is {fchance}")

    @hihungry.command()
    @commands.has_permissions(manage_guild=True)
    async def single(self, ctx: commands.Context):
        """Toggle between detecting only single sentence no punctuation message or not."""
        toggled_single = not self.hhsingle[ctx.guild.id]
        await self.config.guild(ctx.guild).hhsingle.set(toggled_single)
        self.hhsingle[ctx.guild.id] = toggled_single
        if toggled_single:
            await ctx.send(f"Now responding only single sentence message.")
        else:
            await ctx.send(f"Now cut off at punctuation.")
