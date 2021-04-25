import os
import sys
import time
import codecs
import psutil
import struct
import asyncio
import discord
import inspect
import pathlib
import datetime
import platform
import subprocess

from discord import __version__ as dv
from discord.ext import commands, menus

from utilities import converters, pagination, speedtest, utils


def setup(bot):
    bot.add_cog(Info(bot))


class Info(commands.Cog):
    """
    Module for bot information.
    """

    def __init__(self, bot):
        self.bot = bot
        self.process = psutil.Process(os.getpid())

    async def total_global_commands(self):
        query = """SELECT COUNT(*) as c FROM commands"""
        value = await self.bot.cxn.fetchrow(query)
        return int(value[0])

    async def total_global_messages(self):
        query = """SELECT COUNT(*) as c FROM messages"""
        value = await self.bot.cxn.fetchrow(query)
        return int(value[0])

    @commands.command(
        aliases=["info", "bot", "botstats", "botinfo"],
        brief="Display information about the bot.",
    )
    async def about(self, ctx):
        """
        Usage: -about
        Aliases: -info, -bot, -botstats, botinfo
        Output: Version info and bot stats
        """
        msg = await ctx.send_or_reply(content="**Collecting Info...**")
        total_members = sum(1 for x in self.bot.get_all_members())
        voice_channels = []
        text_channels = []
        for guild in self.bot.guilds:
            voice_channels.extend(guild.voice_channels)
            text_channels.extend(guild.text_channels)

        text = len(text_channels)
        voice = len(voice_channels)

        ramUsage = self.process.memory_full_info().rss / 1024 ** 2
        proc = psutil.Process()
        with proc.oneshot():
            mem_total = psutil.virtual_memory().total / (1024 ** 2)
            mem_of_total = proc.memory_percent()

        embed = discord.Embed(colour=self.bot.constants.embed)
        embed.set_thumbnail(url=ctx.bot.user.avatar_url)
        embed.add_field(
            name="Last boot",
            value=utils.timeago(datetime.datetime.utcnow() - self.bot.uptime),
            inline=True,
        )
        embed.add_field(
            name=f"Developer{'' if len(self.bot.constants.owners) == 1 else 's'}",
            value=",\n ".join(
                [str(self.bot.get_user(x)) for x in self.bot.constants.owners]
            ),
            inline=True,
        )
        embed.add_field(
            name="Python Version", value=f"{platform.python_version()}", inline=True
        )
        embed.add_field(name="Library", value="Discord.py", inline=True)
        embed.add_field(name="API Version", value=f"{dv}", inline=True)
        embed.add_field(
            name="Command Count",
            value=len([x.name for x in self.bot.commands if not x.hidden]),
            inline=True,
        )
        embed.add_field(
            name="Server Count", value=f"{len(ctx.bot.guilds):,}", inline=True
        )
        embed.add_field(
            name="Channel Count",
            value=f"""{self.bot.emote_dict['textchannel']} {text:,}        {self.bot.emote_dict['voicechannel']} {voice:,}""",
            inline=True,
        )
        embed.add_field(name="Member Count", value=f"{total_members:,}", inline=True)
        embed.add_field(
            name="Commands Run",
            value=f"{await self.total_global_commands():,}",
            inline=True,
        )
        embed.add_field(
            name="Messages Seen",
            value=f"{await self.total_global_messages():,}",
            inline=True,
        )
        embed.add_field(name="RAM", value=f"{ramUsage:.2f} MB", inline=True)

        await msg.edit(
            content=f"About **{ctx.bot.user}** | **{self.bot.constants.version}**",
            embed=embed,
        )

    @commands.command(
        brief="Send a bugreport to the developer.",
        aliases=["reportbug", "reportissue", "issuereport"],
    )
    @commands.cooldown(2, 60, commands.BucketType.user)
    async def bugreport(self, ctx, *, bug: str = None):
        """
        Usage:    -bugreport <report>
        Aliases:  -issuereport, -reportbug, -reportissue
        Examples: -bugreport Hello! I found a bug with Snowbot
        Output:   Confirmation that your bug report has been sent.
        Notes:
            Do not hesitate to use this command,
            but please be very specific when describing the bug so
            that the developer may easily see the issue and
            correct it as soon as possible.
        """
        if bug is None:
            return await ctx.send_or_reply(
                content=f"Usage: `{ctx.prefix}bugreport <bug>`",
            )

        owner = discord.utils.get(self.bot.get_all_members(), id=708584008065351681)
        author = ctx.message.author
        if ctx.guild:
            server = ctx.message.guild
            source = "server **{}** ({})".format(server.name, server.id)
        else:
            source = "a direct message"
        sender = "**{0}** ({0.id}) sent you a bug report from {1}:\n\n".format(
            author, source
        )
        message = sender + bug
        try:
            await owner.send(message)
        except discord.errors.InvalidArgument:
            await ctx.send_or_reply(
                "I cannot send your bug report, I'm unable to find my owner."
            )
        except discord.errors.HTTPException:
            await ctx.send_or_reply(content="Your bug report is too long.")
        except Exception:
            await ctx.send_or_reply(
                content="I'm unable to deliver your bug report. Sorry.",
            )
        else:
            await ctx.send_or_reply(
                content="Your bug report has been sent.",
            )

    @commands.command(
        brief="Send a suggestion to the developer.", aliases=["suggestion"]
    )
    @commands.cooldown(2, 60, commands.BucketType.user)
    async def suggest(self, ctx, *, suggestion: str = None):
        """
        Usage:    -suggest <report>
        Aliases:  -suggestion
        Examples: -suggest Hello! You should add this feature...
        Output:   Confirmation that your suggestion has been sent.
        Notes:
            Do not hesitate to use this command,
            your feedback is valued immensly.
            However, please be detailed and concise.
        """
        if suggestion is None:
            return await ctx.send_or_reply(
                content=f"Usage `{ctx.prefix}suggest <suggestion>`",
            )
        owner = discord.utils.get(self.bot.get_all_members(), id=708584008065351681)
        author = ctx.author
        if ctx.guild:
            server = ctx.guild
            source = "server **{}** ({})".format(server.name, server.id)
        else:
            source = "a direct message"
        sender = "**{}** ({}) sent you a suggestion from {}:\n\n".format(
            author, author.id, source
        )
        message = sender + suggestion
        try:
            await owner.send(message)
        except discord.errors.InvalidArgument:
            await ctx.send_or_reply(content="I cannot send your message")
        except discord.errors.HTTPException:
            await ctx.send_or_reply(content="Your message is too long.")
        except Exception as e:
            await ctx.send_or_reply(
                content="I failed to send your message.",
            )
            print(e)
        else:
            await ctx.send_or_reply(content="Your message has been sent.")

    @commands.command(brief="Show the bot's uptime.", aliases=["runtime"])
    async def uptime(self, ctx):
        """
        Usage: -uptime
        Alias: -runtime
        Output: Time since last boot.
        """
        await ctx.send_or_reply(
            f"{self.bot.emote_dict['stopwatch']} I've been running for `{utils.time_between(self.bot.starttime, int(time.time()))}`"
        )

    @commands.command(
        brief="Bot network speed.",
        aliases=["speedtest", "network", "wifi", "download", "upload"],
    )
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def speed(self, ctx):
        """
        Usage: -speed
        Aliases:
            -speedtest, -network, -speed,
            -wifi, -download, -upload
        Output: Internet speed statistics
        Notes:
            The speedtest takes around 30 seconds
            to complete. Please be patient. This
            command is heavily rate limited.
        """
        async with ctx.channel.typing():
            start = time.time()
            message = await ctx.send_or_reply(
                content=f'{self.bot.emote_dict["loading"]} **Calculating Speed...**',
            )
            end = time.time()

            try:
                st = speedtest.Speedtest()
            except Exception as e:
                await message.edit(
                    content=f"{self.bot.emote_dict['failed']} **Failed**"
                )
                print(f"Speedtest error: {e}")
                return
            st.get_best_server()
            d = await self.bot.loop.run_in_executor(None, st.download)
            u = await self.bot.loop.run_in_executor(None, st.upload)

            db_start = time.time()
            await self.bot.cxn.fetch("SELECT 1;")
            elapsed = time.time() - db_start

            p = str(round((end - start) * 1000, 2))
            q = str(round(self.bot.latency * 1000, 2))
            r = str(round(st.results.ping, 2))
            s = str(round(d / 1024 / 1024, 2))
            t = str(round(u / 1024 / 1024, 2))
            v = str(round((elapsed) * 1000, 2))

            formatter = []
            formatter.append(p)
            formatter.append(q)
            formatter.append(r)
            formatter.append(s)
            formatter.append(t)
            formatter.append(v)
            width = max(len(a) for a in formatter)

            msg = "**Results:**\n"
            msg += "```yaml\n"
            msg += " Latency: {} ms\n".format(q.ljust(width, " "))
            msg += " Network: {} ms\n".format(r.ljust(width, " "))
            msg += "Response: {} ms\n".format(p.ljust(width, " "))
            msg += "Database: {} ms\n".format(v.ljust(width, " "))
            msg += "Download: {} Mb/s\n".format(s.ljust(width, " "))
            msg += "  Upload: {} Mb/s\n".format(t.ljust(width, " "))
            msg += "```"
        await message.edit(content=msg)

    @commands.command(
        brief="Test the bot's response latency.",
        aliases=["latency", "response"],
    )
    async def ping(self, ctx):
        """
        Usage: -ping
        Aliases: -latency, -response
        Output: Bot latency statistics.
        Notes:
            Use -speed and the bot will attempt
            to run an internet speedtest. May fail.
        """
        async with ctx.channel.typing():
            start = time.time()
            message = await ctx.send_or_reply(
                content=f'{self.bot.emote_dict["loading"]} **Calculating Latency...**',
            )
            end = time.time()

            db_start = time.time()
            await self.bot.cxn.fetch("SELECT 1;")
            elapsed = time.time() - db_start

            p = str(round((end - start) * 1000, 2))
            q = str(round(self.bot.latency * 1000, 2))

            v = str(round((elapsed) * 1000, 2))

            formatter = []
            formatter.append(p)
            formatter.append(q)
            formatter.append(v)
            width = max(len(a) for a in formatter)

            msg = "**Results:**\n"
            msg += "```yaml\n"
            msg += " Latency: {} ms\n".format(q.ljust(width, " "))
            msg += "Response: {} ms\n".format(p.ljust(width, " "))
            msg += "Database: {} ms\n".format(v.ljust(width, " "))
            msg += "```"
        await message.edit(content=msg)

    @commands.command(brief="Show the bot's host environment.")
    async def hostinfo(self, ctx):
        """
        Usage: -hostinfo
        Output: Detailed information on the bot's host environment
        """
        message = await ctx.channel.send(
            f'{self.bot.emote_dict["loading"]} **Collecting Information...**'
        )

        with self.process.oneshot():
            process = self.process.name
        swap = psutil.swap_memory()

        processName = self.process.name()
        pid = self.process.ppid()
        swapUsage = "{0:.1f}".format(((swap[1] / 1024) / 1024) / 1024)
        swapTotal = "{0:.1f}".format(((swap[0] / 1024) / 1024) / 1024)
        swapPerc = swap[3]
        cpuCores = psutil.cpu_count(logical=False)
        cpuThread = psutil.cpu_count()
        cpuUsage = psutil.cpu_percent(interval=1)
        memStats = psutil.virtual_memory()
        memPerc = memStats.percent
        memUsed = memStats.used
        memTotal = memStats.total
        memUsedGB = "{0:.1f}".format(((memUsed / 1024) / 1024) / 1024)
        memTotalGB = "{0:.1f}".format(((memTotal / 1024) / 1024) / 1024)
        currentOS = platform.platform()
        system = platform.system()
        release = platform.release()
        version = platform.version()
        processor = platform.processor()
        botOwner = self.bot.get_user(self.bot.constants.owners[0])
        botName = ctx.guild.me
        currentTime = int(time.time())
        timeString = utils.time_between(self.bot.starttime, currentTime)
        pythonMajor = sys.version_info.major
        pythonMinor = sys.version_info.minor
        pythonMicro = sys.version_info.micro
        pythonRelease = sys.version_info.releaselevel
        pyBit = struct.calcsize("P") * 8
        process = subprocess.Popen(
            ["git", "rev-parse", "--short", "HEAD"], shell=False, stdout=subprocess.PIPE
        )
        git_head_hash = process.communicate()[0].strip()

        threadString = "thread"
        if not cpuThread == 1:
            threadString += "s"

        msg = "***{}'s*** ***Home:***\n".format(botName)
        msg += "```fix\n"
        msg += "OS       : {}\n".format(currentOS)
        msg += "Owner    : {}\n".format(botOwner)
        msg += "Client   : {}\n".format(botName)
        msg += "Commit   : {}\n".format(git_head_hash.decode("utf-8"))
        msg += "Uptime   : {}\n".format(timeString)
        msg += "Process  : {}\n".format(processName)
        msg += "PID      : {}\n".format(pid)
        msg += "Hostname : {}\n".format(platform.node())
        msg += "Language : Python {}.{}.{} {} ({} bit)\n".format(
            pythonMajor, pythonMinor, pythonMicro, pythonRelease, pyBit
        )
        msg += "Processor: {}\n".format(processor)
        msg += "System   : {}\n".format(system)
        msg += "Release  : {}\n".format(release)
        msg += "CPU Core : {} Threads\n\n".format(cpuCores)
        msg += (
            utils.center(
                "{}% of {} {}".format(cpuUsage, cpuThread, threadString), "CPU"
            )
            + "\n"
        )
        msg += utils.makeBar(int(round(cpuUsage))) + "\n\n"
        msg += (
            utils.center(
                "{} ({}%) of {}GB used".format(memUsedGB, memPerc, memTotalGB), "RAM"
            )
            + "\n"
        )
        msg += utils.makeBar(int(round(memPerc))) + "\n\n"
        msg += (
            utils.center(
                "{} ({}%) of {}GB used".format(swapUsage, swapPerc, swapTotal), "Swap"
            )
            + "\n"
        )
        msg += utils.makeBar(int(round(swapPerc))) + "\n"
        # msg += 'Processor Version: {}\n\n'.format(version)
        msg += "```"

        await message.edit(content=msg)

    @commands.command(
        brief="Show some info on the bot's purpose.", aliases=["boss", "botowner"]
    )
    async def overview(self, ctx):
        """
        Usage:  -overview
        Alias:  -boss, botowner
        Output: Me and my purpose
        """

        owner, command_list, category_list = self.bot.public_stats()
        with open("./data/txts/overview.txt", "r", encoding="utf-8") as fp:
            overview = fp.read()
        embed = discord.Embed(
            description=overview.format(
                self.bot.user.name, len(command_list), len(category_list)
            ),
            color=self.bot.constants.embed,
        )
        embed.set_author(name=owner, icon_url=owner.avatar_url)
        await ctx.send_or_reply(embed=embed)

    @commands.command(brief="Show my changelog.", aliases=["updates"])
    async def changelog(self, ctx):
        """
        Usage: -changelog
        Alias: -updates
        Output: My changelog
        """
        with open("./data/txts/changelog.txt", "r", encoding="utf-8") as fp:
            changelog = fp.read()
        await ctx.send_or_reply(
            content=f"**{self.bot.user.name}'s Changelog**",
        )
        p = pagination.MainMenu(
            pagination.TextPageSource(changelog, prefix="```prolog")
        )
        try:
            await p.start(ctx)
        except menus.MenuError as e:
            await ctx.send_or_reply(e)

    @commands.command(brief="Display the source code.", aliases=["sourcecode"])
    async def source(self, ctx, *, command: str = None):
        """
        Usage: -source [command]
        Alias: -sourcecode
        Notes:
            If no command is specified, shows full repository
        """
        source_url = "https://github.com/Hecate946/Snowbot"
        branch = "main"
        if command is None:
            return await ctx.send_or_reply(source_url)

        else:
            obj = self.bot.get_command(command.replace(".", " "))
            if obj is None:
                return await ctx.send_or_reply(
                    f'{self.bot.emote_dict["failed"]} Command `{command}` does not exist.'
                )
            # Show source for all commands so comment this out.
            # elif obj.hidden:
            #     return await ctx.send_or_reply(
            #         f'{self.bot.emote_dict["failed"]} Command `{command}` does not exist.'
            #     )

            src = obj.callback.__code__
            module = obj.callback.__module__
            filename = src.co_filename

        lines, firstlineno = inspect.getsourcelines(src)
        if not module.startswith("discord"):
            # not a built-in command
            location = os.path.relpath(filename).replace("\\", "/")
        else:
            location = module.replace(".", "/") + ".py"
            source_url = "https://github.com/Hecate946/Snowbot"
            branch = "main"

        final_url = f"<{source_url}/blob/{branch}/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>"
        msg = f"**__My source {'' if command is None else f'for {command}'} is located at:__**\n\n{final_url}"
        await ctx.send_or_reply(msg)

    @commands.command(brief="Invite me to your server!", aliases=["bi", "invite"])
    async def botinvite(self, ctx):
        """
        Usage: -botinvite
        Aliases: -bi, -invite
        Output: An invite link to invite me to your server
        """
        await ctx.send_or_reply(
            f"**{ctx.author.name}**, use this URL to invite me\n<{self.bot.constants.oauth}>"
        )

    @commands.command(
        brief="Join my support server!", aliases=["sup", "assistance", "assist"]
    )
    async def support(self, ctx):
        """
        Usage: -support
        Aliases: -sup, -assist, -assistance
        Output: An invite link to my support server
        """
        await ctx.send_or_reply(
            f"**{ctx.author.name}**, use this URL to join my support server\n{self.bot.constants.support}"
        )

    @commands.command(brief="Shows all users I'm connected to.")
    async def users(self, ctx):
        """
        Usage: -users
        Output: Detailed information on my user stats
        """
        async with ctx.channel.typing():
            msg = await ctx.send_or_reply(
                content=f"{self.bot.emote_dict['loading']} **Collecting User Statistics**",
            )
            users = [x for x in self.bot.get_all_members() if not x.bot]
            users_online = [x for x in users if x.status != discord.Status.offline]
            unique_users = set([x.id for x in users])
            bots = [x for x in self.bot.get_all_members() if x.bot]
            bots_online = [x for x in bots if x.status != discord.Status.offline]
            unique_bots = set([x.id for x in bots])
            e = discord.Embed(title="User Stats", color=self.bot.constants.embed)
            e.add_field(
                name="Humans",
                value="{:,}/{:,} online ({:,g}%) - {:,} unique ({:,g}%)".format(
                    len(users_online),
                    len(users),
                    round((len(users_online) / len(users)) * 100, 2),
                    len(unique_users),
                    round((len(unique_users) / len(users)) * 100, 2),
                ),
                inline=False,
            )
            e.add_field(
                name="Bots",
                value="{:,}/{:,} online ({:,g}%) - {:,} unique ({:,g}%)".format(
                    len(bots_online),
                    len(bots),
                    round((len(bots_online) / len(bots)) * 100, 2),
                    len(unique_bots),
                    round(len(unique_bots) / len(bots) * 100, 2),
                ),
                inline=False,
            )
            e.add_field(
                name="Total",
                value="{:,}/{:,} online ({:,g}%)".format(
                    len(users_online) + len(bots_online),
                    len(users) + len(bots),
                    round(
                        (
                            (len(users_online) + len(bots_online))
                            / (len(users) + len(bots))
                        )
                        * 100,
                        2,
                    ),
                ),
                inline=False,
            )
            await msg.edit(content=None, embed=e)

    @commands.command(brief="Servers you and the bot share.")
    @commands.guild_only()
    async def sharedservers(self, ctx, *, member: converters.DiscordUser = None):
        """
        Usage: -sharedservers [member]
        Output: The servers that the passed member share with the bot
        Notes:
            Will default to youself if no member is passed
        """

        if member is None:
            member = ctx.author

        if member.id == self.bot.user.id:
            return await ctx.send_or_reply(
                "I'm on **{:,}** server{}. ".format(
                    len(self.bot.guilds), "" if len(self.bot.guilds) == 1 else "s"
                )
            )

        count = 0
        for guild in self.bot.guilds:
            for mem in guild.members:
                if mem.id == member.id:
                    count += 1
        if ctx.author.id == member.id:
            targ = "You share"
        else:
            targ = "**{}** shares".format(member.display_name)

        await ctx.send_or_reply(
            "{} **{:,}** server{} with me.".format(
                targ, count, "" if count == 1 else "s"
            )
        )

    async def run_process(self, command):
        try:
            process = await asyncio.create_subprocess_shell(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            result = await process.communicate()
        except NotImplementedError:
            process = subprocess.Popen(
                command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            result = await self.bot.loop.run_in_executor(None, process.communicate)

        return [
            str(output.decode()).replace("[?25l[?7l", "").replace("[?25h[?7h", "")
            for output in result
        ]

    @commands.command(brief="Run the neofetch command.")
    async def neofetch(self, ctx):
        """
        Usage: -neofetch
        Output: Some stats on the bot's server
        """
        async with ctx.typing():
            stdout, stderr = await self.run_process("neofetch|sed 's/\x1B[[0-9;]*m//g'")

        if stderr:
            text = f"stdout:\n{stdout}\nstderr:\n{stderr}"
        else:
            text = stdout

        text = text[:-3]

        pages = pagination.MainMenu(pagination.TextPageSource(text, prefix="```prolog"))
        try:
            await pages.start(ctx)
        except menus.MenuError as e:
            await ctx.send_or_reply(str(e))

    @commands.command(
        aliases=["code", "cloc", "codeinfo"], brief="Show sourcecode statistics."
    )
    async def lines(self, ctx):
        """
        Usage: -lines
        Aliases: -cloc, -code, codeinfo
        Output:
            Gives lines, characters, imports, functions,
            classes, comments, and files in the source code
        """
        async with ctx.channel.typing():
            msg = "```fix\n"
            lines = 0
            file_amount = 0
            comments = 0
            funcs = 0
            classes = 0
            chars = 0
            imports = 0
            exclude = set([".testervenv", ".git", "__pycache__", ".vscode"])
            for path, subdirs, files in os.walk("."):
                [subdirs.remove(d) for d in list(subdirs) if d in exclude]
                for name in files:
                    if name.endswith(".py"):
                        file_amount += 1
                        with codecs.open(
                            "./" + str(pathlib.PurePath(path, name)), "r", "utf-8"
                        ) as f:
                            for l in f:
                                chars += len(l.strip())
                                if l.strip().startswith("#"):
                                    comments += 1
                                elif len(l.strip()) == 0:
                                    pass
                                else:
                                    lines += 1
                                    if l.strip().startswith(
                                        "def"
                                    ) or l.strip().startswith("async"):
                                        funcs += 1
                                    elif l.strip().startswith("class"):
                                        classes += 1
                                    elif l.strip().startswith(
                                        "import"
                                    ) or l.strip().startswith("from"):
                                        imports += 1
            width = max(
                len(f"{lines:,}"),
                len(f"{file_amount:,}"),
                len(f"{chars:,}"),
                len(f"{imports:,}"),
                len(f"{classes:,}"),
                len(f"{funcs:,}"),
                len(f"{comments:,}"),
            )
            files = "{:,}".format(file_amount)
            lines = "{:,}".format(lines)
            chars = "{:,}".format(chars)
            imports = "{:,}".format(imports)
            classes = "{:,}".format(classes)
            funcs = "{:,}".format(funcs)
            comments = "{:,}".format(comments)
            msg += f"{files.ljust(width)} Files\n"
            msg += f"{lines.ljust(width)} Lines\n"
            msg += f"{chars.ljust(width)} Characters\n"
            msg += f"{imports.ljust(width)} Imports\n"
            msg += f"{classes.ljust(width)} Classes\n"
            msg += f"{funcs.ljust(width)} Functions\n"
            msg += f"{comments.ljust(width)} Comments"
            msg += "```"
            em = discord.Embed(color=self.bot.constants.embed)
            em.title = f"{self.bot.emote_dict['info']} Source information"
            em.description = msg
            await ctx.send_or_reply(embed=em)