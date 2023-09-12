import asyncio
import random
import discord
from discord.ext import vbu
from cogs import utils
import math
from ._fish import _Fish_Species

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

fish_prices = {
        "common": 1,
        "uncommon": 2,
        "rare": 5,
        "epic": 10,
        "legendary": 25,
        "mythic": 50
        }
bait_values = {
    "Common": 1,
    "Uncommon": 2,
    "Rare": 3,
    "Epic": 4,
}

fish_path = "C:\\Users\\johnt\\Pictures\\fish"
def get_small_fish(rarity_tier):
    rarity = random.choices(("common","uncommon","rare","epic","legendary","mythic"),rarity_chances[rarity_tier])
    print(rarity[0])
    fish_options = _Fish_Species.get_fish_by_rarity(rarity[0])
    caught_fish = random.choice(tuple(fish_options))
    return caught_fish

async def add_xp(ctx, bot, current_xp, max_xp, level, fish_object, user_settings):
    rarities = ['legendary', 'epic', 'rare', 'uncommon', 'common']
    current_xp = current_xp+1
    if current_xp==max_xp:
        level +=1
        current_xp=0
        max_xp=5*level+max_xp
        if level % utils.lever_info[fish_object.lever][1][rarities.index(fish_object.rarity)] == 0:
            async with bot.database() as db:
                db_call = "UPDATE user_settings SET {0} = $1 + {1} WHERE user_id = $2"
                await db(
                    db_call.format(fish_object.lever, 
                            utils.lever_info[fish_object.lever][0]), 
                        user_settings[0][fish_object.lever], 
                        ctx.author.id
                )
    return current_xp,max_xp,level

async def fish(ctx, bot, current_tool, user_settings):
    if current_tool == "Net":
        async with bot.database() as db:
            fish_data = await db("""SELECT * FROM user_fish_inventory WHERE user_id = $1""",
                                    ctx.author.id)
        if user_settings[0]['net_type'] == "none":
            return "You have no net!"
        caught_fish = get_small_fish(user_settings[0]['rarity_increase_tier'])
        if user_settings[0]['user_id'] == 449966150898417664:
            caught_fish = _Fish_Species.get_fish("drakefish")
        net_hp = user_settings[0]["net_hp"]
        net_type = user_settings[0]["net_type"]
        caught_check = False
        for fish in fish_data:
            if fish['species'] == caught_fish.name:
                caught_check = True
                break
        embed = discord.Embed()
        embed.add_field(name="You Caught:", value=f"{caught_fish.name.replace('_', ' ').title()} ({caught_fish.rarity.title()})")
        embed.add_field(name="Fish Owned:", value=f"{caught_check}")
        embed.add_field(name="Passive Tank Bonus", value=caught_fish.lever.replace("_", " ").title(), inline=False)
        if (caught_fish.rarity in ["uncommon", "rare", "epic", "legendary", "mythic"]):
            region_names = ""
            region_descriptions = ""
            class_names = ""
            class_descriptions = ""
            for region in caught_fish.region:
                region_names += f"{region.name.replace('_', ' ').title()}\n"
                region_descriptions += f"{region.description}\n"
            for fish_class in caught_fish.fish_class:
                class_names += f"{fish_class.name.replace('_', ' ').title()}\n"
                class_descriptions += f"{fish_class.description}\n"
            embed.add_field(name=region_names, value=region_descriptions,inline=False)
            embed.add_field(name=class_names, value=class_descriptions,inline=False)

        
        components = discord.ui.MessageComponents(
            discord.ui.ActionRow(
                discord.ui.Button(custom_id="catch", label="Catch"),
                discord.ui.Button(custom_id="release", label="Release")
            )
        )
        if net_hp == 0:
            net_type = "none"
            async with bot.database() as db:
                await db("""UPDATE user_settings SET net_type = $1, has_net = FALSE, net_hp = $2 WHERE user_id = $3""",
                            net_type,
                            net_hp,
                            ctx.author.id)
            return "You have no net!"
        fish_file = discord.File(fish_path+"\\"+caught_fish.rarity+"\\"+caught_fish.name+"-export.png", "new_fish.png")
        embed.set_image(url="attachment://new_fish.png")
        fish_message = await ctx.send(embed=embed, file=fish_file, components=components)
        def button_check(payload):
            if payload.message.id != fish_message.id:
                return False
            return payload.user.id == ctx.author.id
        
        fish_button_payload = await bot.wait_for(
            "component_interaction", check=button_check
        )
        chosen_button = fish_button_payload.component.custom_id

        if chosen_button == "release":
            await fish_message.delete()
            return "Fish has been released!"
        elif chosen_button == "catch":
            await fish_message.delete()
            owned_fish = None
            for fish in fish_data:
                if fish['species'] == caught_fish.name:
                    owned_fish = fish
                    break
            async with bot.database() as db:
                await db("""UPDATE user_settings SET net_hp = $1 WHERE user_id = $2""",
                            net_hp-1,
                            ctx.author.id)
                if owned_fish:
                    new_xp, new_max_xp,new_level = await add_xp(ctx, bot, owned_fish['current_xp'], owned_fish['max_xp'], owned_fish['level'], caught_fish, user_settings)
                    await db("""UPDATE user_fish_inventory SET current_xp = $1, max_xp = $2, level = $3 WHERE user_id = $4 AND species = $5""",
                             new_xp,
                             new_max_xp,
                             new_level,
                             ctx.author.id,
                             caught_fish.name)
                    return f"Your fish has been upgraded: Level {new_level} {new_xp}/{new_max_xp}"
                else:
                    await db("""INSERT INTO user_fish_inventory(user_id, name, species) VALUES ($1, 'WIP', $2)""",
                                ctx.author.id,
                                caught_fish.name)
                    return "Your fish has been added to your collection!"
            
    if current_tool == "Fishing Rod":
        bait_modifier = 0
        bait = await get_bait(user_settings[0]['bait_amount'])
        used_bait = "no"
        for bait_type in bait[0]:
            if bait[1][bait[0].index(bait_type)] != 0:
                used_bait = bait_type
        if used_bait != "no":
            bait_modifier = bait_values[used_bait]
            async with bot.database() as db:
                await db(
                    """UPDATE user_settings SET bait_amount = $1 WHERE user_id = $2""",
                    utils.remove_bait(bait, used_bait),
                    ctx.author.id
                )
        caught_fish = get_small_fish(user_settings[0]['rarity_increase_tier']+bait_modifier)

        embed = discord.Embed()
        embed.add_field(name="You Caught:", value=f"{caught_fish.name.replace('_', ' ').title()} ({caught_fish.rarity.title()})\nUsed {used_bait} bait")
        embed.add_field(name="Sold fish for:", value=f"{fish_prices[caught_fish.rarity]} Sand Dollars.")
        fish_file = discord.File(fish_path+"\\"+caught_fish.rarity+"\\"+caught_fish.name+"-export.png", "new_fish.png")
        embed.set_image(url="attachment://new_fish.png")
        fish_message = await ctx.send(embed=embed, file=fish_file)
        await fish_message.delete(delay=5)
        async with bot.database() as db:
            await db("""UPDATE user_settings SET sand_dollars = $1 WHERE user_id = $2""",
                        user_settings[0]["sand_dollars"]+fish_prices[caught_fish.rarity],
                        ctx.author.id)
        return f"You have {user_settings[0]['sand_dollars']+fish_prices[caught_fish.rarity]} total sand dollars!"
async def get_bait(bait_string: str):
    baits = bait_string.split("_")
    baits = list(map(int, baits))
    return [["Common", "Uncommon", "Rare", "Epic"], baits]