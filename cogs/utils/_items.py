from __future__ import annotations

from typing import Any
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from apiclient import discovery


items = {
    "Tier 1": ["coral", "shell", "seaweed", "crab_claw", "pebble", "scale", 
               "tire", "plastic_bag", "boot"],
    "Tier 2": {},
    "Tier 3": {},
}

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

        self.add_item(Item("Wooden Net", 10, "Wooden Net with 5 HP used for /fish", 
                      ("net", 5)))
        self.add_item(Item("Plastic Net", 50, "Plastic Net with 25 HP used for /fish", 
                           ("net", 25)))
        self.add_item(Item("Metal Net", 250, "Metal Net with 125 HP used for /fish", 
                           ("net", 125)))
        self.add_item(Item("Fish Tank +1 Room", 100, "Gives you one more room for fish in your tank", 
                           ("tank")))

class FishMarket(Category):

    def __init__(self):
        super().__init__("Baits")

        self.add_item(Item("Common Bait", 10, "Used as okay bait for the fishing rod in /fish", 
                           ("bait", "common_bait")))
        self.add_item(Item("Uncommon Bait", 20, "Used as good bait for the fishing rod in /fish", 
                           ("bait", "uncommon_bait")))
        self.add_item(Item("Rare Bait", 30, "Used as great bait for the fishing rod in /fish", 
                           ("bait", "rare_bait")))

class SkinMarket(Category):

    def __init__(self):
        super().__init__("Skins")

        self.add_item(Item("Candyland", 140, "Candyland skin with \nTier 1: Atlantic Needlefish, Boxer Crab, Sea Bunny, Hairy Squat Lobster\nTier 2: Flowerhorn Cichlid, Great Crested Newt",
                            ("doubloon", "skin")))
        self.add_item(Item("Upgraded", 140, "Upgraded skin with \nTier 1: Atlantic Needlefish, Boxer Crab, Sea Bunny, Dumbo Octopus\nTier 2: Longspine Pufferfish, Turquise Rainbowfish\nTier 3: Drakefish", 
                           ("doubloon", "skin")))
        self.add_item(Item("Draconic", 140, "Draconic skin with \nTier 1: Crawfish, Lionfish, Mandarinfish, White Red Cap Goldfish\nTier 2: Current Darter School, Yellow Boxfish\nTier 3: Ifish", 
                           ("doubloon", "skin")))
        self.add_item(Item("Choose Single Skin", 0, "Choose to buy a single skin from one of the skin lines (prices varies from 10, 30, and 50 doubloons)", 
                           ("choose_skin")))

class ConsumableMarket(Category):

    def __init__(self):
        super().__init__("Consumables WIP")

        self.add_item(Item("Candy", 10, "WIP"))
        self.add_item(Item("Spells", 100, "WIP"))
        self.add_item(Item("Bones", 1_000, "WIP"))

class ScrapMarket(Category):

    def __init__(self):
        super().__init__("Tier 1 Items")

        self.add_item(Item("Coral", 50, "Used for crafting items for your fish", ('tier_1', 'coral')))
        self.add_item(Item("Shell", 50, "Used for crafting items for your fish", ('tier_1', 'shell')))
        self.add_item(Item("Crab Claw", 50, "Used for crafting items for your fish", ('tier_1', 'crab_claw')))
        self.add_item(Item("Pebble", 50, "Used for crafting items for your fish", ('tier_1', 'pebble')))
        self.add_item(Item("Scale", 50, "Used for crafting items for your fish", ('tier_1', 'scale')))
        self.add_item(Item("Seaweed", 50, "Used for crafting items for your fish", ('tier_1', 'seaweed')))
        self.add_item(Item("Tire", 50, "Used for crafting items for your fish", ('tier_1', 'tire')))
        self.add_item(Item("Plastic Bag", 50, "Used for crafting items for your fish", ('tier_1', 'plastic_bag')))
        self.add_item(Item("Boot", 50, "Used for crafting items for your fish", ('tier_1', 'boot')))



class Item:

    def __init__(self, display_name: str, price: int, description: str, ref: Any = None):
        self.display_name = display_name
        self.price = price
        self.ref = ref
        self.description = description

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"Item({self.display_name}, ${self.price})"

FishingMarket()
FishMarket()
SkinMarket()
#ConsumableMarket()
ScrapMarket()


class FishItem():

    def __init__(
            self,
            name: str,
            tier: int,
            coral: int,
            shell: int,
            crab_claw: int,
            pebble: int,
            scale: int,
            seaweed: int,
            tire: int,
            plastic_bag: int,
            boot: int,
            components: list[FishItem]
    ):
        self.name = name
        self.tier = tier
        self.coral = coral
        self.shell = shell
        self.crab_claw = crab_claw
        self.pebble = pebble
        self.scale = scale
        self.seaweed = seaweed
        self.tire = tire
        self.plastic_bag = plastic_bag
        self.boot = boot
        self.components = components


SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1fh8WMLVU15fgfHVS_39ie81WgoImt2Unvum4Yr-Ccgk'

creds = None
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.json'):
    creds = service_account.Credentials.from_service_account_file('token.json', scopes=SCOPES)



try:
    service = discovery.build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range="A290:L306").execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')

    for row in values:
        if len(row) < 11:
            items['Tier 2'][row[0]] = FishItem(row[0],'Tier 1',row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],[])
        else:
            components = [row[10], row[11]]
            items['Tier 3'][row[0]] = FishItem(row[0],'Tier 2',row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],components)
except HttpError as err:
    print(err)





        