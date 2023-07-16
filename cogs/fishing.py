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
                            name="Net (used for keeping fish)", value="net"
                        ),
                        discord.ApplicationCommandOptionChoice(
                            name="Fishing Rod (used for selling fish)", value="fishing_rod"
                        ),
                        discord.ApplicationCommandOptionChoice(
                            name="Speargun (used for getting bait)", value="speargun"
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
        components = discord.ui.MessageComponents(
            discord.ui.ActionRow(
                discord.ui.Button(custom_id="fish", label="Fish"),
                discord.ui.Button(custom_id="change_tool", label="Change Tool")
            )
        )
        def change_tool(current_tool):
            embed = discord.Embed()
            embed.add_field(name="Current Buffs", value="None (WIP)") #get_net/rod/speargun_buffs()
            embed.add_field(name="Current Tool", value=current_tool)
            if current_tool == "Net":
                embed.add_field(name="Net Type:", value=user_settings[0]['net_type'].replace("_"," ").title())
                embed.add_field(name="Net HP:", value=user_settings[0]['net_hp'])
                if not user_settings[0]['has_net']:
                    components.get_component('catch').disable()
            if current_tool == "Fishing Rod":
                bait = utils.get_bait(user_settings[0]['bait_amount'])
                embed.add_field(name="Bait Type", value=bait[0])
                embed.add_field(name="Bait Amount", value=bait[1])
            if current_tool == "Speargun":
                embed.add_field(name="Current Energy", value=user_settings[0]['current_energy'])
                embed.add_field(name="Max Energy", value=user_settings[0]['max_energy'])
            return embed
        embed = change_tool(current_tool)
        message = await ctx.send(embed=embed, components=components)
        
        def button_check(payload):
            if payload.message.id != message.id:
                return False
            return payload.user.id == ctx.author.id
        
        while True:
            chosen_button_payload = await self.bot.wait_for(
                "component_interaction", check=button_check
            )
            chosen_button = chosen_button_payload.component.custom_id

            if chosen_button == "change_tool":
                options = ["Net", "Fishing Rod", "Speargun", "Cancel"]
                options.remove(current_tool)
                new_tool = await utils.create_select_menu(self.bot, ctx, options, "tool", "change to", True)
                if new_tool != "cancel":
                    current_tool = new_tool
                new_embed = change_tool(current_tool)
                await message.edit(embed=new_embed)
            elif chosen_button == "fish":
                await utils.fish(ctx,self.bot,current_tool, user_settings)


def setup(bot):
    bot.add_cog(Fishing(bot))