import asyncio
import random
import discord
from discord.ext import vbu
from cogs import utils
from ._fish import _Fish_Species
import math
from PIL import Image
import io


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
}

VALID_ITEMS = [
                "common_xp_orb", "uncommon_xp_orb", "rare_xp_orb", "epic_xp_orb", "legendary_xp_orb", "mythic_xp_orb",
               "common_bait", "uncommon_bait", "rare_bait", "epic_bait",
            ]
# This is used to fix fields that are too long (i.e. If someone has too many of one rarity in their fish bucket)
def get_fixed_field(field):
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
    user,
    field: tuple[str, str],
    page: int,
    custom_title: None
):
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
async def paginate(ctx, fields, user, select, options=None, custom_str=None):

    # intiiates bot as ctx.bot
    bot = ctx.bot
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


async def create_select_menu(bot, ctx, option_list, type_noun, type_verb, remove=False):
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


async def create_modal(bot, Interaction, title, placeholder):
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


async def sort_by_rarity(user_fish):
        fish_list = []
        for rarity in ["common", "uncommon", "rare", "epic", "legendary", "mythic"]:
            for fish in user_fish:
                if _Fish_Species.get_fish(fish['species']).rarity == rarity:
                    fish_list.append(_Fish_Species.get_fish(fish['species']))
                    print(_Fish_Species.get_fish(fish['species']))
        return fish_list
    
async def create_dropdown_embed(ctx, user, fish_list):
    fish_list_sectioned = []
    fish_sectioned_string = []
    for count, fish in enumerate(fish_list):
        if count/25==0:
            fish_list_sectioned.append([fish.name.replace("_", " ").title()])
            fish_sectioned_string.append(["Fish Inventory", "(" + fish.rarity[0] + ") " + fish.name.replace("_", " ").title()])
        else:
            fish_list_sectioned[int(count/25)].append(fish.name.replace("_", " ").title())
            fish_sectioned_string[int(count/25)][1] += "\n(" + fish.rarity[0] + ") " + fish.name.replace("_", " ").title()
    
    return await paginate(ctx, fish_sectioned_string, user, True, fish_list_sectioned)

async def get_info(ctx, fish):
    async with vbu.Database() as db:
        user_fish = await db(
            """SELECT * FROM user_fish_inventory WHERE user_id = $1""",
            ctx.author.id,
        )
    fish_path = "C:\\Users\\johnt\\Pictures\\fish"
    fish_species = _Fish_Species.get_fish(fish.replace(" ", "_").lower())
    user_fish_data = None
    for single_fish in user_fish:
        if single_fish['species'] == fish.replace(" ", "_").lower():
            user_fish_data = single_fish
            break
    embed = discord.Embed(title=f"{fish}")
    if (fish_species.rarity in ["uncommon", "rare", "epic", "legendary", "mythic"]):
        region_names = ""
        region_descriptions = ""
        class_names = ""
        class_descriptions = ""
        for region in fish_species.region:
            region_names += f"{region.name.replace('_', ' ').title()}\n"
            region_descriptions += f"{region.description}\n"
        for fish_class in fish_species.fish_class:
            class_names += f"{fish_class.name.replace('_', ' ').title()}\n"
            class_descriptions += f"{fish_class.description}\n"
        embed.add_field(name=region_names, value=region_descriptions,inline=False)
        embed.add_field(name=class_names, value=class_descriptions,inline=False)
    embed.add_field(name="Passive Bonus", value=fish_species.lever.replace("_", " ").title())
    fish_file = discord.File(fish_path+"\\"+fish_species.rarity+"\\"+fish_species.name+"-export.png", "new_fish.png")
    embed.set_image(url="attachment://new_fish.png")
    embed.add_field(name=f"Level {user_fish_data['level']}: {user_fish_data['current_xp']}/{user_fish_data['max_xp']} XP", value=f"In Tank: {user_fish_data['in_tank']}")
    await ctx.send(embed=embed, file=fish_file)


async def create_images(fish, settings):
    room = settings[0]['tank_room']
    tanks = []
    tank_images = []
    fish_placements = [(100,100), (500,100), (400, 400), (600,400), (100,300)]
    fish_path = "C:\\Users\\johnt\\Pictures\\fish"
    for single_room in range(room):
        if single_room < len(fish):
            if single_room % 5 == 0:
                tanks.append([fish[single_room]])
            else:
                tanks[int(single_room / 5)].append(fish[single_room])
    for tank in tanks:
        background = Image.open(
                f"{fish_path}\\tank_backgrounds\\test.png"
            )
        fish_images = []
        for num, fish in enumerate(tank):
            background.paste(Image.open(f"{fish_path}\\{_Fish_Species.get_fish(fish['species']).rarity}\\{fish['species']}.png"), 
                             (fish_placements[num][0], fish_placements[num][1]), 
                             Image.open(f"{fish_path}\\{_Fish_Species.get_fish(fish['species']).rarity}\\{fish['species']}.png")
                            )
        tank_images.append(background)
    
    return tank_images

async def create_tank_embed(ctx, bot, fish, images):
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
