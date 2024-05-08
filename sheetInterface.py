from oauth2client.service_account import ServiceAccountCredentials
import gspread
from sqlInterface import sqlAcces



wsheet = sheet.worksheet('XRPEUR')
KPI_tab=[["aa1","aa2"],["bb1","bb2"]]
wsheet.update('H3', KPI_tab)

sql = sqlAcces()

class sheetAcces():
    def __init__(self):
        scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('cred.json', scope)
        client = gspread.authorize(creds)
        self.sheet = client.open("binance")
        self.sql = sqlAcces()


def main():    
    sheet = sheetAcces()

    


if __name__ == '__main__':
     main()