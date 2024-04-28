from __future__ import print_function, annotations
from ._fish_type import _FishType
from ._regions import Region
from ._fish_classes import Fish_Class

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from apiclient import discovery

class _Fish_Species:
    all_species_by_name = {}
    all_species_by_rarity = {}
    skins = []
    def __init__(
            self, 
            name: str, 
            rarity: str, 
            lever: str, 
            region: str, 
            fish_class: str, 
            hp: str, 
            ad: str, 
            ar: str, 
            mr: str, 
            haste: str, 
            mana: str, 
            ability: str,
            ability_string: str,
):
        self.name = name
        self.rarity = rarity
        self.lever = lever
        self.region = []
        self.fish_class = []
        self.hp = int(hp)
        self.max_hp = int(hp)
        self.ad = int(ad)
        self.ap = 100
        self.ar = int(ar)
        self.mr = int(mr)
        self.haste = int(haste)
        self.mana = int(mana)
        self.curr_mana = 0
        self.stunned = 0
        self.crit_chance = 25
        self.crit_damage = 150
        self.mark = 0
        self.level = 0
        self.stunproof = 0
        self.item = ""
        self.ability = ability
        self.ability_string = ability_string
        if (region != ""):
            for single_region in region.split(","):
                self.region.append(Region.get_region(single_region))
            for single_fish_class in fish_class.split(","):
                self.fish_class.append(Fish_Class.get_fish_class(single_fish_class))
        self.all_species_by_name[name] = self
        if rarity not in self.all_species_by_rarity.keys():
            self.all_species_by_rarity[rarity] = [self]
        elif self.name not in [obj.name for obj in self.all_species_by_rarity[rarity]]:
            self.all_species_by_rarity[rarity].append(self)
        for skin in skins:
            if skin[0] == name:
                self.skins.append(skin)

        # self.flags = {
        #     is_stunned: bool
        #     is_marked: _Fish
        #     is_taunted: _Fish
        #     forced_target: _Fish
        #     has_died: bool
        #     has_revives: bool
        # }

    @classmethod
    def get_fish(cls, name: str) -> _Fish_Species:
        return cls.all_species_by_name[name]
    
    @classmethod
    def get_fish_by_rarity(cls, rarity: str) -> list[_Fish_Species]:
        return cls.all_species_by_rarity[rarity]


class _Large_Fish_Species:
    all_species_by_rarity = {}

    def __init__(
            self,
            name: str,
            rarity: str
):
        self.name = name
        self.rarity = rarity
        if rarity not in self.all_species_by_rarity.keys():
            self.all_species_by_rarity[rarity] = [self]
        elif self.name not in [obj.name for obj in self.all_species_by_rarity[rarity]]:
            self.all_species_by_rarity[rarity].append(self)

    @classmethod
    def get_fish_by_rarity(cls, rarity: str) -> list[_Fish_Species]:
        return cls.all_species_by_rarity[rarity]

all_fish = []
all_large_fish = []
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1fh8WMLVU15fgfHVS_39ie81WgoImt2Unvum4Yr-Ccgk'

creds = None
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.json'):
    creds = service_account.Credentials.from_service_account_file('token.json', scopes=SCOPES)

skins = []
try:
    service = discovery.build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range="G128:I148").execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')

    for row in values:
            skins.append((row[0],row[1],row[2]))
        
except HttpError as err:
    print(err)

try:
    service = discovery.build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range="A2:N126").execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')

    for row in values:
        if row[0] == "":
            continue
        if (len(row) > 3):
            all_fish.append(_Fish_Species(row[0].lower().replace(" ", "_"),row[1], row[2], row[3].lower().replace(" ", "_"), row[4].lower().replace(" ", "_"), row[5], row[6], row[8], row[9], row[10], row[11], row[12], row[13]))
        elif (len(row) == 3 and row[1] != "" and row[2] != ""):
            all_fish.append(_Fish_Species(row[0].lower().replace(" ", "_"),row[1], row[2], "", "", 0, 0, 0, 0, 0, 0, "", ""))
except HttpError as err:
    print(err)

lever_info = {}
try:
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range="A128:C158").execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')

    for row in values:
        lever_info[row[0]] = (int(row[1]), list(map(int, row[2].split("/"))))
        
except HttpError as err:
    print(err)

try:
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range="A209:B241").execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')

    for row in values:
        all_large_fish.append(_Large_Fish_Species(row[0], row[1]))
        
except HttpError as err:
    print(err)


