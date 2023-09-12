import random
import asyncio
import discord
from datetime import datetime as dt, timedelta
from discord.ext import commands, tasks, vbu

from cogs import utils


class Fishing(vbu.Cog):
    
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
                            name="Speargun WIP (used for getting bait)", value="Speargun WIP"
                        ),
                    ],
                    required=False,
                ),
            ]
        )
    )
    @commands.bot_has_permissions(send_messages=True)
    async def fish(self, ctx: commands.Context, tool_type: str = None):
        """fish for a fish
        /fish (optional tool)
        menu with current buffs, current tool
        (if net, show space available for caught fish, current net type, and current net HP,
        if rod, show current bait amount, if speargun, show current energy)
        buttons with change tool and fish
        *change tool    
            pops up a menu asking which tool they would like to switch to
            dropdown with two other tools plus cancel
        *fish
            *net
                cost: net breaks and keeps needing bought
                show fish image and current net tier plus HP
                buttons for catch and for release
                *catch
                    pull up menu with random generated name, asking if they 
                    would like to set a name or keep the randomly generated 
                    one.
                    *keep name closes menu
                    *rename
                        opens a modal asking for new name for the fish
                *release closes menu
            *fishing rod
                cost: nothing but can be upgraded by having bait
                show fish image, how much bait
                button for reel
                *reel
                    shows fish you caught and what it sold for
            *speargun
                cost: energy(?)
                show fish image and current energy
                button for fillet and for sell
                *fillet
                    turns the fish into bait for fishing rod
                *sell
                    sells the fish for a lot of money
        """
        #await utils.start_using(ctx, self.bot)
        async with vbu.Database() as db:
            # await db("""INSERT INTO user_settings (user_id) VALUES ($1)""",
            #          ctx.author.id)
            user_settings = await db(
                """SELECT * FROM user_settings WHERE user_id = $1""",
                ctx.author.id,
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
                    embed.add_field(name="Your net has broken!", value="** **")
            if current_tool == "Fishing Rod":
                bait = await utils.get_bait(user_settings[0]['bait_amount'])
                embed.add_field(name="Tool Explanation", value="The fishing rod is used to catch fish to sell (Using higher quality bait gets you high quality fish). Not for adding fish to collection or getting bait", inline=False)
                bait_type_string = ""
                bait_amount_string = ""
                for type_bait in bait[0]:
                    bait_type_string += f"{type_bait}"
                    bait_amount_string += f"{bait[1][bait[0].index(type_bait)]}"
                    if type_bait != bait[0][len(bait[0])-1]:
                        bait_type_string+="/"
                        bait_amount_string+="/"
                embed.add_field(name="Bait Type", value=bait_type_string)
                embed.add_field(name="Bait Amount", value=bait_amount_string)
            if current_tool == "Speargun WIP":
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
                options = ["Net", "Fishing Rod", "Speargun WIP", "Cancel"]
                options.remove(current_tool)
                new_tool = await utils.create_select_menu(self.bot, ctx, options, "tool", "change to", True)
                if new_tool != "Cancel":
                    current_tool = new_tool
                print(current_tool)
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
                while keep_fishing:
                    
                    returned_message = await utils.fish(ctx,self.bot,current_tool, user_settings)
                    async with vbu.Database() as db:
                        user_settings = await db(
                            """SELECT * FROM user_settings WHERE user_id = $1""",
                            ctx.author.id,
                        )
                    new_embed = await change_tool(current_tool, user_settings)
                    await message.edit(embed=new_embed, components=components)
                    fish_message = await ctx.send(returned_message, components=fish_components)

                    try:
                        fish_chosen_button_payload = await self.bot.wait_for(
                            "component_interaction", timeout=60.0, check=lambda p: p.user.id == ctx.author.id)
                        chosen_button = fish_chosen_button_payload.component.custom_id.lower()
                    except asyncio.TimeoutError:
                        keep_fishing = False
                    if chosen_button == "stop":
                        keep_fishing = False
                        await fish_chosen_button_payload.response.defer_update()
                    await fish_message.delete()
        
            elif chosen_button == "close_menu":
                await chosen_button_payload.response.defer_update()
                menu_open = False
            
        

def setup(bot):
    bot.add_cog(Fishing(bot))