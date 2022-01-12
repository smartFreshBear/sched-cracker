from __future__ import print_function

import os.path
import pickle
import gc

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.discovery_cache.base import Cache

from uxui.uiobjects.Cell import *
import re


PATH_TO_CRED = "token.pickle"

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

LOCATION_OF_ALL_SHEET = 'A1:T32'

class MemoryCache(Cache):
    _CACHE = {}

    def get(self, url):
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        MemoryCache._CACHE[url] = content


class SpreadsheetClient:

    @staticmethod
    def get_spreadsheetservice():
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    PATH_TO_CRED, SCOPES)
                creds = flow.run_local_server(port=58326)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        service = build('sheets', 'v4', credentials=creds, cache=MemoryCache())
        return service

    def __init__(self, sheet_id):
        self.spreadsheet_service = self.get_spreadsheetservice().spreadsheets()
        self.sheet_id = sheet_id
        self.all_cells_of_sheet = self.spreadsheet_service.values().get(spreadsheetId=self.sheet_id,
                                    range=LOCATION_OF_ALL_SHEET).execute()

    def load_cells_given_pair(self, pair_str):
        splitted_to_cells = pair_str.split(':')
        return self.load_cells_given_from_to(splitted_to_cells[0], splitted_to_cells[1])


    @staticmethod
    def from_letter_to_number(letter):
        return [ord(x) - 96 for x in letter.lower()].pop()

    def load_cells_given_from_to(self, from_cell, to_cell) -> list[list[Cell]]:


        from_row = int(re.split('(\d+)', from_cell)[1]) - 1
        to_row = int(re.split('(\d+)', to_cell)[1])

        from_column = self.from_letter_to_number(re.split('(\d+)', from_cell)[0]) - 1
        to_column = self.from_letter_to_number(re.split('(\d+)', to_cell)[0])

        relevant_cells = [sheet_raw_row[from_column: to_column] for sheet_raw_row in self.all_cells_of_sheet['values'][from_row: to_row]]

        cell_table = list()
        for given_raw in relevant_cells:
            row_of_cells = list()
            for sheet_cell_value in given_raw:
                row_of_cells.append(Cell(text=sheet_cell_value))
            cell_table.append(row_of_cells)

        return cell_table

    def update_cells_given_from_to_and_cells(self, from_cell, to_cell, cells: list[list[Cell]]) -> bool:

        def from_cell_row_str_row(row):
            return list(map(lambda c: c.text, row))

        rows = list(map(from_cell_row_str_row, cells))

        body = {
            'values': rows
        }

        request = self.spreadsheet_service.values().append(spreadsheetId=self.sheet_id,
                                                           range='{}:{}'.format(from_cell, to_cell),
                                                           valueInputOption='RAW',
                                                           insertDataOption='OVERWRITE',
                                                           body=body)
        response = request.execute()

        return response is not None

