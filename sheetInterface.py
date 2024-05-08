from oauth2client.service_account import ServiceAccountCredentials
import gspread
from sqlInterface import sqlAcces







class sheetAcces():
    def __init__(self):
        scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('cred.json', scope)
        client = gspread.authorize(creds)
        self.sheet = client.open("binance")
        self.sql = sqlAcces()
    
    def update_values(self,symbol):
        ecart = self.sql.get_ecart_bet_from_symbol(symbol)
        wsheet = self.sheet.worksheet('XRPEUR')
        keys = ecart.keys()
        ecart_tab=[]
        for key in keys:
            ecart_tab.append([key,ecart[key][0],ecart[key][1]])
        wsheet.update('A2', ecart_tab)
        ajout = self.sql.get_ajout_entier_dic(symbol)
        breakpoint()


def main():    
    sheet = sheetAcces()
    sheet.update_values("XRPEUR")

    


if __name__ == '__main__':
     main()