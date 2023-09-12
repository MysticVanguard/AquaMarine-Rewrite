from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from apiclient import discovery
import os.path

class Fish_Class:
    all_fish_classes_by_name = {}
    def __init__(self, name, breakpoints, keyword, amount, decaying, trigger, targets, description):
        self.name = name
        self.breakpoints = list(map(int, breakpoints.split(',')))
        self.keyword = keyword.split(',')
        self.amount = list(map(int, amount.split(',')))
        self.decaying = bool(decaying)
        self.trigger = trigger
        self.targets = targets.split(',')
        self.description = description
        self.all_fish_classes_by_name[name] = self
    @classmethod
    def get_fish_class(cls, name: str):
        return cls.all_fish_classes_by_name[name]
all_fish_classes = []
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
                                range="A186:H195").execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')

    for row in values:
        all_fish_classes.append(Fish_Class(row[0],row[1], row[2], row[3], row[4], row[5], row[6], row[7]))
except HttpError as err:
    print(err)