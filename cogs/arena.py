import random
import asyncio
import discord
from datetime import datetime as dt, timedelta
from discord.ext import commands, tasks, vbu

import copy
from cogs import utils
from cogs.utils._fish import _Fish_Species


class Arena(vbu.Cog):

    def add_fish_to_team(self, fish_names):
        region_string = ""
        fish_class_string = ""
        fish_name_string = ""
        fish_regions = {}
        fish_classes = {}
        for fish in fish_names:
            fish = _Fish_Species.get_fish(fish.replace(' ', '_').lower())
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
            fish_name_string += f"({fish.rarity}) {fish.name.replace('_', ' ').title()}\n"
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
        embed = discord.Embed(title="Created Team! (Only fish of Uncommon rarity or higher can be on a team)")
        embed.add_field(name="Fish Names", value=fish_name_string)
        embed.add_field(name="Fish Regions", value=region_string)
        embed.add_field(name="Fish Classes", value=fish_class_string)
        embed.add_field(name="Fish Selected", value=len(fish_names))
        return embed
    
    async def add_fish(self, ctx, settings, draft_fish, rarity, text):
        fishes = []
        buttons = []
        embed = discord.Embed(title=text)
        while len(buttons) < 3:
            fish = random.choice(_Fish_Species.get_fish_by_rarity(rarity))
            if fish.name not in fishes:
                embed.add_field(name=f"**{fish.name.replace('_', ' ').title()}**",value=f"*{rarity.title()}*\n{fish.ability}")
                embed.add_field(name="**Stats**",value=f"HP: {fish.hp}\nAD: {fish.ad}\nAP: {fish.ap}\nAR: {fish.ar}\nMR: {fish.mr}\nHaste: {fish.haste}\nMana: {fish.mana}")
                region_class_string = ""
                for region in fish.region:
                    region_class_string += f"**{region.name.replace('_', ' ').title()}**:\n"
                    region_class_string += f"*({region.description})*\n"
                for fish_class in fish.fish_class:
                    region_class_string += f"**{fish_class.name.replace('_', ' ').title()}**:\n"
                    region_class_string += f"*({fish_class.description})*\n"
                embed.add_field(name='**Regions and Classes**', value=region_class_string)
                fishes.append(fish.name)
                buttons.append(discord.ui.Button(label=fish.name.replace('_', ' ').title(), custom_id=fish.name))
        components = discord.ui.MessageComponents(discord.ui.ActionRow(*buttons))
        
        fish_add_message = await ctx.send(embed=embed, components = components)
        try:
            embed_button_payload = await self.bot.wait_for(
                "component_interaction", 
                timeout=60.0, 
                check=lambda p: p.user.id == ctx.author.id and p.message.id == fish_add_message.id)
            chosen_button = embed_button_payload.component.custom_id
            await embed_button_payload.response.defer_update()
        except asyncio.TimeoutError:
            await fish_add_message.edit(components=components.disable_components())
            return
        if settings[0]['draft_fish_amount'] == 5:
            curr_draft_fish = [single_fish['species'].replace('_', ' ').title() for single_fish in draft_fish]
            curr_draft_fish.append("Do not replace any!")
            fish_replaced = utils.create_select_menu(self.bot, ctx, curr_draft_fish, 'fish', 'replace (new fish will hold any item old fish did, and any skin or bonuses will be removed)', True)
            if fish_replaced in curr_draft_fish:
                if fish_replaced != "Do not replace any!":
                    async with vbu.Database() as db:
                        await db("""DELETE FROM user_draft_fish WHERE species = $1 AND user_id = $2""",
                                 fish_replaced.replace(' ', '_').lower(),
                                 ctx.author.id)
        async with vbu.Database() as db:
            await db("""INSERT INTO user_draft_fish(user_id,species,level) VALUES ($1,$2,1)""",
                        ctx.author.id,
                        chosen_button)
        ctx.send(f"You chose {chosen_button.replace('_', ' ').title()}!")
        fish_add_message.edit(components=components.disable_components())
    
    async def show_draft_info(self, ctx, settings):
        pass
    
    def add_item(self, fish: _Fish_Species, item):
        items = {"scale_armor": {"hp": 100},
                 "shell_shield": {"ar": 10},
                 "plastic_bag_cape": {"mr": 10},
                 "coral_sword": {"ad": 15},
                 "crab_claw_gauntlet": {"crit_chance": 10},
                 "seaweed_staff": {"ap": 15},
                 "pebble_amulet": {"mana": -10},
                 "tire_tread_boots": {"haste": 10},
                 "scalebreakers_plate": {"hp": 800},
                 "tidal_resurgence": {"ar": 20, "hp": 200},
                 "barrierweave_cloak": {"haste": 40, "ar": 20, "mr": 20},
                 "stormforged_edge": {"ad": 100, "haste": -20},
                 "doubledrake_cutlass": {"ad": 30, "crit_chance": 20},
                 "crabshell_crusher": {"crit_chance": 40},
                 "aquamage_scepter": {"ap": 30, "mr": 20},
                 "aquaflow_amulet": {"mana": -10, "haste": 10},
                 "seafoam_mantle": {"ap": 30, "mana": -10}}
        for stat, change in items[item.replace(' ', '_').lower()].items():
            fish.__setattr__(stat, (fish.__getattribute__(stat)+change))
        fish.item = item
    
    def add_skin(self, fish, skin):
        pass

    def add_levels(self, fish, level):
        for _ in range(level):
            if fish.name == "beefish":
                fish.crit_damage += 5
                fish.ad += 5
            fish.hp += int(fish.hp*.04)
            fish.ap += int(fish.ap*.0075)
            fish.ad += int(fish.ad*.01)
            fish.level += 1

    def add_levers(self, fish, settings):
        fish.hp = int((fish.hp + settings['hp_increase']) * (settings['hp_percent']/ 100))
        fish.ad = int((fish.ad + settings['ad_increase']) * (settings['ad_percent']/ 100))
        fish.ap = int((fish.ap + settings['ap_increase']) * (settings['ap_percent']/ 100))
        fish.ar = int((fish.ar + settings['ar_increase']) * (settings['ar_percent']/ 100))
        fish.mr = int((fish.mr + settings['mr_increase']) * (settings['mr_percent']/ 100))
        fish.crit_chance = settings['crit_chance_percent']
        fish.crit_damage = settings['crit_damage_increase']
        fish.haste += settings['haste_increase']

    def find_changed_rp(self, user_rank, enemy_rank):
        changed_amount = 25
        index = utils.ranks.index(user_rank)
        index -= utils.ranks.index(enemy_rank)
        changed_amount -= index
        return changed_amount

    def format_ability(self, ability: str):
        formatted_ability = {}
        effects = ability.split(";")
        for effect in effects:
            effect_split = effect.split("-")
            effect_split_2 = effect_split[1].split(",")
            if "=" in effect_split[1]:
                effect_split_3 = effect_split_2[-1].split("=")
                formatted_ability[effect_split[0]] = effect_split_2[:-1] 
                formatted_ability[effect_split[0]].append((effect_split_3[0], effect_split_3[1].split("|")))
            else:
                formatted_ability[effect_split[0]] = effect_split_2
        return formatted_ability

    def cast_ability(self, fish: _Fish_Species, friendly_fish_sorted: list[_Fish_Species], enemy_fish_sorted: list[_Fish_Species]):
        formatted_ability = self.format_ability(fish.ability_string)
        for effect, values in formatted_ability.items():
            if effect in ["heal", "deal", "buff_stat", "debuff_stat", "stun"]:
                target_list = []
                if effect in ["heal", "buff_stat"]:
                    if values[3] in ["all", "self", "random"]:
                        target_list = friendly_fish_sorted
                    elif values[3][0] == "haste":
                        target_list = friendly_fish_sorted
                    elif values[3][0] == "health":
                        target_list = sorted(friendly_fish_sorted, key=lambda fish: fish.hp, reverse=True)
                elif effect in ["deal", "debuff_stat"]:
                    if values[3] in ["all", "self", "random"]:
                        target_list = enemy_fish_sorted
                    elif values[3][0] == "haste":
                        target_list = enemy_fish_sorted
                    elif values[3][0] == "health":
                        target_list = sorted(enemy_fish_sorted, key=lambda fish: fish.hp, reverse=True)
                else:
                    target_list = enemy_fish_sorted
                targets: list[_Fish_Species] = []
                i = 3
                if effect == "stun":
                    i = 1
                if values[i] == "all":
                    targets = target_list
                elif values[i] == "random":
                    targets.append(random.choice(target_list))
                elif values[i] == "self":
                    targets.append(fish)
                else:
                    for target in values[i][1]:
                        if target == "1" and (target_list[0] not in targets or len(target_list) > 1):
                            targets.append(target_list[0])
                        elif target == "2" and len(target_list) >= 2:
                            targets.append(target_list[1])
                        elif target == "4" and len(target_list) >= 2:
                            targets.append(target_list[-2])
                        elif target == "5" and (target_list[-1] not in targets or len(target_list) > 1):
                            targets.append(target_list[-1])
                if effect != "stun":
                    if values[2] == "flat":
                        used_stat = 1
                    else:
                        used_stat = fish.__getattribute__(values[2])
                if effect in ["heal", "deal"]:
                    damage = int(values[1])
                    damage_type = values[0]
                
                for target in targets:
                    if effect == "stun":
                        target.stunned += int(values[0])
                    elif effect == "heal":
                        target.hp += int((damage/100)* used_stat)
                        target.hp = min(target.max_hp, target.hp)
                    elif effect == "deal":
                        if damage_type == "ad":
                            resistance = target.ar
                        else:
                            resistance = target.mr
                        if fish.item == "Aquamage Scepter":
                            fish.hp += int(((damage/100)* used_stat)* (1 - resistance/(100 + resistance))/100)
                            fish.hp = min(fish.max_hp, fish.hp)
                        target.hp -= int(((damage/100)* used_stat)* (1 - resistance/(100 + resistance)))
                    elif effect == "debuff_stat":
                        target.__setattr__(values[0], max(int(fish.__getattribute__(values[0])-((int(values[1])/100)*used_stat)), 0))
                    elif effect == "buff_stat":
                        target.__setattr__(values[0], int(fish.__getattribute__(values[0])+((int(values[1])/100)*used_stat)))
                    
    def region_class_on_attack(self, fish: _Fish_Species, target_fish: _Fish_Species, regions, fish_classes):
            for region in fish.region:
                if region in regions.keys() and region.trigger == "on_attack":
                    buff_index = region.breakpoints.index(regions[region])
                    if region.name == "river":
                        target_fish.__setattr__(region.keyword[0], (fish.__getattribute__(region.keyword[0])+region.amount[buff_index]))
                    else:
                        fish.__setattr__(region.keyword[0], (fish.__getattribute__(region.keyword[0])+region.amount[buff_index]))
            for fish_class in fish.fish_class:
                if fish_class in fish_classes.keys() and fish_class.trigger == "on_attack":
                    buff_index = fish_class.breakpoints.index(fish_classes[fish_class])
                    fish.__setattr__(fish_class.keyword[0], (fish.__getattribute__(fish_class.keyword[0])+fish_class.amount[buff_index]))

    async def do_combat(self, ctx, user_fish: list[_Fish_Species], enemy_fish: list[_Fish_Species], user_regions, user_classes, enemy_regions, enemy_classes):
        user_fish_sorted = sorted(user_fish, key=lambda fish: fish.haste, reverse=True)
        enemy_fish_sorted = sorted(enemy_fish, key=lambda fish: fish.haste, reverse=True)
        fish_sorted = sorted(user_fish+enemy_fish, key=lambda fish: fish.haste, reverse=True)
        lowest_haste = fish_sorted[-1]
        for fish in fish_sorted:
            if fish in user_fish_sorted:
                use_regions = user_regions
                use_classes = user_classes
                other_classes = enemy_classes
            else:
                use_regions = enemy_regions
                use_classes = enemy_classes
                other_classes = user_regions
            for region in fish.region:
                if "coastal" == region.name and "coastal" in use_regions.keys() and fish.curr_mana < (fish.mana / 2):
                    fish.ap += region.amount[region.breakpoints.index(use_regions["coastal"])]
                    fish.ad += region.amount[region.breakpoints.index(use_regions["coastal"])]
                if "island" == region.name:
                    fish.mr = max(fish.mr, 50)
                    fish.ar = max(fish.ar, 50)
            for fish_class in fish.fish_class:
                if "shoalist" == fish_class.name and "shoalist" in use_classes.keys():
                    fish.ad += fish_class.amount[fish_class.breakpoints.index(use_classes['shoalist'])]
            

            if fish.stunned > 0 and fish.stunproof == 0:
                fish.stunned -= 1
                continue
            elif fish.stunproof > 0:
                fish.stunproof -= 1
                continue
            if fish in user_fish_sorted:
                slowest_fish = enemy_fish_sorted[-1]
            else:
                slowest_fish = user_fish_sorted[-1]
            extra_haste = 1 + int((fish.haste - lowest_haste.haste)/50)
            if fish.item == "Doubledrake Cutlass":
                extra_haste += 1
            if fish.item == "Crabshell Crusher" and fish.hp < fish.max_hp/2:
                fish.ad += 50
                fish.item = ""
            if fish.item == "Tidal Resurgence" and fish.hp < fish.max_hp/4:
                fish.hp += int(fish.max_hp/4)
                fish.item = ""
            for _ in range(extra_haste):
                multiplier = 1
                crit = random.randint(1,100)
                if crit < fish.crit_chance:
                    multiplier = fish.crit_damage / 100
                if slowest_fish.mark < 1:
                    multiplier = 2
                if fish.item == "Aquaflow Amulet":
                    fish.ap += 5
                slowest_fish.hp -= int(fish.ad * (1 - slowest_fish.ar/(100 + slowest_fish.ar)) * multiplier)
                for region in slowest_fish.region:
                    if slowest_fish.fish_class == "floundserker" and "floundserker" in other_classes.keys():
                        fish.ad += fish_class.amount[0]
                    if slowest_fish.fish_class == "whirllock" and "whirllock" in other_classes.keys():
                        fish.ap += fish_class.amount[fish_class.breakpoints.index(other_classes['whirllock'])]

                fish.curr_mana += 5
                slowest_fish.curr_mana += int(((fish.ad * (1 - slowest_fish.ar/(100 + slowest_fish.ar))))/10)
                if slowest_fish.hp < 0:
                    slowest_fish.hp = 0
                self.region_class_on_attack(fish, slowest_fish, use_regions, use_classes)
            if fish.curr_mana >= fish.mana:
                for region in fish.region:
                    if "deep_sea" == region.name and "deep_sea" in use_regions.keys():
                        fish.stunproof += region.amount[region.breakpoints.index(use_regions["deep_sea"])]
                    elif "creek" == region.name and "creek" in use_regions.keys():
                        fish.ar += region.amount[region.breakpoints.index(use_regions["creek"])]
                    elif "tropical" == region.name and "tropical" in use_regions.keys():
                        fish.ap += region.amount[region.breakpoints.index(use_regions["tropical"])]
                fish.curr_mana = 0
                casts = 1
                double_cast = random.randint(1,100)
                if double_cast <= 50 and "robotic" in [region.name for region in fish.region] or fish.item == "Seafoam Mantle":
                    casts = 2
                for _ in range(casts):
                    if fish in user_fish_sorted:
                        self.cast_ability(fish, user_fish_sorted, enemy_fish_sorted)
                    else:
                        self.cast_ability(fish, enemy_fish_sorted, user_fish_sorted)
                 
    def show_combat(self, user_fish: list[_Fish_Species], enemy_fish: list[_Fish_Species], count: int):
        user_fish_sorted = sorted(user_fish, key=lambda fish: fish.haste)
        enemy_fish_sorted = sorted(enemy_fish, key=lambda fish: fish.haste)
        embed = discord.Embed(title=f"Round {count}")
        user_fish_string = ""
        enemy_fish_string = ""
        for fish in user_fish_sorted:
            user_fish_string += fish.name.replace("_", " ").title() + "\n" + f"HP: {fish.hp} AD: {fish.ad} AP: {fish.ap} Mana: {fish.curr_mana}/{fish.mana} Haste: {fish.haste}\nAbility: {fish.ability}\n\n"
        for fish in enemy_fish_sorted:
            enemy_fish_string += fish.name.replace("_", " ").title() + "\n" + f"HP: {fish.hp} AD: {fish.ad} AP: {fish.ap} Mana: {fish.curr_mana}/{fish.mana} Haste: {fish.haste}\nAbility: {fish.ability}\n\n"
        embed.add_field(name="User Fish:", value=user_fish_string)
        embed.add_field(name="Enemy Fish:", value=enemy_fish_string)
        return embed

    def show_result(self, user_hp, enemy_hp):
        if user_hp > 0:
            return "You won!"
        else:
            return "You lost :("
        
    def configure_regions_and_classes(self, fish_list: list[_Fish_Species]):
        regions = {}
        fish_classes = {}
        for fish in fish_list:
            for region in fish.region:
                if region.name not in regions.keys():
                    regions[region.name] = 1
                else:
                    regions[region.name] += 1
            for fish_class in fish.fish_class:
                if fish_class.name not in fish_classes.keys():
                    fish_classes[fish_class.name] = 1
                else:
                    fish_classes[fish_class.name] += 1
        for fish in fish_list:
            for region in fish.region:
                if region.name in regions.keys():
                    region_breakpoint = 0
                    for single_breakpoint in region.breakpoints:
                        if regions[region.name] >= single_breakpoint:
                            region_breakpoint = single_breakpoint
                    if region_breakpoint == 0:
                        regions.pop(region.name)
                    else:
                        regions[region.name] = region_breakpoint
            for fish_class in fish.fish_class:
                if fish_class.name in fish_classes.keys():
                    class_breakpoint = 0
                    for single_breakpoint in fish_class.breakpoints:
                        if fish_classes[fish_class.name] >= single_breakpoint:
                            class_breakpoint = single_breakpoint
                    if class_breakpoint == 0:
                        fish_classes.pop(fish_class.name)
                    else:
                        fish_classes[fish_class.name] = class_breakpoint
        return regions, fish_classes
    
    def region_class_start_of_combat(self, fish_list: list[_Fish_Species], enemy_fish_list: list[_Fish_Species], regions, fish_classes):
        for fish in fish_list:
            for region in fish.region:
                if region in regions.keys() and region.trigger == "on_combat_start":
                    buff_index = region.breakpoints.index(regions[region])
                    if region.name == "coral_reef":
                        if buff_index == 1:
                            enemy_fish_sorted = sorted(enemy_fish_list, key=lambda fish: fish.haste)
                            enemy_fish_sorted[-5].stunned += region.amount[0]
                        else:
                            for enemy in enemy_fish_list:
                                enemy.stunned += region.amount[0]
                    elif region.name == "pond":
                        for _ in range(fish.level):
                            fish.ap += region.amount[0]
                            fish.hp += region.amount[0]*10
                    elif region.name == "divine":
                        for single_fish in fish_list:
                            haste = random.randint(1,60)
                            single_fish.haste = haste
                        for single_fish in enemy_fish_list:
                            haste = random.randint(1,60)
                            single_fish.haste = haste
                    else:
                        for keyword in region.keyword:
                            fish.__setattr__(keyword, (fish.__getattribute__(keyword)+region.amount[buff_index]))
        for fish in fish_list:
            for fish_class in fish.fish_class:
                if fish_class in fish_classes.keys() and fish_class.trigger == "on_combat_start":
                    buff_index = fish_class.breakpoints.index(fish_classes[fish_class])
                    if region.name == "sirenchanter":
                        fish.__setattr__(keyword, int(fish.__getattribute__(keyword)+((fish_class.amount[buff_index]/100)*fish.mr)))
                    else:
                        for keyword in fish_class.keyword:
                            fish.__setattr__(keyword, (fish.__getattribute__(keyword)+fish_class.amount[buff_index]))

    async def draft_combat(self, ctx, settings, draft_fish):
        rarities = ("uncommon","rare","epic","legendary")
        current_fish = []
        user_fish_hp = 0
        fish_levels = 1
        rarity = rarities[settings[0]['draft_level']]
        enemy_fish = []
        enemy_fish_hp = 0
        counter = 0
        
        for fish in draft_fish:
            temp_fish = copy.deepcopy(_Fish_Species.get_fish(fish['species']))
            if fish['item']:
                self.add_item(temp_fish, fish['item'])
            if fish['skin'] != "Normal":
                self.add_skin(temp_fish, fish['skin'])
            self.add_levels(temp_fish, fish['level'])
            fish_levels += fish['level']
            user_fish_hp += temp_fish.hp
            current_fish.append(temp_fish)

        amount = len(current_fish)
        level = int(fish_levels / amount)
        for _ in range(amount):
            temp_fish = copy.deepcopy(random.choice(_Fish_Species.get_fish_by_rarity(rarity)))
            self.add_levels(temp_fish, level)
            enemy_fish.append(temp_fish)
            enemy_fish_hp += temp_fish.hp
        current_regions, current_classes = self.configure_regions_and_classes(current_fish)
        self.region_class_start_of_combat(current_fish, enemy_fish, current_regions, current_classes)
        enemy_regions, enemy_classes = self.configure_regions_and_classes(current_fish)

        embed = self.show_combat(current_fish, enemy_fish, counter)
        combat_message = await ctx.send(embed=embed)
        while user_fish_hp > 0 and enemy_fish_hp > 0:
            starting_time = dt.utcnow()
            user_fish_hp = 0
            enemy_fish_hp = 0
            counter += 1
            await self.do_combat(ctx, current_fish, enemy_fish, current_regions, current_classes, enemy_regions, enemy_classes)
            for fish in current_fish.copy():
                if fish.hp <= 0:
                    current_fish.remove(fish)
                user_fish_hp += fish.hp
            for fish in enemy_fish.copy():
                if fish.hp <= 0:
                    enemy_fish.remove(fish)
                enemy_fish_hp += fish.hp
            current_regions, current_classes = self.configure_regions_and_classes(current_fish)
            enemy_regions, enemy_classes = self.configure_regions_and_classes(enemy_fish)
            embed = self.show_combat(current_fish, enemy_fish, counter)
            await combat_message.edit(embed=embed)
            await asyncio.sleep(1)



            
        embed = self.show_combat(current_fish, enemy_fish, counter)
        await combat_message.edit(embed=embed)
        result_string = self.show_result(user_fish_hp, enemy_fish_hp)
        await ctx.send(result_string)

    def combat_node():
        pass
    def shop_node():
        pass
    def orb_node():
        pass
    def bless_node():
        pass
    def fish_node():
        pass
    def mini_boss_node():
        pass
    def boss_node():
        pass
    def random_node():
        pass
   
    def make_map(level):
        nodes = level * 50
        made_nodes = 0
        graph = utils.Graph()
        temp_made = 0
        while made_nodes < nodes:
            last_amount = temp_made
            temp_made = random.randint(1,4)
            made_nodes += temp_made
            for _ in range(temp_made):
                node_name = random.choices(["combat_node", "shop_node", "orb_node", "bless_node", "fish_node", "mini_boss_node", "random_node"],
                                             [.5, .06, .2, .02, .02, .1, .1])
                created_node = utils.Node(node_name, False)
                graph.add_node(created_node)
            for i in reversed(range(last_amount)):
                graph.add_path(graph.get_node(made_nodes-i),)

        return graph
    
    def display_map(node_list):
        map_string = ""
        for index, level in enumerate(node_list):
            map_string += f"Level {len(node_list) - index}:\n"
            for node in level:
                map_string += f"{node[0]}\t"
            map_string += "\n"
            for node in level:
                map_string += f"({node[1]})\t"
            map_string += "\n"
        map_string += f"Start"
            
    @commands.command(application_command_meta=commands.ApplicationCommandMeta())
    @commands.bot_has_permissions(send_messages=True)
    async def team_planner(self, ctx: vbu.SlashContext):
        """Fake creates a team to see the synergies of certain fish"""
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

    @commands.command(application_command_meta=commands.ApplicationCommandMeta())
    @commands.bot_has_permissions(send_messages=True)
    async def team_creator(self, ctx: vbu.SlashContext):
        """Creates a team with your fish, uncommon and above fish only"""
        async with vbu.Database() as db:
            user_fish = await db("""SELECT * FROM user_fish_inventory WHERE user_id = $1 AND in_tank = FALSE""",
                     ctx.author.id)
            user_fish_team = await db("""SELECT * FROM user_fish_inventory WHERE user_id = $1 AND in_team = TRUE""",
                     ctx.author.id)
        fish_names = []
        fish_selected = 0
        
        for fish in user_fish_team:
            fish_selected += 1  
            fish_names.append(fish["species"])
        embed = self.add_fish_to_team(fish_names)
        buttons = [discord.ui.Button(custom_id="add", label=f"Add Fish To Team"),
                       discord.ui.Button(custom_id="remove", label=f"Remove Fish From Team"),
                       discord.ui.Button(custom_id="stop", label=f"Stop Editing")]
        components = discord.ui.MessageComponents(discord.ui.ActionRow(*buttons))
        embed_message = await ctx.send(embed=embed, components=components)
        while True:
            
            if fish_selected < 1:
                buttons[1].disable()
            else:
                buttons[1].enable()
            if fish_selected >= 5:
                buttons[0].disable()
            else:
                buttons[0].enable()
            components = discord.ui.MessageComponents(discord.ui.ActionRow(*buttons))
            await embed_message.edit(embed=embed, components=components)
            try:
                embed_button_payload = await self.bot.wait_for(
                    "component_interaction", 
                    timeout=60.0, 
                    check=lambda p: p.user.id == ctx.author.id and p.message.id == embed_message.id)
                chosen_button = embed_button_payload.component.custom_id.lower()
                await embed_button_payload.response.defer_update()
            except asyncio.TimeoutError:
                await embed_message.edit(components=components.disable_components())
                break
            if chosen_button == "add":
                first_fish_options = [single_fish["species"].replace('_', ' ').title() for single_fish in user_fish]
                for fish_name in first_fish_options[:]:
                    if _Fish_Species.get_fish(fish_name.replace(' ', '_').lower()).rarity == "common":
                        first_fish_options.remove(fish_name)
                for fish_name in fish_names[:]:
                    if fish_name.replace('_', ' ').title() in first_fish_options:
                        first_fish_options.remove(fish_name.replace('_', ' ').title())
                fish_options = []
                if len(first_fish_options) > 25:
                    fish_options = first_fish_options[:24]
                    fish_options.append("Next List")
                else:
                    fish_options = first_fish_options
                if len(first_fish_options) < 1:
                    await ctx.send("You have no more fish that are not Common!")
                else:
                    fish = await utils.create_select_menu(self.bot, ctx, fish_options, "fish", "select", True)
                    if fish == "Next List":
                        fish = await utils.create_select_menu(self.bot, ctx, first_fish_options[25:], "fish", "select", True)
                    if fish not in first_fish_options:
                        await embed_message.edit(components=components.disable_components())
                        break
                    fish_names.append(fish.replace(' ', '_').lower())
                    embed = self.add_fish_to_team(fish_names)
                    fish_selected += 1
            
                    async with vbu.Database() as db:
                        await db("""UPDATE user_fish_inventory SET in_team = TRUE WHERE user_id = $1 AND species = $2""",
                                ctx.author.id,
                                fish.replace(' ', '_').lower())
            elif chosen_button == "remove":
                fish = await utils.create_select_menu(self.bot, ctx, [fish.replace('_', ' ').title() for fish in fish_names], "fish", "select", True)
                if fish.replace(' ', '_').lower() not in fish_names:
                    await embed_message.edit(components=components.disable_components())
                    break
                fish_selected -= 1
                async with vbu.Database() as db:
                    await db("""UPDATE user_fish_inventory SET in_team = FALSE WHERE user_id = $1 AND species = $2""",
                                ctx.author.id,
                                fish.replace(' ', '_').lower())
                fish_names.remove(fish.replace(' ', '_').lower())
                embed = self.add_fish_to_team(fish_names)
            elif chosen_button == "stop":
                await embed_message.edit(components=components.disable_components())
                break
    
    @commands.command(application_command_meta=commands.ApplicationCommandMeta())
    @commands.bot_has_permissions(send_messages=True)
    async def arena(self, ctx: vbu.SlashContext):
        """Fights in an arena with your fish team against an opponent's fish"""

        # **Draft Code**
        # async with vbu.Database() as db:
        #     settings = await db("""SELECT * FROM user_settings WHERE user_id = $1""",
        #                         ctx.author.id)
        #     draft_fish = await db("""SELECT * FROM user_draft_fish WHERE user_id = $1""",
        #                     ctx.author.id)
        #     if len(draft_fish) == 0:
        #         await self.add_fish(ctx, settings, draft_fish, "uncommon", "Welcome to the draft. Choose your starting fish to begin:")
        #         draft_fish = await db("""SELECT * FROM user_draft_fish WHERE user_id = $1""",
        #                     ctx.author.id)
        # map = self.make_map()
        # self.display_map(map)
        # await self.draft_combat(ctx, settings, draft_fish)

        #await show_draft_info(ctx, settings)

        async with vbu.Database() as db:
            settings = await db("""SELECT * FROM user_settings WHERE user_id = $1""",
                                ctx.author.id)
            if not settings:
                await utils.add_user(ctx)
                settings = await db("""SELECT * FROM user_settings WHERE user_id = $1""",
                            ctx.author.id)
            fish_team = await db("""SELECT * FROM user_fish_inventory WHERE user_id = $1 AND in_team = TRUE""",
                                 ctx.author.id)
            if not fish_team:
                return await ctx.send("You have no fish on your team! Use `team_creator` to add fish Uncommon and greater to your team!")
            opponent_fish = []
            while len(opponent_fish) == 0:
                users = await db("""SELECT * FROM user_settings WHERE user_rank = $1 AND user_id != $2""",
                                settings[0]['user_rank'],
                                ctx.author.id)
                starting_index = utils.ranks.index(settings[0]['user_rank'])
                index = starting_index
                final_check = False
                while len(users) == 0 and index >= 0:
                    if not final_check:
                        index += 1
                    else:
                        index -= 1
                    users = await db("""SELECT * FROM user_settings WHERE user_rank = $1 AND user_id != $2""",
                                    utils.ranks[index],
                                    ctx.author.id)
                    if index == 23:
                        final_check = True
                        index == starting_index
                opponent = random.choice(users)
                opponent_fish = await db("""SELECT * FROM user_fish_inventory WHERE user_id = $1 AND in_team = TRUE""",
                                        opponent['user_id'],)

        user_fish = []
        user_fish_hp = 0
        for fish in fish_team:
            temp_fish = copy.deepcopy(_Fish_Species.get_fish(fish['species']))
            self.add_levels(temp_fish, fish['level'])
            if fish['item']:
                self.add_item(temp_fish, fish['item'])
            self.add_levers(temp_fish, settings[0])
            user_fish_hp += temp_fish.hp
            user_fish.append(temp_fish)

        enemy_fish = []
        enemy_fish_hp = 0
        for fish in opponent_fish:
            temp_fish = copy.deepcopy(_Fish_Species.get_fish(fish['species']))
            self.add_levels(temp_fish, fish['level'])
            if fish['item']:
                self.add_item(temp_fish, fish['item'])
            self.add_levers(temp_fish, opponent)
            enemy_fish_hp += temp_fish.hp
            enemy_fish.append(temp_fish)

        user_regions, user_classes = self.configure_regions_and_classes(user_fish)
        enemy_regions, enemy_classes = self.configure_regions_and_classes(enemy_fish)
        self.region_class_start_of_combat(user_fish, enemy_fish, user_regions, user_classes)
        self.region_class_start_of_combat(enemy_fish, user_fish, enemy_regions, enemy_classes)
        counter = 0
        embed = self.show_combat(user_fish, enemy_fish, counter)
        combat_message = await ctx.send(f"(<@{ctx.author.id}> VS <@{opponent['user_id']}>)", embed=embed, allowed_mentions=discord.AllowedMentions.none())
        while user_fish_hp > 0 and enemy_fish_hp > 0:
            starting_time = dt.utcnow()
            user_fish_hp = 0
            enemy_fish_hp = 0
            counter += 1
            await self.do_combat(ctx, user_fish, enemy_fish, user_regions, user_classes, enemy_regions, enemy_classes)
            for fish in user_fish.copy():
                if fish.hp <= 0:
                    user_fish.remove(fish)
                user_fish_hp += fish.hp
            for fish in enemy_fish.copy():
                if fish.hp <= 0:
                    enemy_fish.remove(fish)
                enemy_fish_hp += fish.hp
            user_regions, user_classes = self.configure_regions_and_classes(user_fish)
            enemy_regions, enemy_classes = self.configure_regions_and_classes(enemy_fish)
            embed = self.show_combat(user_fish, enemy_fish, counter)
            await combat_message.edit(embed=embed)
            await asyncio.sleep(1)

        async with vbu.Database() as db:
            user_rp = settings[0]['user_rp']
            user_rank = settings[0]['user_rank']
            if enemy_fish_hp <= 0:
                user_rp += self.find_changed_rp(settings[0]['user_rank'], opponent['user_rank'])
                result_message = f"You Won! You gained {self.find_changed_rp(settings[0]['user_rank'], opponent['user_rank'])} RP"
            else:
                user_rp -= self.find_changed_rp(settings[0]['user_rank'], opponent['user_rank'])
                result_message = f"You Lost! You lost {self.find_changed_rp(settings[0]['user_rank'], opponent['user_rank'])} RP"
            if user_rp >= 100:
                user_rp = user_rp - 100
                user_rank = utils.ranks[utils.ranks.index(settings[0]['user_rank'])+1]
            elif user_rp < 0:
                if utils.ranks.index(settings[0]['user_rank']) == 0:
                    user_rp = 0
                else:
                    user_rp = user_rp + 100
                    user_rank = utils.ranks[utils.ranks.index(settings[0]['user_rank'])-1]
            await db("""UPDATE user_settings SET user_rp = $1, user_rank = $2 WHERE user_id = $3""",
                        user_rp,
                        user_rank,
                        settings[0]['user_id'])
            result_message += f"\nYou are now **{user_rank}** at {user_rp} RP!"
        await ctx.send(result_message)
            
    # @commands.command(application_command_meta=commands.ApplicationCommandMeta())
    # @commands.bot_has_permissions(send_messages=True)
    # async def test_arena(self, ctx: vbu.SlashContext): 
    #     all_fish = _Fish_Species.get_fish_by_rarity("legendary")
    #     all_fish += _Fish_Species.get_fish_by_rarity("epic")
    #     all_fish += _Fish_Species.get_fish_by_rarity("rare")
    #     all_fish += _Fish_Species.get_fish_by_rarity("uncommon")
    #     fish_wins = {}
    #     fish_games = {}
    #     for fish in all_fish:
    #         for enemy_fish in all_fish:
    #             copy_fish = copy.deepcopy(fish)
    #             fish_list = []
    #             fish_list.append(copy_fish)
    #             copy_enemy_fish = copy.deepcopy(enemy_fish)
    #             if copy_fish.name not in fish_wins.keys():
    #                 fish_wins[copy_fish.name] = 0
    #                 fish_games[copy_fish.name] = 1
    #             else:
    #                 fish_games[copy_fish.name] += 1
    #             if copy_enemy_fish.name not in fish_wins.keys():
    #                 fish_wins[copy_enemy_fish.name] = 0
    #                 fish_games[copy_enemy_fish.name] = 1
    #             elif copy_enemy_fish.name != copy_fish.name:
    #                 fish_games[copy_enemy_fish.name] += 1
    #             user_fish_hp = copy_fish.hp
    #             enemy_fish_hp = copy_enemy_fish.hp
    #             enemy_fish_list = []
    #             enemy_fish_list.append(copy_enemy_fish)
    #             counter = 0
    #             current_regions, current_classes = self.configure_regions_and_classes(fish_list)
    #             self.region_class_start_of_combat(fish_list, enemy_fish_list, current_regions, current_classes)
    #             enemy_regions, enemy_classes = self.configure_regions_and_classes(enemy_fish_list)
    #             while user_fish_hp > 0 and enemy_fish_hp > 0:
    #                 current_regions, current_classes = self.configure_regions_and_classes(fish_list)
    #                 enemy_regions, enemy_classes = self.configure_regions_and_classes(enemy_fish_list)
    #                 user_fish_hp = copy_fish.hp
    #                 enemy_fish_hp = copy_enemy_fish.hp
    #                 await self.do_combat(ctx, fish_list, enemy_fish_list, current_regions, current_classes, enemy_regions, enemy_classes)
    #                 counter += 1
    #                 if counter > 300:
    #                     enemy_fish_hp = 0
    #                     break
    #             if enemy_fish_hp <= 0:
    #                 fish_wins[copy_fish.name] += 1
    #             elif user_fish_hp <= 0:
    #                 fish_wins[copy_enemy_fish.name] += 1
    #     fish_record_dict = {}
    #     for fish in all_fish:
    #         fish_record_dict[fish.name] = fish_wins[fish.name]/fish_games[fish.name]
    #     fish_record_dict = {k: v for k, v in sorted(fish_record_dict.items(), key=lambda item: item[1])}
    #     fish_record = ""
    #     for fish, percent in fish_record_dict.items():
    #         fish_record += f"{_Fish_Species.get_fish(fish).rarity[0]} {fish}: {percent:.2f}\n"
    #     await ctx.send(f"{fish_record}\n\n\n")

    #     fish_wins = {}
    #     fish_games = {}
    #     for _ in range(15000):
    #         current_fish = []
    #         starting_current = []
    #         user_fish_hp = 0
    #         enemy_fish = []
    #         starting_enemy = []
    #         enemy_fish_hp = 0
    #         counter = 0
    #         for _ in range(5):
    #             temp_fish = copy.deepcopy(random.choice(_Fish_Species.get_fish_by_rarity("legendary")))
    #             enemy_fish.append(temp_fish)
    #             starting_enemy.append(temp_fish)
    #             if temp_fish.name not in fish_games.keys():
    #                 fish_wins[temp_fish.name] = 0
    #                 fish_games[temp_fish.name] = 1
    #             else:
    #                 fish_games[temp_fish.name] += 1
    #             enemy_fish_hp += temp_fish.hp
    #             temp_user_fish = copy.deepcopy(random.choice(_Fish_Species.get_fish_by_rarity("legendary")))
    #             current_fish.append(temp_user_fish)
    #             starting_current.append(temp_user_fish)
    #             if temp_user_fish.name not in fish_games.keys():
    #                 fish_wins[temp_user_fish.name] = 0
    #                 fish_games[temp_user_fish.name] = 1
    #             else:
    #                 fish_games[temp_user_fish.name] += 1
    #             user_fish_hp += temp_user_fish.hp
    #         current_regions, current_classes = self.configure_regions_and_classes(current_fish)
    #         self.region_class_start_of_combat(current_fish, enemy_fish, current_regions, current_classes)
    #         enemy_regions, enemy_classes = self.configure_regions_and_classes(enemy_fish)
    #         self.region_class_start_of_combat(current_fish, enemy_fish, enemy_regions, enemy_classes)
    #         while user_fish_hp > 0 and enemy_fish_hp > 0:
    #             current_regions, current_classes = self.configure_regions_and_classes(current_fish)
    #             enemy_regions, enemy_classes = self.configure_regions_and_classes(enemy_fish)
    #             user_fish_hp = 0
    #             enemy_fish_hp = 0
    #             counter += 1
    #             await self.do_combat(ctx, current_fish, enemy_fish, current_regions, current_classes, enemy_regions, enemy_classes)
    #             for fish in current_fish.copy():
    #                 if fish.hp <= 0:
    #                     current_fish.remove(fish)
    #                 user_fish_hp += fish.hp
    #             for fish in enemy_fish.copy():
    #                 if fish.hp <= 0:
    #                     enemy_fish.remove(fish)
    #                 enemy_fish_hp += fish.hp
    #             counter += 1
    #             if counter > 300:
    #                 enemy_fish_hp = 0
    #                 break
    #         if enemy_fish_hp <= 0:
    #             for fish in starting_current:
    #                 fish_wins[fish.name] += 1
    #         elif user_fish_hp <= 0:
    #             for fish in starting_enemy:
    #                 fish_wins[fish.name] += 1
    #     fish_record_dict = {}
    #     for fish in all_fish:
    #         fish_record_dict[fish.name] = fish_wins[fish.name]/fish_games[fish.name]
    #     fish_record_dict = {k: v for k, v in sorted(fish_record_dict.items(), key=lambda item: item[1])}
    #     fish_record = ""
    #     for fish, percent in fish_record_dict.items():
    #         fish_record += f"{_Fish_Species.get_fish(fish).rarity[0]} {fish}: {percent:.2f}\n"
    #     await ctx.send(fish_record)

def setup(bot):


    bot.add_cog(Arena(bot))






