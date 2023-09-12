from __future__ import annotations

from typing import Any


class Category:
    _categories: dict[str, Category] = {}

    def __init__(self, display_name: str):
        self.display_name = display_name
        self.items: dict[str, Item] = {}

        Category._categories[display_name] = self

    def add_item(self, item: Item):
        self.items[item.display_name] = item

    @staticmethod
    def get_categories():
        return Category._categories

class FishingMarket(Category):

    def __init__(self):
        super().__init__("Fishing")

        self.add_item(Item("Wooden Net", 10, ("net", 5)))
        self.add_item(Item("Plastic Net", 50, ("net", 25)))
        self.add_item(Item("Metal Net", 250, ("net", 125)))
        self.add_item(Item("Fish Tank +1 Room", 100, ("tank")))

class FishMarket(Category):

    def __init__(self):
        super().__init__("Baits")

        self.add_item(Item("Common Bait", 10, ("bait", "common")))
        self.add_item(Item("Uncommon Bait", 20, ("bait", "uncommon")))
        self.add_item(Item("Rare Bait", 30, ("bait", "rare")))

class SkinMarket(Category):

    def __init__(self):
        super().__init__("Skins WIP")

        self.add_item(Item("Candyland", 10))
        self.add_item(Item("Robotica", 100))
        self.add_item(Item("Cosmic", 1_000))

class ConsumableMarket(Category):

    def __init__(self):
        super().__init__("Consumables WIP")

        self.add_item(Item("Candy", 10))
        self.add_item(Item("Spells", 100))
        self.add_item(Item("Bones", 1_000))

class ScrapMarket(Category):

    def __init__(self):
        super().__init__("Scraps WIP")

        self.add_item(Item("Wooden Scraps", 10))
        self.add_item(Item("Metal Scraps", 100))


class Item:

    def __init__(self, display_name: str, price: int, ref: Any = None):
        self.display_name = display_name
        self.price = price
        self.ref = ref

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"Item({self.display_name}, ${self.price})"

FishingMarket()
FishMarket()
SkinMarket()
ConsumableMarket()
ScrapMarket()