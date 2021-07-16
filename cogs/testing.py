import discord
import time
import io
from discord.ext import commands
from utilities import checks

from PIL import Image

query = """
WITH status_data AS (
    SELECT status, insertion_chopped as insertion,
        case when 
            lag(insertion_chopped) over (order by insertion desc) is null then
                now() at time zone 'utc'
            else
                lag(insertion_chopped) over (order by insertion desc)
        end as last_seen
    from (
        select
            distinct on (insertion_chopped)
            insertion,
            case when insertion < (now() at time zone 'utc' - interval '30 days') then
                (now() at time zone 'utc' - interval '30 days')
                else insertion end as insertion_chopped,
            status,
            lag(status) over (order by insertion desc) as status_last
        from ( 
            (select status, insertion
            from statuses
            where user_id=0
            order by insertion desc)
            union
            (select status, insertion
            from statuses
            where user_id=$1
            order by insertion desc
            limit 3000)
        ) first3000
        order by insertion_chopped desc, insertion desc
    ) subtable
    where
        status is distinct from status_last
    order by insertion desc
)
select *
from status_data
"""


def setup(bot):
    bot.add_cog(Testing(bot))


class Testing(commands.Cog):
    """
    A cog for testing features
    """

    def __init__(self, bot):
        self.bot = bot

    # Owner only cog.
    async def cog_check(self, ctx):
        return checks.is_owner(ctx)

    @commands.command()
    async def a(self, ctx, role: discord.Role):
        st = time.time()
        users = sum(1 for m in role.guild.members if m._roles.has(role.id))
        await ctx.send(str(time.time() - st))
        st = time.time()
        users = sum(1 for m in role.guild.members if role in m.roles)
        await ctx.send(str(time.time() - st))

    @commands.command()
    async def blah(self, ctx):
        from utilities import images

        query = """
                SELECT author_id, COUNT(*) FROM messages
                WHERE server_id = $1
                GROUP BY author_id
                ORDER BY count DESC
                LIMIT 5;
                """
        await ctx.trigger_typing()
        records = await self.bot.cxn.fetch(query, ctx.guild.id)
        data = {
            str(await self.bot.fetch_user(record["author_id"])): record["count"]
            for record in records
        }
        image = Image.new("RGBA", (len(data) * 200, 1000), (216, 183, 255))
        while max(data.values()) > 1000:
            data = {user: count // 2 for user, count in data.items()}
        for user, count in data.items():
            bar = images.get_bar(user, count)
            image.paste(im=bar, box=(list(data.values()).index(count) * 200, 0))

        buffer = io.BytesIO()
        image.save(buffer, "png")  # 'save' function for PIL
        buffer.seek(0)
        dfile = discord.File(fp=buffer, filename="mstats.png")
        em = discord.Embed(title="Message Stats", color=self.bot.constants.embed)
        em.set_image(url="attachment://mstats.png")
        await ctx.send_or_reply(embed=em, file=dfile)

    @commands.command()
    async def statuses(self, ctx):
        d = await self.bot.cxn.fetch(query, ctx.author.id)
        print(d)
