import asyncio
import random
import discord
from discord.ext import vbu
from cogs import utils
import math

rarity_chances = [
    (0,0,0,0,0,0),

    (.900,.075,.025,0,0,0),
    (.880,.091,.029,0,0,0), #-.020,+.016,+.004,+0,+0,+0
    (.860,.107,.033,0,0,0), #-.020,+.016,+.004,+0,+0,+0
    (.840,.123,.037,0,0,0), #-.020,+.016,+.004,+0,+0,+0
    (.815,.141,.043,.001,0,0), #-.025,+.018,+.006,+.001,+0,+0
    (.790,.159,.049,.002,0,0), #-.025,+.018,+.006,+.001,+0,+0
    (.775,.177,.055,.003,0,0), #-.025,+.018,+.006,+.001,+0,+0
    (.760,.195,.061,.004,0,0), #-.025,+.018,+.006,+.001,+0,+0
    (.745,.213,.067,.005,0,0), #-.025,+.018,+.006,+.001,+0,+0
    (.715,.233,.074,.007,.001,0), #-.030,+.020,+.007,+.002,+.001,+0

    (.685,.253,.081,.009,.002,0), #-.030,+.020,+.007,+.002,+.001,+0
    (.655,.273,.088,.011,.003,0), #-.030,+.020,+.007,+.002,+.001,+0
    (.625,.293,.095,.013,.004,0), #-.030,+.020,+.007,+.002,+.001,+0
    (.595,.313,.102,.015,.005,0), #-.030,+.020,+.007,+.002,+.001,+0
    (.560,.334,.110,.018,.007,.001), #-.035,+.021,+.008,+.003,+.002,+.001
    (.525,.355,.118,.021,.009,.002), #-.035,+.021,+.008,+.003,+.002,+.001
    (.490,.376,.126,.024,.011,.003), #-.035,+.021,+.008,+.003,+.002,+.001
    (.455,.397,.134,.027,.013,.004), #-.035,+.021,+.008,+.003,+.002,+.001
    (.420,.418,.142,.030,.015,.005), #-.035,+.021,+.008,+.003,+.002,+.001
    (.385,.439,.150,.033,.017,.006), #-.035,+.021,+.008,+.003,+.002,+.001

]

fish_list = {
    "common": {
        "small": ["american_lobster", "black_crappie"],
    },
    "uncommon": {
        "small": ["bluegill"],
    },
    "rare":  {
        "small": ["crown_jellyfish"],
    },
    "epic":  {
        "small": ["seahorse"],
    },
    "legendary":  {
        "small": ["starfish"],
    },
    "mythic":  {
        "small": ["royal_blue_tang"],
    },
}

fish_path = "C:\\Users\\johnt\\Pictures\\fish\\"
def get_net_fish(rarity_tier):
    rarity = random.choices(("common","uncommon","rare","epic","legendary","mythic"),rarity_chances[rarity_tier])
    caught_fish = random.choice(fish_list[rarity[0]]["small"])
    return caught_fish, rarity[0]

async def fish(ctx, bot, current_tool, user_settings):
    if current_tool == "Net":
        caught_fish, rarity = get_net_fish(user_settings[0]['rod_rarity_increase_tier'])
        net_hp = user_settings[0]["net_hp"] - 1
        net_type = user_settings[0]["net_type"]
        has_net = True
        break_message = "** **"
        embed = discord.Embed()
        embed.add_field(name=f"You Caught: {caught_fish.replace('_', ' ').title()} ({rarity.title()})", value="** **")
        embed.add_field(name=f"Net: {net_type.replace('_', ' ').title()}",value=f"Net HP: {net_hp}")
        if net_hp == 0:
            net_type = "none"
            has_net = False
            break_message = "Your net has broken!"
        embed.add_field(name=break_message, value="** **")
        components = discord.ui.MessageComponents(
            discord.ui.ActionRow(
                discord.ui.Button(custom_id="catch", label="Catch"),
                discord.ui.Button(custom_id="release", label="Release")
            )
        )
        fish_file = discord.File(fish_path+caught_fish+".png", "new_fish.png")
        embed.set_image(url="attachment://new_fish.png")
        message = await ctx.send(embed=embed, file=fish_file, components=components)

        def button_check(payload):
            if payload.message.id != message.id:
                return False
            return payload.user.id == ctx.author.id
        
        while True:
            chosen_button_payload = await bot.wait_for(
                "component_interaction", check=button_check
            )
            chosen_button = chosen_button_payload.component.custom_id

            if chosen_button == "release":
                await message.delete()
            elif chosen_button == "catch":
                await message.delete()


async def get_bait(bait_string: str):
    baits = bait_string.split("_")
    baits = list(map(int, baits))
    return (("Common", "Uncommon", "Rare", "Epic"), baits)