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
            ability: str
):
        self.name = name
        self.rarity = rarity
        self.lever = lever
        self.region = []
        self.fish_class = []
        self.hp = hp
        self.ad = ad
        self.ap = 100
        self.ar = ar
        self.mr = mr
        self.haste = haste
        self.mana = mana
        self.ability = ability
        if (region != ""):
            for single_region in region.split(","):
                print(single_region)
                self.region.append(Region.get_region(single_region))
            for single_fish_class in fish_class.split(","):
                self.fish_class.append(Fish_Class.get_fish_class(single_fish_class))
        self.all_species_by_name[name] = self
        if rarity not in self.all_species_by_rarity.keys():
            self.all_species_by_rarity[rarity] = [self]
        elif self.name not in [obj.name for obj in self.all_species_by_rarity[rarity]]:
            self.all_species_by_rarity[rarity].append(self)

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
    
all_fish = []
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
                                range="A2:E126").execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')

    for row in values:
        if (len(row) > 3):
            all_fish.append(_Fish_Species(row[0].lower().replace(" ", "_"),row[1], row[2], row[3].lower().replace(" ", "_"), row[4].lower().replace(" ", "_"), "", "", "", "", "", "", ""))
        elif (len(row) == 3 and row[0] != "" and row[1] != "" and row[2] != ""):
            all_fish.append(_Fish_Species(row[0].lower().replace(" ", "_"),row[1], row[2], "", "", "", "", "", "", "", "", ""))
except HttpError as err:
    print(err)

lever_info = {}
try:
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range="A128:C163").execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')

    for row in values:
        lever_info[row[0]] = (int(row[1]), list(map(int, row[2].split("/"))))
        
except HttpError as err:
    print(err)