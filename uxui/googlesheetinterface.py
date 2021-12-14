from __future__ import print_function

import os.path
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from uxui.uiobjects.Cell import *

PATH_TO_CRED = "token.pickle"

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.

# TODO remove and take as parameter
SAMPLE_SPREADSHEET_ID = '1HMsTxrDeekNQRVNaTQT3xg3iksvzHVzQ_PCIx1xPsTE'



class SpreadsheetClient:

    @staticmethod
    def get_spreadsheetservice():
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
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
        service = build('sheets', 'v4', credentials=creds)
        return service

    def __init__(self, sheet_id):
        self.spreadsheet_service = self.get_spreadsheetservice()
        self.sheet_id = sheet_id

    def load_constraints_given_pair(self, pair_str):
        splitted_to_cells = pair_str.split(':')
        return self.load_cells_given_from_to(splitted_to_cells[0], splitted_to_cells[1])

    def load_cells_given_from_to(self, from_cell, to_cell) -> list[list[Cell]]:
        cell_range = '{}:{}'.format(from_cell, to_cell)
        sheet = self.spreadsheet_service.spreadsheets()

        result = sheet.get(spreadsheetId=self.sheet_id,
                           includeGridData=True,
                           ranges=cell_range).execute()

        cell_table = list()
        for row in result['sheets'][0]['data'][0]['rowData']:
            row_of_cells = list()
            for sheet_cell in row['values']:
                entered_value = sheet_cell.get('userEnteredValue', None)
                user_str = '' if entered_value is None else entered_value['stringValue']
                cell = Cell(color=sheet_cell['effectiveFormat']['backgroundColor'], text=user_str)
                row_of_cells.append(cell)
            cell_table.append(row_of_cells)

        return cell_table

    def update_cells_given_from_to_and_cells(self, from_cell, to_cell, cells: list[list[Cell]]) -> bool:

        def from_cell_row_str_row(row):
            return list(map(lambda c: c.text, row))

        rows = list(map(from_cell_row_str_row, cells))

        body = {
            'values': rows
        }

        request = self.spreadsheet_service.spreadsheets().values().append(spreadsheetId=self.sheet_id,
                                                        range='{}:{}'.format(from_cell,to_cell),
                                                        valueInputOption='RAW',
                                                        insertDataOption='OVERWRITE',
                                                        body=body)
        response = request.execute()

        return response is not None


if __name__ == '__main__':

    client = SpreadsheetClient('1bIqr2NTI51xVMCtROVq2IOltztkArZLvmtPyJvXvbXs')

    table = client.load_cells_given_from_to('E13', 'I15')
    lst = ['what', 'am', 'I', 'doing', 'with', 'my', 'life', 'now']
    for row in table:
        for i, cell in enumerate(row):
            cell.text = lst[i % 8]

    worked = client.update_cells_given_from_to_and_cells('E13', 'I15', table)
    assert worked


