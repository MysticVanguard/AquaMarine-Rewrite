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
        async with vbu.Database() as db:
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
        
        if type == "fish":
            async with vbu.Database() as db:
                user_fish = await db(
                            """SELECT * FROM user_fish_inventory WHERE user_id = $1""",
                            ctx.author.id,
                        )
            if not user_fish:
                return await ctx.send("You have no fish!")
            
            chosen_fish = await utils.create_dropdown_embed(ctx, ctx.author, await utils.sort_by_rarity(user_fish))
            if chosen_fish:
                if _Fish_Species.get_fish(chosen_fish.replace(" ", "_").lower()) not in await utils.sort_by_rarity(user_fish):
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
            embed=discord.Embed(title="Items")
            for item in utils.VALID_ITEMS:
                embed.add_field(name=f"{utils.EMOJIS[item]} {item.replace('_', ' ').title()}", value=user_items[0][item])
            await ctx.send(embed=embed)

                
    
    @commands.command(application_command_meta=commands.ApplicationCommandMeta())
    @commands.bot_has_permissions(send_messages=True)
    async def add_to_tank(self, ctx: vbu.SlashContext):
        rarities = ['legendary', 'epic', 'rare', 'uncommon', 'common']
        async with vbu.Database() as db:
            user_fish = await db(
                    """SELECT * FROM user_fish_inventory WHERE user_id = $1 AND in_tank = FALSE""",
                    ctx.author.id,
                )
            user_settings = await db(
                """SELECT * FROM user_settings WHERE user_id = $1""",
                ctx.author.id
            )
        if not user_fish:
            return await ctx.send("You have no fish!")
        if len(user_fish) >= user_settings[0]['tank_room']:
            return await ctx.send("You have no tank room!")
        fish_objects = []
        for fish in user_fish:
            fish_objects.append(_Fish_Species.get_fish(fish['species']))
        first_fish_options = [single_fish.name.replace('_', ' ').title() for single_fish in fish_objects]
        fish_options = []
        if len(first_fish_options) > 25:
            fish_options = first_fish_options[:24]
            fish_options.append("Next List")
        else:
            fish_options = first_fish_options
        fish = await utils.create_select_menu(self.bot, ctx, fish_options, "fish", "select", True)
        if fish == "Next List":
            fish = await utils.create_select_menu(self.bot, ctx, first_fish_options[25:], "fish", "select", True)
        if fish not in first_fish_options:
            return
        for single_fish in user_fish:
            if single_fish['species'] == fish.replace(" ", "_").lower():
                selected_fish_object = single_fish
                break
        async with vbu.Database() as db:
            db_call = "UPDATE user_settings SET {0} = $1 + {1} WHERE user_id = $2"
            lever_info = utils.lever_info[_Fish_Species.get_fish(fish.replace(" ", "_").lower()).lever]
            
            await db(
                db_call.format(_Fish_Species.get_fish(fish.replace(" ", "_").lower()).lever, 
                           lever_info[0]*int(selected_fish_object['level']/lever_info[1][rarities.index(_Fish_Species.get_fish(fish.replace(" ", "_").lower()).rarity)])), 
                           user_settings[0][_Fish_Species.get_fish(fish.replace(" ", "_").lower()).lever], 
                           ctx.author.id
            )
            await db(
                """UPDATE user_fish_inventory SET in_tank = TRUE WHERE user_id = $1 and species = $2""",
                ctx.author.id,
                fish.replace(" ", "_").lower()
            )
        return await ctx.send("Successfully added to tank.")
def setup(bot):
    bot.add_cog(Home(bot))