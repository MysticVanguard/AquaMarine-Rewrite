import math
import random
import asyncio
import discord
from datetime import datetime as dt, timedelta
from discord.ext import commands, tasks, vbu

from cogs import utils
from cogs.utils._fish import _Fish_Species


class Town(vbu.Cog):


    async def add_quest(self, settings: list[dict]):  
        rarities = ("common","uncommon","rare","epic","legendary","mythic")
        rarity = random.choices(rarities,utils.rarity_chances[settings[0]['rarity_increase_tier']])[0]
        fish_type = random.choice(_Fish_Species.get_fish_by_rarity(rarity))
        orb_type = f"{rarity}_xp_orb"
        time_to_complete = (rarities.index(rarity)+1)*2
        time_given = dt.utcnow() - timedelta(hours=5)
        time_expires = dt.utcnow() + timedelta(days=time_to_complete) - \
            timedelta(hours=5)
        sand_dollars = random.randint(1*(rarities.index(rarity)+1), 
                                      20*(rarities.index(rarity)+1))*(settings[0]['quest_reward_multiplier']/100)
        amount = random.randint(1,20)
        if amount < 5:
            orb_amount = math.ceil((1*(settings[0]['quest_reward_multiplier']/100)))
        elif amount < 10:
            orb_amount = math.ceil((2*(settings[0]['quest_reward_multiplier']/100)))
        elif amount < 15:
            orb_amount = math.ceil((3*(settings[0]['quest_reward_multiplier']/100)))
        else:
            orb_amount = math.ceil((4*(settings[0]['quest_reward_multiplier']/100)))
        async with vbu.Database() as db:
            await db(
                """INSERT INTO user_quests (
                    user_id, quest_rarity, fish_species, total_amount, orb_type, 
                    orb_amount, sand_dollars, time_given, time_expires) 
                    VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                settings[0]["user_id"],
                rarity,
                fish_type.name,
                amount,
                orb_type,
                orb_amount,
                sand_dollars,
                time_given,
                time_expires
            )

    def __init__(self, bot: vbu.Bot):
        super().__init__(bot)
        self.quest_loop.start()
        self.quest_add_loop.start()

    def cog_unload(self):
        self.quest_loop.cancel()
        self.quest_add_loop.cancel()

    @tasks.loop(hours=24)
    async def quest_add_loop(self):

        async with vbu.Database() as db:
            all_quests = await db("""SELECT * FROM user_quests""")
            
            users = {}
            for quest in all_quests:
                if quest["user_id"] not in users.keys():
                    users[quest["user_id"]] = 1
                else:
                    users[quest["user_id"]] += 1
            for user, value in users.items():
                user_settings = await db("""select * From user_settings WHERE user_id = $1""",
                                         user)
                if value < user_settings[0]['max_quests']:
                    settings = await db("""SELECT * FROM user_settings WHERE user_id = $1""",
                             user)
                    await self.add_quest(settings)

    @quest_add_loop.before_loop
    async def before_quest_add_loop(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def quest_loop(self):

        async with vbu.Database() as db:
            all_quests = await db(
                """SELECT * FROM user_quests"""
            )
            for quest in all_quests:
                if dt.utcnow() > quest["time_expires"]:
                    await db(
                        """DELETE FROM user_quests WHERE time_expires = $1 AND user_id = $2 AND fish_species = $3""",
                        quest["time_expires"],
                        quest["user_id"],
                        quest["fish_species"]
                    )

    @quest_loop.before_loop
    async def before_quest_loop(self):
        await self.bot.wait_until_ready()

    async def _choose_item(
                self,
                ctx: vbu.SlashContext,
                category: str,
                send_new: bool = True
            ) -> utils.Item | None:
        """Ask a User to choose an item from their chosen category"""

        def item_question_check(interaction: discord.Interaction) -> bool:
            return bool(
                    interaction.component and interaction.component.custom_id
                    and
                    interaction.component.custom_id.startswith("ITEM_")
                    and
                    interaction.user.id == ctx.author.id
                )

        category_items = utils.Category.get_categories()[category].items
        print(category_items)

        question_embed = vbu.Embed(
            title = category,
            description = "Choose an item!",
            use_random_colour=True
        )
        item_buttons = []
        for item in category_items.values():
            if item.ref[0] == "doubloon":
                type = "Doubloons"
            else:
                type = "Sand Dollars"
            price = ""
            if item.ref != "choose_skin":
                price = f"({item.price} {type})"
            item_buttons.append(discord.ui.Button(
                    label=f"{item.display_name} {price}",
                    custom_id=f"ITEM_OPT_{item.display_name}"
                ))
            question_embed.add_field(name=f"{item.display_name} {price}",value=item.description)
            

        action_rows = []
        while len(item_buttons) > 5:
            action_rows.append(discord.ui.ActionRow(*item_buttons[:5]))
            item_buttons = item_buttons[5:]
        
        action_rows.append(discord.ui.ActionRow(*item_buttons))
        action_rows.append(discord.ui.ActionRow(discord.ui.Button(
                            label="Exit",
                            custom_id=f"ITEM_BACK",
                            style=discord.ButtonStyle.danger)))
        
        components = discord.ui.MessageComponents(*action_rows)
        if send_new:
            question_message = await ctx.send(
                embed = question_embed,
                components = components,
                ephemeral = True,
            )
            await question_message.delete(delay = 60)

        try:
            chosen_button = await self.bot.wait_for(
                "interaction",
                timeout=30,
                check=item_question_check
            )
        except asyncio.TimeoutError:
            return await ctx.send("Command timed out.")
        await chosen_button.response.defer_update()

        # Linting stuff
        assert chosen_button
        assert chosen_button.component
        assert isinstance(chosen_button.component, discord.ui.Button)
        assert chosen_button.component.label

        if chosen_button.component.custom_id == "ITEM_BACK":
            return None

        return (
            category_items[chosen_button.component.custom_id
                           .replace("ITEM_OPT_", "")]
            or
            None
        )
        

    async def _choose_category(self, ctx: vbu.SlashContext) -> str:
        """If a User doesn't pick a category, ask them to"""

        def category_question_check(interaction: discord.Interaction) -> bool:
            return bool(
                    interaction.component and interaction.component.custom_id
                    and
                    interaction.component.custom_id.startswith("CAT_")
                    and
                    interaction.user.id == ctx.author.id
                )

        question_embed = vbu.Embed(
            title = "Shop",
            description = "Choose a category!",
            use_random_colour = True
        )

        category_buttons = [
            discord.ui.Button(label=cat_name, custom_id=f"CAT_OPT_{cat_name}")
            for cat_name in utils.Category.get_categories()
        ]

        question_message = await ctx.send(
            embed = question_embed,
            components = discord.ui.MessageComponents(
                    discord.ui.ActionRow(
                        discord.ui.Button(
                            label="Exit",
                            custom_id=f"CAT_BACK",
                            style=discord.ButtonStyle.danger
                        )
                    ),
                    discord.ui.ActionRow(*category_buttons)
                ),
            ephemeral = True,
        )
        await question_message.delete(delay = 60)
        try:
            chosen_button = await self.bot.wait_for(
                "interaction",
                timeout = 30,
                check = category_question_check
            )
        except asyncio.TimeoutError:
            return await ctx.send("Command timed out.")
        await chosen_button.response.defer_update()

        # Linting stuff
        assert chosen_button
        assert chosen_button.component
        assert isinstance(chosen_button.component, discord.ui.Button)

        return chosen_button.component.label or ""

    @commands.command(
        name = "shop",
        application_command_meta=commands.ApplicationCommandMeta(
            options = [
                discord.ApplicationCommandOption(
                    name = "category",
                    description = "The category you'd like to browse",
                    type = discord.ApplicationCommandOptionType.string,
                    required = False,
                    autocomplete = True
                )
            ]
        )
    )
    async def shop(self, ctx: vbu.SlashContext, category: str = ""):
        """
        Opens the shop
        """
        has_exited: bool = False

        while not has_exited:
            # Retrieve a category
            if not category:
                category = await self._choose_category(ctx)
                if type(category) == discord.WebhookMessage:
                    return
                
                if category == "Exit":
                    has_exited = True
                    break

                if not category or category not in utils.Category.get_categories():
                    fail_message =  await ctx.send(
                        "Something went wrong :(",
                        ephemeral = True,
                    )
                    await fail_message.delete(delay = 5)
                    return

            # Retrieve an item
            item = None
            while not has_exited:

                item = await self._choose_item(ctx, category, not bool(item))
                if type(item) == discord.WebhookMessage:
                    return
                
                if not item:
                    category = ""
                    break
                cant_buy = False
                async with vbu.Database() as db:
                    settings = await db("""SELECT * FROM user_settings WHERE user_id = $1""",
                                ctx.author.id)
                    if not settings:
                        await utils.add_user(ctx)
                        settings = await db("""SELECT * FROM user_settings WHERE user_id = $1""",
                                    ctx.author.id)
                    if settings[0]['sand_dollars'] < item.price and item.ref[0] != 'doubloon':
                        item_message = await ctx.send("You don't have enough money! Use /fish with the fishing rod tool to get more!", 
                                                      ephemeral = True)
                    elif settings[0]['doubloons'] < item.price and item.ref[0] == 'doubloon':
                        item_message = await ctx.send("You don't have enough money!", 
                                                      ephemeral = True)
                    else:
                        if item.ref == "choose_skin":
                            skin_line = await utils.create_select_menu(ctx.bot, ctx, [item for item in list(utils.Category.get_categories()[category].items.keys())[:-1]], "skin line", "select", True)
                            if skin_line in [item for item in list(utils.Category.get_categories()[category].items.keys())[:-1]]:
                                fish_options = []
                                fish_tiers = []
                                for skin in utils.skins:
                                    if skin[1] == skin_line:
                                        fish_options.append(skin[0].replace("_", " ").title())
                                        fish_tiers.append(skin[2])
                                skin = await utils.create_select_menu(ctx.bot, ctx, fish_options, "fish", "select", True)
                                if skin in fish_options:
                                    values = {"1":10,"2":30,"3":50}
                                    tier = fish_tiers[fish_options.index(skin)]
                                    skin = skin.replace(" ", "_").lower()
                                    
                                    
                                    skin_db = await db("""SELECT * FROM user_skin_inventory WHERE user_id = $1 AND name = $2 AND fish = $3""",
                                                       ctx.author.id,
                                                       skin_line,
                                                       skin)
                                    if not skin_db:
                                        if settings[0]['doubloons'] < values[str(tier)]:
                                            item_message = await ctx.send("You don't have enough money!", 
                                                ephemeral = True)
                                            continue
                                        await db("""INSERT INTO user_skin_inventory(user_id, name, fish, tier) VALUES ($1, $2, $3, $4)""",
                                             ctx.author.id,
                                             skin_line,
                                             skin,
                                             tier
                                        )
                                        await db("""UPDATE user_settings SET doubloons = doubloons - $1 WHERE user_id = $2""",
                                                 values[str(tier)],
                                                 ctx.author.id)
                                        item_message = await ctx.send(f"You bought {skin_line} for {skin.replace('_', ' ').title()}", 
                                                          ephemeral = True)
                                        continue
                                    else:
                                        item_message = await ctx.send("You already have this skin!", 
                                                ephemeral = True)
                                        continue
                                
                        if item.ref[0] == "net":
                            if settings[0]['has_net']:
                                item_message = await ctx.send("You already have a net!", 
                                                              ephemeral = True)
                                cant_buy = True
                            else:   
                                await db("""UPDATE user_settings SET has_net = TRUE, net_type = $1, net_hp= $2 WHERE user_id = $3""",
                                            item.display_name.replace(" ", "_").lower(),
                                            (item.ref[1]+settings[0]['net_durability_mod']),
                                            ctx.author.id)
                        elif item.ref == "tank":
                            await db("""UPDATE user_settings SET tank_room = $1 WHERE user_id = $2""",
                                     settings[0]['tank_room']+1,
                                     ctx.author.id)
                        elif item.ref[0] in ["bait", "tier_1"]:
                            await db("""UPDATE user_item_inventory SET {0} = {0} + 1 WHERE user_id = $1""".format(item.ref[1]),
                                     ctx.author.id)
                        elif item.ref[1] == "skin":
                            skins = await db("""SELECT * FROM user_skin_inventory WHERE user_id = $1 AND name = $2""",
                                             ctx.author.id,
                                             item.display_name)
                            if len(skins) > 0:
                                item_message = await ctx.send(f"You already have part of or all of this skin line, cannot buy bundle!", 
                                                              ephemeral = True)
                                await item_message.delete(delay = 5)
                                continue

                            for skin in utils.skins:
                                if skin[1] == item.display_name:
                                    await db("""INSERT INTO user_skin_inventory(user_id, name, fish, tier) VALUES ($1, $2, $3, $4)""",
                                             ctx.author.id,
                                             skin[1],
                                             skin[0],
                                             skin[2]
                                             )
                        if not cant_buy:
                            item_message = await ctx.send(f"You bought 1 {item.display_name}", 
                                                          ephemeral = True)
                            if item.ref[0] == 'doubloon':
                                    await db("""UPDATE user_settings SET doubloons = $1 WHERE user_id = $2""",
                                        settings[0]["doubloons"]-item.price,
                                        ctx.author.id)
                            else:
                                await db("""UPDATE user_settings SET sand_dollars = $1 WHERE user_id = $2""",
                                            settings[0]["sand_dollars"]-item.price,
                                            ctx.author.id)
                await item_message.delete(delay = 5)

        await ctx.interaction.delete_original_message()

    @shop.autocomplete # pyright: ignore
    async def get_category_autocomplete(
                self,
                ctx: vbu.SlashContext,
                interaction: discord.AutocompleteInteraction
            ) -> None:
        """Gets the category names for autocomplete"""
        options = [
            discord.ApplicationCommandOptionChoice(
                                                    name = cat_name,
                                                    value = cat_name
                                                )
            for cat_name in utils.Category.get_categories()
        ]


        await interaction.response.send_autocomplete(options)

    @commands.command(application_command_meta=commands.ApplicationCommandMeta())
    async def quests(self, ctx: vbu.SlashContext):
        """Let's you complete quests for rewards"""
        async with vbu.Database() as db:
            user_quests = await db("""SELECT * FROM user_quests WHERE user_id = $1""",
                        ctx.author.id)
            settings = await db("""SELECT * FROM user_settings WHERE user_id = $1""",
                        ctx.author.id)
            if not settings:
                await utils.add_user(ctx)
                settings = await db("""SELECT * FROM user_settings WHERE user_id = $1""",
                        ctx.author.id)
            items = await db(
                                """SELECT * FROM user_item_inventory WHERE user_id = $1""",
                                ctx.author.id
                            )
            if not user_quests:
                for i in range(settings[0]['max_quests']):
                    await self.add_quest(settings)
            user_quests = await db("""SELECT * FROM user_quests WHERE user_id = $1""",
                        ctx.author.id)
            quest_string = ""
            buttons = []
            components_check = False
            for i in range(len(user_quests)):
                quest_string += f"Quest {str(i+1)}: catch **{str(user_quests[i]['total_amount']-user_quests[i]['amount'])} " + \
                    f"{user_quests[i]['fish_species'].replace('_', ' ').title()}s** " + \
                    f"{discord.utils.format_dt(user_quests[i]['time_expires'], 'R')} to get " + \
                    f"**{str(user_quests[i]['orb_amount'])} {user_quests[i]['orb_type'].replace('_', ' ').title()}s** " + \
                    f"and **{str(user_quests[i]['sand_dollars'])} Sand Dollars**.\n\n" 
                if user_quests[i]['total_amount']-user_quests[i]['amount'] == 0:
                    buttons.append(discord.ui.Button(custom_id=i, label=f"Claim Quest {i+1}"))
                    components_check = True
            
            file = discord.File("C://Users//johnt//Pictures//fish//town_images//quest_image.png")
            if components_check == False:
                await ctx.send(quest_string, file=file)
            else:
                components = discord.ui.MessageComponents(discord.ui.ActionRow(*buttons))
                
                quest_message = await ctx.send(quest_string, components=components, file=file)
                try:
                    quest_button_payload = await self.bot.wait_for(
                        "component_interaction", 
                        timeout=60.0, 
                        check=lambda p: p.user.id == ctx.author.id and p.message.id == quest_message.id)
                    chosen_button = quest_button_payload.component.custom_id.lower()
                except asyncio.TimeoutError:
                    await quest_message.edit(components=components.disable_components())
                if chosen_button:
                    await quest_button_payload.response.defer_update()
                    async with vbu.Database() as db:
                        chosen_button = int(chosen_button)
                        await db("""UPDATE user_settings SET sand_dollars = $1 WHERE user_id = $2""",
                                        settings[0]["sand_dollars"]+user_quests[chosen_button]["sand_dollars"],
                                        ctx.author.id)
                        await db("""UPDATE user_item_inventory SET {0} = $1 WHERE user_id = $2""".format(user_quests[chosen_button]["orb_type"]),
                                    items[0][user_quests[chosen_button]["orb_type"]]+user_quests[chosen_button]["orb_amount"],
                                    ctx.author.id)
                        await db("""DELETE FROM user_quests WHERE user_id = $1 AND fish_species = $2""",
                                 ctx.author.id,
                                 user_quests[chosen_button]["fish_species"])
                    await quest_message.edit(components=components.disable_components())
                    await ctx.send(f"Claimed {user_quests[chosen_button]['orb_amount']} {user_quests[i]['orb_type'].replace('_', ' ').title()}s and {str(user_quests[i]['sand_dollars'])} Sand Dollars.")
        
    @commands.command(application_command_meta=commands.ApplicationCommandMeta())
    @commands.bot_has_permissions(send_messages=True)
    async def bestiary(self, ctx: vbu.SlashContext):
        """Let's you see details of any fish in the bot"""
        rarity = await utils.create_select_menu(self.bot, ctx, ["Common", "Uncommon", "Rare", "Epic", "Legendary"], "rarity", "select", True)
        if rarity not in ["Common", "Uncommon", "Rare", "Epic", "Legendary"]:
            return
        first_fish_options = [single_fish.name.replace('_', ' ').title() for single_fish in _Fish_Species.get_fish_by_rarity(rarity.lower())]
        fish_options = []
        fish = "Next List"
        while len(first_fish_options) > 25 and fish == "Next List":
            fish_options = first_fish_options[:24]
            fish_options.append("Next List")
            first_fish_options = first_fish_options[24:]
            fish = await utils.create_select_menu(self.bot, ctx, fish_options, "fish", "select", True)
        if fish == "Next List":
            fish = await utils.create_select_menu(self.bot, ctx, first_fish_options, "fish", "select", True)
        
        if fish not in first_fish_options:
            return

        fish = _Fish_Species.get_fish(fish.replace(' ', '_').lower()) 
        embed = discord.Embed(title=fish.name.replace("_", " ").title())
        embed.add_field(name="Rarity", value=fish.rarity.title())
        embed.add_field(name="Passive Bonus", value=fish.lever.replace("_", " ").title())
        fish_file = discord.File("C:\\Users\\johnt\\Pictures\\fish"+"\\"+fish.rarity+"\\"+fish.name+"-export.png", "new_fish.png")
        embed.set_image(url="attachment://new_fish.png")
        
        if fish.rarity != "common":
            region_name_string = ""
            region_description_string = ""
            for region in fish.region:
                region_name_string += region.name.replace("_", " ").title() + ", "
                region_description_string += region.description + ", "
            region_name_string = region_name_string[:-2]
            region_description_string = region_description_string[:-2]

            class_name_string = ""
            class_description_string = ""
            for fish_class in fish.fish_class:
                class_name_string += fish_class.name.replace("_", " ").title() + ", "
                class_description_string += fish_class.description + ", "
            class_name_string = class_name_string[:-2]
            class_description_string = class_description_string[:-2]

            stats_string = f"HP: {fish.hp} AD: {fish.ad} AR: {fish.ar} " + \
                f"MR: {fish.mr} Haste: {fish.haste} Max Mana: {fish.mana}"
            embed.add_field(name=region_name_string, value=region_description_string)
            embed.add_field(name=class_name_string, value=class_description_string)
            embed.add_field(name="Base Stats", value=stats_string)
            embed.add_field(name="Ability", value=fish.ability)
        
        await ctx.send(embed=embed, file=fish_file)
        
    @commands.command(application_command_meta=commands.ApplicationCommandMeta())
    @commands.bot_has_permissions(send_messages=True)
    async def craft(self, ctx: vbu.SlashContext):
        """Let's you craft items for your fish"""
        async with vbu.Database() as db:
            items = await db("""SELECT * FROM user_item_inventory 
                             WHERE user_id = $1""",
                             ctx.author.id)
            if not items:
                await utils.add_user(ctx)
                items = await db("""SELECT * FROM user_item_inventory 
                            WHERE user_id = $1""",
                            ctx.author.id)
            equipped_items = await db("""SELECT * FROM user_fish_inventory 
                                      WHERE user_id = $1 AND item != ''""",
                                      ctx.author.id,)
        equipped_items_counts = {}
        for fish in equipped_items:
            if fish['item'] not in equipped_items_counts.keys():
                equipped_items_counts[fish['item']] = [1, [fish['species']]]
            else:
                equipped_items_counts[fish['item']][0] += 1
                equipped_items_counts[fish['item']][1].append(fish['species'])
        embed=discord.Embed(title="Items")
        buttons = []
        components_check = False
        for index in range(0, len(utils.items['Tier 1'])-1, 2):
            embed.add_field(name=f"{utils.EMOJIS[utils.items['Tier 1'][index]]} {utils.items['Tier 1'][index].replace('_', ' ').title()}: {items[0][utils.items['Tier 1'][index]]}", 
                            value=f"{utils.EMOJIS[utils.items['Tier 1'][index + 1]]} {utils.items['Tier 1'][index + 1].replace('_', ' ').title()}: {items[0][utils.items['Tier 1'][index + 1]]}")
        temp_items = utils.items['Tier 2']
        temp_items.update(utils.items['Tier 3'])
        for item, item_object in temp_items.items():
            if item not in equipped_items_counts.keys():
                embed.add_field(name=item, value="0")
            else:
                embed.add_field(name=item, value=equipped_items_counts[item][0])

            button_check = True
            for tier_1, value in vars(item_object).items():
                if tier_1 in ['tier', 'name', 'components']:
                    continue
                value = int(value)
                if value > items[0][tier_1]:
                    button_check = False
            
            if button_check:
                if len(item_object.components) > 0 and \
                item_object.components[0] in equipped_items_counts.keys() and \
                item_object.components[1] in equipped_items_counts.keys():
                    if item_object.components.count(item_object.components[0]) \
                    <= equipped_items_counts[item_object.components[0]][0] and \
                    item_object.components.count(item_object.components[1]) \
                    <= equipped_items_counts[item_object.components[1]][0]:
                        buttons.append(discord.ui.Button(custom_id=item, label=f"Craft {item.replace('_', ' ').title()}"))
                        components_check = True
                elif len(item_object.components) == 0:
                    buttons.append(discord.ui.Button(custom_id=item, label=f"Craft {item.replace('_', ' ').title()}"))
                    components_check = True
        if not components_check:
            await ctx.send(embed=embed)
        else:
            actionrows = []
            while len(buttons) > 5:
                actionrows.append(discord.ui.ActionRow(*buttons[:5]))
                buttons = buttons[5:]
            actionrows.append(discord.ui.ActionRow(*buttons))
            components = discord.ui.MessageComponents(*actionrows)
            craft_message = await ctx.send(embed=embed, components=components)
            try:
                quest_button_payload = await self.bot.wait_for(
                    "component_interaction", 
                    timeout=60.0, 
                    check=lambda p: p.user.id == ctx.author.id and p.message.id == craft_message.id)
                chosen_button = quest_button_payload.component.custom_id.lower()
                await quest_button_payload.response.defer_update()
            except asyncio.TimeoutError:
                await craft_message.edit(components=components.disable_components())
                return
            if chosen_button:
                async with vbu.Database() as db:
                    fish = await db("""SELECT * FROM user_fish_inventory WHERE user_id = $1 AND item = ''""",
                                    ctx.author.id)
                    fish_options = []
                    for single_fish in fish:
                        if _Fish_Species.get_fish(single_fish['species']).rarity == "common":
                            continue
                        fish_options.append(single_fish['species'])
                    
                await ctx.send(f"Which fish would you like to equip your new {chosen_button.replace('_', ' ').title()} to?")
                selected_fish = await utils.create_select_menu(self.bot, ctx, fish_options, 'fish', 'select', True)
                if selected_fish not in fish_options:
                    return
                
                async with vbu.Database() as db:
                    for tier_1, value in vars(utils.items['Tier 2'][chosen_button]).items():
                        if tier_1 in ['tier', 'name', 'components']:
                            continue
                        value = int(value)
                        await db("""UPDATE user_item_inventory SET {0} = {0} - $1 WHERE user_id = $2""".format(tier_1),
                                    value,
                                    ctx.author.id)
                    if chosen_button in utils.items['Tier 3'].keys():
                        for component in utils.items['Tier 3'][chosen_button].components:
                            await db("""UPDATE user_fish_inventory SET item = '' WHERE user_id = $1 AND species = $2""",
                                     ctx.author.id,
                                     equipped_items_counts[component][1][0])
                            equipped_items_counts[component][1].pop(0)
                    await db("""UPDATE user_fish_inventory SET item = $3 WHERE user_id = $1 AND species = $2""",
                             ctx.author.id,
                             selected_fish.replace(' ', '_').lower(),
                             chosen_button)
                await ctx.send(f"{selected_fish.replace('_', ' ').title()} equipped {chosen_button.replace('_', ' ').title()}!")
                await craft_message.edit(components=components.disable_components())
                   
def setup(bot):
    bot.add_cog(Town(bot))