import asyncio
import random
import discord
from discord.ext import vbu
from cogs import utils
from ._fish import _Fish_Species
import math
from PIL import Image, PngImagePlugin
import io
import typing

EMOJIS = {
    "common_xp_orb": "<:common_xp_orb:1151075696223998002>",
    "uncommon_xp_orb": "<:uncommon_xp_orb:1151075716562161706>",
    "rare_xp_orb": "<:rare_xp_orb:1151075730407567380>",
    "epic_xp_orb": "<:epic_xp_orb:1151075745645461514>",
    "legendary_xp_orb": "<:legendary_xp_orb:1151075757544706078>",
    "mythic_xp_orb": "<:mythic_xp_orb:1151075766256279563>",
    "common_bait": "<:common_bait:1151076122029723648>",
    "uncommon_bait": "<:uncommon_bait:1151076139478032394>",
    "rare_bait": "<:rare_bait:1151076153562513489>",
    "epic_bait": "<:epic_bait:1151076163821781012>",
    "wooden_net": "<:wooden_net:1151076184885571615>",
    "plastic_net": "<:plastic_net:1151076197833396266>",
    "metal_net": "<:metal_net:1151076208088469584>",
    "coral": "<:coral:1174244030792609883>",
    "shell": "<:shell:1174244037050511380>",
    "crab_claw": "<:crab_claw:1174244031572746260>",
    "pebble": "<:pebble:1174244032394821723>",
    "scale": "<:scale:1174244034831712296>",
    "seaweed": "<:seaweed:1174244035460878378>",
    "tire": "<:tire:1174244039181221980>",
    "plastic_bag": "<:plastic_bag:1174244033661505537>",
    "boot": "<:boot:1174244028410249286>",
}

VALID_ITEMS = [
                "common_xp_orb", "uncommon_xp_orb", "rare_xp_orb", 
                "epic_xp_orb", "legendary_xp_orb", "mythic_xp_orb", 
                "common_bait", "uncommon_bait", "rare_bait", "epic_bait", 
                "coral", "shell", "crab_claw", "pebble", "scale", "seaweed", 
                "tire", "plastic_bag", "boot"
            ]



ranks = ["Iron 1", "Iron 2", "Iron 3", "Iron 4", 
         "Bronze 1", "Bronze 2", "Bronze 3", "Bronze 4", 
         "Silver 1", "Silver 2", "Silver 3", "Silver 4",
         "Gold 1", "Gold 2", "Gold 3", "Gold 4",
         "Platinum 1", "Platinum 2", "Platinum 3", "Platinum 4", 
         "Diamond 1", "Diamond 2", "Diamond 3", "Diamond 4"]
skin_common_path = "C://Users//johnt//Pictures//fish//skins//"
# This is used to fix fields that are too long (i.e. If someone has too many of one rarity in their fish bucket)
def get_fixed_field(field: tuple[str,str]) -> list[tuple[str,str]]:
    """
    Return a list of tuples for the rarity-level in the pagination to fix fields that are too large
    """

    # This gets the main part of the field that will be put into an embed in a list of each time new line is given
    fish_string_split = field[1].split("\n")

    # Initializes the fixed field list, current string string, and fish char sum
    fixed_field = []
    current_string = ""
    fish_character_sum = 0

    # For each new line segment. The part of a bucket that says:
    # "Red": Red Betta (Size: Small, Alive: True)
    for index, fish_string in enumerate(fish_string_split):

        # Find the length of that piece with the new line
        fish_character_sum += len("\n" + fish_string)

        # If it gets to a point where the sum is less than 1020...
        if fish_character_sum < 1020:

            # Add the current string and new line to "current string"
            current_string += "\n" + fish_string
            # If it's the last string in the field...
            if index == len(fish_string_split) - 1:

                # Add it to the new field with the original starting part
                fixed_field.append((field[0], current_string))

        # Else if it's greater...
        else:

            # Add it to the new field with the original starting part
            fixed_field.append((field[0], current_string))
            # Set the current string to "current string"
            current_string = "\n" + fish_string
            # Set the sum back to 0
            fish_character_sum = len("\n" + fish_string)

    # If there was nothing sent to fixed field...
    if not fixed_field:

        # Simply don't change the field and send it back
        fixed_field = [field]

    # Send the fixed field
    return fixed_field


# Puts together an embed based on the field given


def create_bucket_embed(
    user: discord.Member | discord.User,
    field: tuple[str, str],
    page: int,
    custom_title: str = None
) -> discord.Embed:
    """
    Creates the embed for the pagination page for the fishbucket
    """

    # Creates a new embed
    embed = discord.Embed()

    # Sets the title to the custom title or just "user's fish bucket"
    embed.title = custom_title or f"**{user.display_name}'s Fish Bucket**\n"

    # Sets the name of the field to the first part of the given field, then the value to the second part
    embed.add_field(name=f"__{field[0]}__", value=field[1], inline=False)
    embed.set_footer(text=f"Page {page}")

    # Returns the field
    return embed


# This takes in the ctx, all of the fields for the embed, the user, and the custom title
async def paginate(
        ctx: vbu.SlashContext, 
        fields: list[tuple[str,str]], 
        user: discord.Member | discord.User, 
        select: bool, 
        options: list[str]=None, 
        custom_str: str=None
) -> None | str:

    # intiiates bot as ctx.bot
    bot: vbu.Bot = ctx.bot
    # Sets the current index to 1
    curr_index = 1
    # Sets the current field to be the first field
    curr_field = fields[curr_index - 1]
    # Creates the first embed

    embed = create_bucket_embed(user, curr_field, curr_index, custom_str)

    # Set up the buttons for pagination
    left = discord.ui.Button(
        custom_id="left", emoji="◀️", style=discord.ui.ButtonStyle.primary
    )
    right = discord.ui.Button(
        custom_id="right", emoji="▶️", style=discord.ui.ButtonStyle.primary
    )
    stop = discord.ui.Button(
        custom_id="stop", emoji="⏹️", style=discord.ui.ButtonStyle.danger
    )
    numbers = discord.ui.Button(
        custom_id="numbers", emoji="🔢", style=discord.ui.ButtonStyle.primary
    )
    select_button = discord.ui.Button(
        custom_id="select", label="Select", style=discord.ui.ButtonStyle.primary
    )
    # Set up the valid buttons to be the first 3 always
    valid_buttons = [left, right, stop]
    # Then if theres more than one page, add numbers
    if len(fields) > 1:
        valid_buttons.append(numbers)
    if select:
        valid_buttons.append(select_button)

    # Put the buttons together
    components = discord.ui.MessageComponents(
        discord.ui.ActionRow(*valid_buttons))

    # Send the message
    fish_message = await ctx.send(embed=embed, components=components)

    # Check to see if the button is...
    def button_check(payload):

        # The correct message
        if payload.message.id != fish_message.id:
            return False
        # The correct button
        if payload.component.custom_id in [
            left.custom_id,
            right.custom_id,
            stop.custom_id,
            numbers.custom_id,
        ]:
            bot.loop.create_task(payload.response.defer_update())
        # The correct user
        return payload.user.id == ctx.author.id

    while True:  # Keep paginating until the user clicks stop

        # Check to see if they...
        try:

            # Click a button, it works with the button check, and it doesnt time out
            chosen_button_payload = await bot.wait_for(
                "component_interaction", timeout=60.0, check=button_check
            )
            # Set the chosen button to be the id
            chosen_button = chosen_button_payload.component.custom_id.lower()

        # If it times out...
        except asyncio.TimeoutError:

            # The chosen button is set to stop
            chosen_button = "stop"

        # A dict that sets left to be one to the left of the current field, and right to be one to the right of it,
        # but not go too far left or right
        index_chooser = {
            "left": max(1, curr_index - 1),
            "right": min(len(fields), curr_index + 1),
        }

        # If the button is left or right...
        if chosen_button in index_chooser.keys():

            # Set the index to be the correct in bounds index
            curr_index = index_chooser[chosen_button]
            # Set the field to be the corresponding field
            curr_field = fields[curr_index - 1]
            # Edit the embed with the new page
            await fish_message.edit(
                embed=create_bucket_embed(
                    user, curr_field, curr_index, custom_str)
            )

        # If the button is stop...
        elif chosen_button == "stop":

            # Disable all the components
            await fish_message.edit(components=components.disable_components())
            # End the while loop
            break

        # If the button is numbers and theres more than one field...
        elif chosen_button == "numbers" and len(fields) > 1:

            # Ask the user what page they want to go to
            pages_string = f"go to? (1-{len(fields)})"
            page_selected = await utils.create_select_menu(
                bot, ctx, range(1, len(fields) + 1), "page", pages_string
            )

            user_input = int(page_selected)

            # Set the current index to be the one the user says
            curr_index = min(len(fields), max(1, user_input))
            # Set the field to the corresponding one
            curr_field = fields[curr_index - 1]

            # Edit the message with the new field
            await fish_message.edit(
                embed=create_bucket_embed(
                    user, curr_field, curr_index, custom_str)
            )
        elif chosen_button == "select":
            return await create_select_menu(bot, ctx, options[curr_index-1], "item", "select", True)


async def create_select_menu(
        bot: vbu.Bot, 
        ctx: vbu.SlashContext, 
        option_list: list[str], 
        type_noun: str, 
        type_verb: str, 
        remove: bool =False
) -> typing.Any:
    """
    This will create a select menu from the given list,
    have the user select one, and return the selection
    """

    # Initiates the option list
    test_options = []

    # For each name that isnt "" add it as an option for the select menu
    for option in option_list:
        if option != "" and len(test_options) < 25:
            test_options.append(discord.ui.SelectOption(
                label=option, value=option))

    # Set the select menu with the options
    components = discord.ui.MessageComponents(
        discord.ui.ActionRow(
            discord.ui.SelectMenu(
                custom_id=type_verb,
                options=test_options,
                placeholder="Select an option",
            )
        )
    )

    # Ask them what they want to do with component
    message = await ctx.send(
        f"What {type_noun} would you like to {type_verb}?",
        components=components,
    )

    # If it's the correct message and author return true
    def check(payload):
        if payload.message.id != message.id:
            return False

        # If its the wrong author send an ephemeral message
        if payload.user.id != ctx.author.id:
            bot.loop.create_task(
                payload.response.send_message(
                    "You can't respond to this message!", ephemeral=True
                )
            )
            return False
        return True

    # If it works don't fail, and if it times out say that
    try:
        payload = await bot.wait_for("component_interaction", check=check, timeout=60)
        await payload.response.defer_update()
    except asyncio.TimeoutError:
        return await ctx.send(
            f"Timed out asking for {type_noun} to " f"{type_verb} <@{ctx.author.id}>"
        )

    # Return what they chose
    if remove == True:
        await message.delete()
    return str(payload.values[0])


async def create_modal(bot: vbu.Bot, Interaction: discord.Interaction, title: str, placeholder: str) -> tuple[str, discord.Interaction] | tuple[None, None]:
    """
    Modal
    """

    # Send a modal back to the user
    await Interaction.response.send_modal(
        (
            sent_modal := discord.ui.Modal(
                title=title,
                components=[
                    discord.ui.ActionRow(
                        discord.ui.InputText(
                            label="Input text label",
                            style=discord.TextStyle.short,
                            placeholder=placeholder,
                            min_length=1,
                            max_length=32,
                        ),
                    ),
                ],
            )
        )
    )

    # Wait for an interaction to be given back
    try:
        interaction: discord.Interaction = await bot.wait_for(
            "modal_submit",
            check=lambda i: i.data["custom_id"] == sent_modal.custom_id,
            timeout=60.0,
        )
    except asyncio.TimeoutError:
        return None, None

    # Go through the response components and get the first (and only) value from the user
    assert interaction.components
    given_value = interaction.components[0].components[0].value

    # Respond with what the user said
    return given_value, interaction


async def sort_by_rarity(user_fish: list[dict]) -> list[_Fish_Species]:
        fish_list = []
        for rarity in ["common", "uncommon", "rare", "epic", "legendary", "mythic"]:
            for fish in user_fish:
                if _Fish_Species.get_fish(fish['species']).rarity == rarity:
                    fish_list.append(_Fish_Species.get_fish(fish['species']))
        return fish_list
    
async def create_dropdown_embed(ctx: vbu.SlashContext, user: discord.Member | discord.User, fish_list: list[_Fish_Species]) -> str | None:
    fish_list_sectioned = []
    fish_sectioned_string = []
    for count, fish in enumerate(fish_list):
        if count%25==0:
            fish_list_sectioned.append([fish.name.replace("_", " ").title()])
            fish_sectioned_string.append(["Fish Inventory\n(Rarity) Name - Lever", f"({fish.rarity[0]}) **{fish.name.replace('_', ' ').title()[:13]}** - *{fish.lever.replace('_', ' ').title()}"[:39].rstrip(" ")+"*"])
        else:
            fish_list_sectioned[int(count/25)].append(fish.name.replace("_", " ").title())
            fish_sectioned_string[int(count/25)][1] += f"\n({fish.rarity[0]}) **{fish.name.replace('_', ' ').title()[:13]}** - *{fish.lever.replace('_', ' ').title()}"[:39].rstrip(" ")+"*"
    
    return await paginate(ctx, fish_sectioned_string, user, True, fish_list_sectioned)

async def get_info(ctx: vbu.SlashContext, fish: str) -> None:
    async with vbu.Database() as db:
        user_fish = await db(
            """SELECT * FROM user_fish_inventory WHERE user_id = $1""",
            ctx.author.id,
        )
        user_items = await db(
            """SELECT * FROM user_item_inventory WHERE user_id = $1""",
            ctx.author.id,
        )
        user_settings = await db(
            """SELECT * FROM user_settings WHERE user_id = $1""",
            ctx.author.id
        )
    components = discord.ui.MessageComponents(
        discord.ui.ActionRow(
            discord.ui.Button(custom_id = "add_fish", label="Add fish to tank"),
            discord.ui.Button(custom_id = "remove_fish", label="Remove fish from tank (Costs 25 Sand Dollars)"),
            discord.ui.Button(custom_id = "add_xp", label="Add XP to fish"),
            discord.ui.Button(custom_id = "change_skin", label="Change fish's skin"),
        )
    )
    
    fish_path = "C:\\Users\\johnt\\Pictures\\fish"
    fish_species = _Fish_Species.get_fish(fish.replace(" ", "_").lower())
    user_fish_data = None
    for single_fish in user_fish:
        if single_fish['species'] == fish.replace(" ", "_").lower():
            user_fish_data = single_fish
            break
    async with vbu.Database() as db:
        fish_skin = await db(
        """SELECT * FROM user_skin_inventory WHERE user_id = $1 AND name = $2 AND fish = $3""",
        ctx.author.id,
        user_fish_data['skin'],
        user_fish_data['species']
            
        )
    if user_items[0][f'{fish_species.rarity}_xp_orb'] == 0:
        components.get_component("add_xp").disable()
    if user_fish_data['in_tank'] or user_fish_data['in_team']:
        components.get_component("add_fish").disable()
    if user_settings[0]['sand_dollars'] < 25 or not user_fish_data['in_tank']:
        components.get_component("remove_fish").disable()
    embed = discord.Embed(title=f"{fish}")
    if user_fish_data['skin'] == "Normal":
        fish_file = discord.File(fish_path+"\\"+fish_species.rarity+"\\"+fish_species.name+"-export.png", "new_fish.png")
    else:
        type = "png"
        if fish_skin[0]['tier'] == 3:
            type = "gif"
        fish_file=discord.File(fish_path+"\\skins\\"+user_fish_data['skin']+"\\"+fish_species.name+"_"+user_fish_data['skin'].lower()+"-export."+type, "new_fish.png")
    if (fish_species.rarity in ["uncommon", "rare", "epic", "legendary", "mythic"]):
        region_names = ""
        region_descriptions = ""
        class_names = ""
        class_descriptions = ""
        item = "None"
        if user_fish_data['item']:
            item = user_fish_data['item']
        for region in fish_species.region:
            region_names += f"{region.name.replace('_', ' ').title()}\n"
            region_descriptions += f"{region.description}\n"
        for fish_class in fish_species.fish_class:
            class_names += f"{fish_class.name.replace('_', ' ').title()}\n"
            class_descriptions += f"{fish_class.description}\n"
        embed.add_field(name=region_names, value=region_descriptions,inline=False)
        embed.add_field(name=class_names, value=class_descriptions,inline=False)
        embed.add_field(name="Item Equipped", value=item)
        embed.add_field(name="In Team", value=user_fish_data['in_team'])
    embed.add_field(name="Passive Bonus", value=fish_species.lever.replace("_", " ").title())
    embed.set_image(url="attachment://new_fish.png")
    embed.add_field(name=f"Level {user_fish_data['level']}: {user_fish_data['current_xp']}/{user_fish_data['max_xp']} XP", value=f"In Tank: {user_fish_data['in_tank']}")
    info_message = await ctx.send(embed=embed, file=fish_file, components = components)
    try:
        fish_chosen_button_payload = await ctx.bot.wait_for(
            "component_interaction", timeout=60.0, check=lambda p: p.user.id == ctx.author.id and p.message.id == info_message.id)
        chosen_button = fish_chosen_button_payload.component.custom_id.lower()
        await fish_chosen_button_payload.response.defer_update()
        if chosen_button == "add_fish":
            rarities = ['legendary', 'epic', 'rare', 'uncommon', 'common']
            async with vbu.Database() as db:
                fish_in_tanks = await db(
                    """SELECT * FROM user_fish_inventory WHERE user_id = $1 AND in_tank = True""",
                    ctx.author.id
                )
            if len(fish_in_tanks) >= user_settings[0]['tank_room']:
                return await ctx.send("You have no tank room!")
            async with vbu.Database() as db:
                db_call = "UPDATE user_settings SET {0} = $1 + {1} WHERE user_id = $2"
                lever_info = utils.lever_info[fish_species.lever]
                
                await db(
                    db_call.format(fish_species.lever, 
                            lever_info[0]*math.ceil(user_fish_data['level']/lever_info[1][rarities.index(fish_species.rarity)])), 
                            user_settings[0][fish_species.lever], 
                            ctx.author.id
                )
                await db(
                    """UPDATE user_fish_inventory SET in_tank = True WHERE user_id = $1 and species = $2""",
                    ctx.author.id,
                    fish.replace(" ", "_").lower()
                )
            await ctx.send("Successfully added to tank.")
        elif chosen_button == "add_xp":
            current, max, level = await utils.add_xp(ctx, ctx.bot, user_fish_data['current_xp'], user_fish_data['max_xp'], user_fish_data['level'], fish_species, user_settings)
            async with vbu.Database() as db:
                await db(
                    """UPDATE user_fish_inventory SET current_xp = $1, max_xp = $2, level = $3 WHERE user_id = $4 and species = $5""",
                    current,
                    max,
                    level,
                    ctx.author.id,
                    fish.replace(" ", "_").lower()
                )
                await db(
                    """UPDATE user_item_inventory SET {0} = $1 WHERE user_id = $2""".format(f"{fish_species.rarity}_xp_orb"),
                    user_items[0][f'{fish_species.rarity}_xp_orb'] - 1,
                    ctx.author.id                    
                )
            await ctx.send(f"Successfully gave your fish 1 xp, they are now Level {level} {current}/{max} XP")
        elif chosen_button == "remove_fish":
            rarities = ['legendary', 'epic', 'rare', 'uncommon', 'common']
            async with vbu.Database() as db:
                db_call = "UPDATE user_settings SET {0} = $1 - {1} WHERE user_id = $2"
                lever_info = utils.lever_info[fish_species.lever]
                
                await db(
                    db_call.format(fish_species.lever, 
                            lever_info[0]*int(user_fish_data['level']/lever_info[1][rarities.index(fish_species.rarity)])), 
                            user_settings[0][fish_species.lever], 
                            ctx.author.id
                )
                await db(
                    """UPDATE user_fish_inventory SET in_tank = False WHERE user_id = $1 and species = $2""",
                    ctx.author.id,
                    fish.replace(" ", "_").lower()
                )
                await db(
                    """UPDATE user_settings SET sand_dollars = sand_dollars - 25 WHERE user_id = $1""",
                    ctx.author.id
                )
            await ctx.send("Successfully removed fish from tank.")
        elif chosen_button == "change_skin":
            skin_options = ["Normal"]
            async with vbu.Database() as db:
                skins = await db("""SELECT * FROM user_skin_inventory WHERE user_id = $1 AND fish = $2""",
                                 ctx.author.id,
                                 fish_species.name)
                for skin in skins:
                    skin_options.append(skin['name'])
                skin = await utils.create_select_menu(ctx.bot, ctx, skin_options, "skin", "select", True)
                if skin in skin_options:
                    await db("""UPDATE user_fish_inventory SET skin = $1 WHERE user_id = $2 AND species = $3""",
                             skin,
                             ctx.author.id,
                             fish_species.name)
                    await db("""UPDATE user_skin_inventory SET equipped = TRUE WHERE user_id = $1 AND name = $2 AND fish = $3""",
                             ctx.author.id,
                             skin,
                             fish_species.name)
        await info_message.edit(components=components.disable_components())
    except asyncio.TimeoutError:
        await info_message.edit(components=components.disable_components())
    


async def create_images(fish: list[typing.Any], settings: list[typing.Any]) -> list[PngImagePlugin.PngImageFile]:

    room = settings[0]['tank_room']
    tanks = []
    tank_images = []
    fish_placements = [(150,150), (500,150), (300, 300), (500,400), (100,300)]
    fish_path = "C:\\Users\\johnt\\Pictures\\fish"
    for single_room in range(room):
        if single_room < len(fish):
            if single_room % 5 == 0:
                tanks.append([fish[single_room]])
            else:
                tanks[int(single_room / 5)].append(fish[single_room])
    for tank in tanks:
        background = Image.open(
                f"{fish_path}\\tank_backgrounds\\default.png"
            )
        fish_images = []
        for num, fish in enumerate(tank):
            fish_image = f"{fish_path}\\{_Fish_Species.get_fish(fish['species']).rarity}\\{fish['species']}.png"
            if fish['skin'] != "Normal":
                fish_image = fish_path+"\\skins\\"+fish['skin']+"\\"+_Fish_Species.get_fish(fish['species']).name+"_"+fish['skin'].lower()+".png"
            background.paste(Image.open(fish_image), 
                             (fish_placements[num][0], fish_placements[num][1]), 
                             Image.open(fish_image)
                            )
        tank_images.append(background)
    
    return tank_images

async def create_tank_embed(ctx: vbu.SlashContext, bot: vbu.Bot, fish: list[typing.Any], images: list[PngImagePlugin.PngImageFile]) -> None:
    fish_list_sectioned = [f"Tank {count+1}" for count in range(len(images))]
    chosen_tank = await create_select_menu(bot, ctx, fish_list_sectioned, "tank", "select", True)
    chosen_tank = int(chosen_tank.split(" ")[1])
    image_stream = io.BytesIO()
    images[chosen_tank-1].save(image_stream, format='PNG')
    image_stream.seek(0)
    tank_file = discord.File(image_stream, "attachment://tank_image.png")
    embed = discord.Embed(title=f"Fish in Tank {chosen_tank}")
    embed.set_image(url="attachment://tank_image.png")
    tank_num = 5*(chosen_tank-1)
    for count in range(len(fish)):
        if int(count/5) == 0 and count+tank_num < len(fish):
            embed.add_field(name=fish[count+tank_num]['species'].replace("_", " ").title(), value=_Fish_Species.get_fish(fish[count+tank_num]['species']).lever.replace("_", " ").title())
        else:
            break
    await ctx.send(embed=embed, file=tank_file)

async def add_user(ctx):
    async with vbu.Database() as db:
        await db("""INSERT INTO user_settings(user_id) VALUES ($1)""",
                 ctx.author.id)
        await db("""INSERT INTO user_item_inventory(user_id) VALUES ($1)""",
                 ctx.author.id)