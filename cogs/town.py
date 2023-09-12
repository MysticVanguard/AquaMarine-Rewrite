import random
import asyncio
import discord
from datetime import datetime as dt, timedelta
from discord.ext import commands, tasks, vbu

from cogs import utils


class Town(vbu.Cog):

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
                    if settings[0]['sand_dollars'] < item.price:
                        item_message = await ctx.send("You don't have enough money!", ephemeral = True)
                    else:
                        if item.ref[0] == "net":
                            if settings[0]['has_net']:
                                item_message = await ctx.send("You already have a net!", ephemeral = True)
                                cant_buy = True
                            else:
                                await db("""UPDATE user_settings SET has_net = TRUE, net_type = $1, net_hp= $2 WHERE user_id = $3""",
                                            item.display_name.replace(" ", "_").lower(),
                                            item.ref[1],
                                            ctx.author.id)
                        elif item.ref == "tank":
                            await db("""UPDATE user_settings SET tank_room = $1 WHERE user_id = $2""",
                                     settings[0]['tank_room']+1,
                                     ctx.author.id)
                        elif item.ref[0] == "bait":
                            await db("""UPDATE user_settings SET bait_amount = $1 WHERE user_id = $2""",
                                    utils.change_bait(settings[0]['bait_amount'], item.ref[1]),
                                     ctx.author.id)
                        if not cant_buy:
                            item_message = await ctx.send(f"You bought 1 {item.display_name}", ephemeral = True)
                            await db("""UPDATE user_settings SET sand_dollars = $1 WHERE user_id = $2""",
                                        settings[0]["sand_dollars"]-item.price,
                                        ctx.author.id)
                await item_message.delete(delay = 5)

        await ctx.interaction.delete_original_message()

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

        question_embed = vbu.Embed(
            title = category,
            description = "Choose an item!",
            use_random_colour=True
        )

        item_buttons = [
            discord.ui.Button(
                label=f"{item.display_name} (${item.price})",
                custom_id=f"ITEM_OPT_{item.display_name}"
            )
            for item in category_items.values()
        ]

        if send_new:
            question_message = await ctx.send(
                embed = question_embed,
                components = discord.ui.MessageComponents(
                                discord.ui.ActionRow(
                                    discord.ui.Button(
                                        label="Exit",
                                        custom_id=f"ITEM_BACK",
                                        style=discord.ButtonStyle.danger
                                    )
                                ),
                                discord.ui.ActionRow(*item_buttons)
                            ),
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


def setup(bot):
    bot.add_cog(Town(bot))