import random
import asyncio
import discord
from datetime import datetime as dt, timedelta
from discord.ext import commands, tasks, vbu

from cogs import utils
from cogs.utils._fish import _Fish_Species


class Arena(vbu.Cog):

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
        )
    )
    @commands.bot_has_permissions(send_messages=True)
    async def test_create(self, ctx: commands.Context):
        fish_selected = 0
        embed = discord.Embed(title="Created Team!")
        embed.add_field(name="Fish Names", value="No Fish Selected")
        embed.add_field(name="Fish Regions", value="No Fish Selected")
        embed.add_field(name="Fish Classes", value="No Fish Selected")
        embed.add_field(name="Fish Selected", value=fish_selected)
        embed_message = await ctx.send(embed=embed)
        
        fish_names = []
        fish_rarities = []
        fish_regions = {}
        fish_classes = {}
        while (fish_selected != 5):
            
            rarity = await utils.create_select_menu(self.bot, ctx, ["Uncommon", "Rare", "Epic", "Legendary"], "rarity", "select", True)
            if rarity not in ["Uncommon", "Rare", "Epic", "Legendary"]:
                return
            fish_rarities.append(rarity)
            first_fish_options = [single_fish.name.replace('_', ' ').title() for single_fish in _Fish_Species.get_fish_by_rarity(rarity.lower())]
            for fish_name in fish_names:
                if fish_name.replace('_', ' ').title() in first_fish_options:
                    first_fish_options.remove(fish_name.replace('_', ' ').title())
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

            fish = _Fish_Species.get_fish(fish.replace(' ', '_').lower())
            fish_names.append(fish.name)
            for region in fish.region:
                if region.name not in fish_regions.keys():
                    fish_regions[region.name] = 1
                else:
                    fish_regions[region.name] += 1
            for fish_class in fish.fish_class:
                if fish_class.name not in fish_classes.keys():
                    fish_classes[fish_class.name] = 1
                else:
                    fish_classes[fish_class.name] += 1
            region_string = ""
            fish_class_string = ""
            fish_name_string = ""
            check = False
            for region_key, region_num in fish_regions.items():
                if region_num >= utils.Region.get_region(region_key).breakpoints[0]:
                    region_string += "**"
                    check = True
                region_string += f"{region_key.replace('_', ' ').title()}: {region_num}\n"
                if (check):
                    region_string += f"** *({utils.Region.get_region(region_key).description})*\n"
                    check = False
            for fish_class_key, fish_class_num in fish_classes.items():
                if fish_class_num >= utils.Fish_Class.get_fish_class(fish_class_key).breakpoints[0]:
                    fish_class_string += "**"
                    check = True
                fish_class_string += f"{fish_class_key.replace('_', ' ').title()}: {fish_class_num}\n"
                if (check):
                    fish_class_string += f"** *({utils.Fish_Class.get_fish_class(fish_class_key).description})*\n"
                    check = False
            for count, name in enumerate(fish_names):
                fish_name_string += f"({fish_rarities[count][0]}) {name.replace('_', ' ').title()}\n"
            new_embed = discord.Embed(title="Created Team! Bolded traits are **active**")
            new_embed.add_field(name="Fish Names", value=fish_name_string)
            new_embed.add_field(name="Fish Regions", value=region_string)
            new_embed.add_field(name="Fish Classes", value=fish_class_string)
            await embed_message.edit(embed=new_embed)
            fish_selected += 1

def setup(bot):
    bot.add_cog(Arena(bot))