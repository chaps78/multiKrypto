import time

from bininterface import binAcces
from sqlInterface import sqlAcces
from KPI import Kpi
from telegramInterface import teleAcces
from sheetInterface import sheetAcces

class Clients():
    def __init__(self):
        self.sql = sqlAcces()
        self.bin = binAcces()


    def display_wallet(self,client):
        wallet = self.bin.get_wallet(client)
        for el in wallet:
            print(el)
    
    def market_order(self,client):
        symbol = input("select pair\n")
        montant = input("amount\n")
        sens = input("BUY/SELL\n")
        
        self.bin.new_market_order(symbol,montant,sens,client)
    
    def list_orders(self,ID_client,symbol):
        symbol_splited = symbol.split("_")[0]
        orders = self.bin.clients[ID_client].get_all_orders(symbol=symbol_splited)
        print("##################################")
        for order in orders:
            if order['status'] == "NEW" or order['status'] == "PARTIAL":
                print("ID : " + str(order["orderId"]) + "\tSide : " + order["side"] + "\tLimite : " 
                      + str(order['price']) + "\tAmount : " + str(order['origQty']))

def main():
    Client = Clients()
    clients_liste = Client.sql.get_clients_infos()
    print("Select a client:")
    for client in clients_liste:
        print(str(client)+" - "+ str(clients_liste[client]["name"]))
    client = int(input("Enter your choice : "))
    print("\n\t#######################\n")

    print("What action do you whant to do?")
    print("1 - Display Wallet\n2 - Market order\n3 - Open orders list")
    action_selected = input("Enter your choice : ")
    if action_selected == "1":
        Client.display_wallet(client)

    elif action_selected == "2":
        Client.market_order(client)
    elif action_selected == "3":
        symbol = input("Whith symbol : ")
        Client.list_orders(client,symbol)




if __name__ == '__main__':
     main()