import random
import asyncio
import discord
from datetime import datetime as dt, timedelta
from discord.ext import commands, tasks, vbu

from cogs import utils


class Fishing(vbu.Cog):
    
    def __init__(self, bot: vbu.Bot):
        super().__init__(bot)
        self.energy_loop.start()

    def cog_unload(self):
        self.energy_loop.cancel()

    @tasks.loop(hours=1) 
    async def energy_loop(self): 

        async with vbu.Database() as db:
            users_settings = await db("""SELECT * FROM user_settings""")
            for user in users_settings:
                if user['current_energy'] < user['max_energy']:
                    await db("""UPDATE user_settings SET current_energy = $1 WHERE user_id = $2""",
                            min((user['current_energy']+user['passive_energy']),user['max_energy']),
                             user['user_id'])
                await db("""UPDATE user_settings SET sand_dollars = sand_dollars + $1 WHERE user_id = $2""",
                         user['passive_sand_dollars'],
                         user['user_id'])

    @energy_loop.before_loop
    async def before_energy_loop(self):
        await self.bot.wait_until_ready()


    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="tool_type",
                    type=discord.ApplicationCommandOptionType.string,
                    description="The type of tool you wish to use",
                    choices=[
                        discord.ApplicationCommandOptionChoice(
                            name="Net (used for keeping fish)", value="Net"
                        ),
                        discord.ApplicationCommandOptionChoice(
                            name="Fishing Rod (used for selling fish)", value="Fishing Rod"
                        ),
                        discord.ApplicationCommandOptionChoice(
                            name="Speargun (used for getting bait and items)", value="Speargun"
                        ),
                    ],
                    required=False,
                ),
            ]
        )
    )
    @commands.bot_has_permissions(send_messages=True)
    async def fish(self, ctx: vbu.SlashContext, tool_type: str = None):
        """Catch a fish to keep with a net, to sell with a rod, or for bait with a speargun"""
        #await utils.start_using(ctx, self.bot)
        async with vbu.Database() as db:
            # await db("""INSERT INTO user_settings (user_id) VALUES ($1)""",
            #          ctx.author.id)
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
            user_baits = await db(
                """SELECT * FROM user_item_inventory WHERE user_id = $1""",
                ctx.author.id
            )
        components = discord.ui.MessageComponents()
        current_tool = 'Net' #user_settings[0]['current_tool'].replace("_"," ").title()
        if tool_type:
            current_tool = tool_type
        components = discord.ui.MessageComponents(
            discord.ui.ActionRow(
                discord.ui.Button(custom_id="fish", label="Fish"),
                discord.ui.Button(custom_id="change_tool", label="Change Tool"),
                discord.ui.Button(custom_id="close_menu", label="Close Menu")
            )
        )
        async def change_tool(current_tool, user_settings):
            components.get_component('fish').enable()
            embed = discord.Embed()
            embed.add_field(name="Current Tool", value=current_tool)
            embed.add_field(name="Current Buffs", value="None (WIP)") #get_net/rod/speargun_buffs()
            if current_tool == "Net":
                embed.add_field(name="Tool Explanation", value="The net is used to catch fish to add to your collection. Not for selling or getting bait.", inline=False)
                embed.add_field(name="Net Material:", value=user_settings[0]['net_type'].replace("_"," ").title())
                embed.add_field(name="Net HP:", value=user_settings[0]['net_hp'])
                if not user_settings[0]['has_net']:
                    components.get_component('fish').disable()
                    embed.add_field(name="Your net has broken! use /shop to buy a new one!", value="** **")
            if current_tool == "Fishing Rod":
                bait_string = f"{user_baits[0]['common_bait']}/{user_baits[0]['uncommon_bait']}/{user_baits[0]['rare_bait']}/{user_baits[0]['epic_bait']}"
                embed.add_field(name="Tool Explanation", value="The fishing rod is used to catch fish to sell (Using higher quality bait gets you high quality fish). Not for adding fish to collection or getting bait", inline=False)
                embed.add_field(name="Bait Type", value="Common/Uncommon/Rare/Epic")
                embed.add_field(name="Bait Amount", value=bait_string)
            if current_tool == "Speargun":
                embed.add_field(name="Tool Explanation", value="The speargun is used to catch fish for bait. Not for adding fish to collection or selling.", inline=False)
                embed.add_field(name="Current Energy", value=user_settings[0]['current_energy'])
                embed.add_field(name="Max Energy", value=user_settings[0]['max_energy'])
            return embed
        embed = await change_tool(current_tool, user_settings)
        message = await ctx.send(embed=embed, components=components)
        
        menu_open = True
        while menu_open:
            try:
                chosen_button_payload = await self.bot.wait_for(
                    "component_interaction", timeout=120, check=lambda p: p.user.id == ctx.author.id
                    and p.message.id == message.id,
                )
                fish_chosen_button_payload = chosen_button_payload
                chosen_button = chosen_button_payload.component.custom_id
            except asyncio.TimeoutError:
                await message.edit(components=components.disable_components())
                chosen_button = ""
                menu_open = False

            
            if chosen_button == "change_tool":
                await chosen_button_payload.response.defer_update()
                options = ["Net", "Fishing Rod", "Speargun", "Cancel"]
                options.remove(current_tool)
                new_tool = await utils.create_select_menu(self.bot, ctx, options, "tool", "change to", True)
                if new_tool != "Cancel":
                    current_tool = new_tool
                new_embed = await change_tool(current_tool, user_settings)
                await message.edit(embed=new_embed, components=components)
            elif chosen_button == "fish":
                await chosen_button_payload.response.defer_update()
                keep_fishing = True
                fish_components = discord.ui.MessageComponents(
                    discord.ui.ActionRow(
                    discord.ui.Button(custom_id="fish", label="Fish Again"),
                    discord.ui.Button(custom_id="stop", label="Stop")
                    )
                )
                if tool_type == "Fishing Rod":
                    curr_money = user_settings[0]['sand_dollars']
                else:
                    curr_money = user_settings[0]['current_energy']
                while keep_fishing:
                    
                    returned_message, curr_money = await utils.fish(ctx,self.bot,current_tool, user_settings, user_baits, curr_money)
                    async with vbu.Database() as db:
                        user_baits = await db(
                            """SELECT * FROM user_item_inventory WHERE user_id = $1""",
                            ctx.author.id
                        )
                        user_settings = await db(
                            """SELECT * FROM user_settings WHERE user_id = $1""",
                            ctx.author.id,
                        )
                    new_embed = await change_tool(current_tool, user_settings)
                    await message.edit(embed=new_embed, components=components)
                    fish_message = await ctx.send(returned_message, components=fish_components)

                    try:
                        fish_chosen_button_payload = await self.bot.wait_for(
                            "component_interaction", timeout=60.0, check=lambda p: p.user.id == ctx.author.id and p.message.id == fish_message.id)
                        chosen_button = fish_chosen_button_payload.component.custom_id.lower()
                    except asyncio.TimeoutError:
                        keep_fishing = False
                    if chosen_button == "stop":
                        keep_fishing = False
                        await fish_chosen_button_payload.response.defer_update()
                    await fish_message.delete()
                async with vbu.Database() as db:
                    await db("""UPDATE user_settings SET sand_dollars = $1 WHERE user_id = $2""",
                        curr_money,
                        ctx.author.id)
                    user_settings = await db("""UPDATE user_settings SET current_energy = $1 WHERE user_id = $2 RETURNING *""",
                        curr_money,
                        ctx.author.id
                        )
            elif chosen_button == "close_menu":
                await chosen_button_payload.response.defer_update()
                menu_open = False
                await message.delete()
            
def setup(bot):
    bot.add_cog(Fishing(bot))