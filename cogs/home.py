import random
import asyncio
import discord
from datetime import datetime as dt, timedelta
from discord.ext import commands, tasks, vbu

from cogs import utils
from cogs.utils._fish import _Fish_Species

class Home(vbu.Cog):

    @commands.command(application_command_meta=commands.ApplicationCommandMeta())
    @commands.bot_has_permissions(send_messages=True)
    async def balance(self, ctx: vbu.SlashContext):
        """Checks your balance"""
        async with vbu.Database() as db:
            user_settings = await db(
                """SELECT * FROM user_settings WHERE user_id = $1""",
                ctx.author.id,
            )
            if not user_settings:
                await utils.add_user(ctx)
                user_settings = await db(
                    """SELECT * FROM user_settings WHERE user_id = $1""",
                    ctx.author.id,
                )

        embed = discord.Embed(title="User Balance")
        embed.add_field(name="Sand Dollars:", value=user_settings[0]['sand_dollars'])
        embed.add_field(name="Doubloons:", value=user_settings[0]['doubloons'])
        await ctx.send(embed=embed)

    @commands.command(application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="type",
                    type=discord.ApplicationCommandOptionType.string,
                    description="The type of inventory you want to see",
                    choices=[
                        discord.ApplicationCommandOptionChoice(
                            name="Item", value="item"
                        ),
                        discord.ApplicationCommandOptionChoice(
                            name="Fish", value="fish"
                        ),
                        discord.ApplicationCommandOptionChoice(
                            name="Tank", value="tank"
                        ),
                    ],
                    required=True,
                ),
            ]
    ))
    @commands.bot_has_permissions(send_messages=True)
    async def inventory(self, ctx: vbu.SlashContext, type: str):
        """Let's you see your fish, tanks, and items, as well as actions with your fish"""
        if type == "fish":
            async with vbu.Database() as db:
                user_fish = await db(
                            """SELECT * FROM user_fish_inventory WHERE user_id = $1""",
                            ctx.author.id,
                        )
            if not user_fish:
                return await ctx.send("You have no fish!")
            
            chosen_fish = await utils.create_dropdown_embed(ctx, ctx.author, 
                            await utils.sort_by_rarity(user_fish))
            if chosen_fish:
                if chosen_fish.__class__ != str:
                    return
                await utils.get_info(ctx, chosen_fish)
        elif type == "tank":
            async with vbu.Database() as db:
                user_fish = await db(
                        """SELECT * FROM user_fish_inventory WHERE user_id = $1 AND in_tank = TRUE""",
                        ctx.author.id,
                    )
                user_settings = await db(
                    """SELECT * FROM user_settings WHERE user_id = $1""",
                    ctx.author.id
                )
                if not user_settings:
                    await utils.add_user(ctx)
                    user_settings = await db(
                        """SELECT * FROM user_settings WHERE user_id = $1""",
                        ctx.author.id,
                    )
            if not user_fish:
                return await ctx.send("You have no fish in tanks!")
            images = await utils.create_images(user_fish, user_settings)
            await utils.create_tank_embed(ctx, self.bot, user_fish, images)
        elif type == "item":
            async with vbu.Database() as db:
                user_items = await db(
                    """SELECT * FROM user_item_inventory WHERE user_id = $1""",
                    ctx.author.id
                )
                if not user_items:
                    await utils.add_user(ctx)
                    user_items = await db(
                        """SELECT * FROM user_item_inventory WHERE user_id = $1""",
                        ctx.author.id
                    )
            embed=discord.Embed(title="Items")
            for item in utils.VALID_ITEMS:
                embed.add_field(name=f"{utils.EMOJIS[item]} {item.replace('_', ' ').title()}", 
                                value=user_items[0][item])
            await ctx.send(embed=embed)

    @commands.command(application_command_meta=commands.ApplicationCommandMeta())
    @commands.cooldown(1, 60 * 60 * 24, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def daily(self, ctx: commands.Context):
        """Gives XP orbs based on what was spun"""

        components = discord.ui.MessageComponents(
            discord.ui.ActionRow(
                discord.ui.Button(label="Stop Spinning", custom_id="stop")
            ),
        )
        embed = discord.Embed(title="Click the button to stop the wheel!")
        file = discord.File(
            "C://Users//johnt//Pictures//fish//daily_wheel//daily_spinning.gif",
            "win_wheel.gif",
        )
        embed.set_image(url="attachment://win_wheel.gif")
        embed.add_field(
            name=f"Spinning...",
            value="Gray = Common\nGreen = Uncommon\nBlue = Rare\nPurple = Epic",
        )
        daily_message = await ctx.send(embed=embed, components=components, file=file)

        # Wait for them to click a button
        try:
            await self.bot.wait_for(
                "component_interaction", check=lambda p: p.user.id == ctx.author.id and p.message.id == daily_message.id, timeout=60
            )
        except TimeoutError:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Timed out waiting for click, try again.")

        reward = random.choices(
            ["common_xp_orb", "uncommon_xp_orb", "rare_xp_orb", "epic_xp_orb"], 
            [0.5, 0.25, 0.125, 0.125]
        )[0]

        # Adds the money to the users balance
        async with vbu.Database() as db:
            items = await db("""SELECT * FROM user_item_inventory WHERE user_id = $1""",
                                ctx.author.id)
            if not items:
                await utils.add_user(ctx)
                items = await db("""SELECT * FROM user_item_inventory WHERE user_id = $1""",
                                    ctx.author.id)
            await db("""UPDATE user_item_inventory SET {0} = $1 WHERE user_id = $2""".format(reward),
                                    items[0][reward]+1,
                                    ctx.author.id)

        # confirmation message
        embed = discord.Embed(title="Click the button to stop the wheel!")
        file = discord.File(
            f"C://Users//johnt//Pictures//fish//daily_wheel//{reward}_daily_win.png",
            "win_wheel.png",
        )
        embed.set_image(url="attachment://win_wheel.png")
        embed.add_field(
            name=f"Daily reward of 1 {reward.replace('_', ' ').title()} claimed!",
            value="Gray = Common\nGreen = Uncommon\nBlue = Rare\nPurple = Epic",
        )
        await daily_message.delete()
        return await ctx.send(embed=embed, file=file)
    
def setup(bot):
    bot.add_cog(Home(bot))