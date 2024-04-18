import time

from bininterface import binAcces
from sqlInterface import sqlAcces


class Basics():

    def __init__(self):
        self.sql = sqlAcces()
        self.bin = binAcces()

    def plus_proche(self,symbol):
        ecart_bet_tab = self.sql.get_ecart_bet_from_symbol(symbol)
        prix_tmp = self.bin.get_price(symbol)
        prix = prix_tmp["price"]
        delta = abs(float(ecart_bet_tab[0][2])-float(prix))
        prix_proche_ID=0
        for ecart_bet in ecart_bet_tab:
            if abs(float(prix)-float(ecart_bet[2]))<delta:
                delta = abs(float(prix)-float(ecart_bet[2]))
                prix_proche_ID = ecart_bet[0]
        return prix_proche_ID
    
    def initialise(self,symbol):
        GO = False
        ordres_ouverts = self.sql.get_orders_status_symbol_filter(self.bin.client.ORDER_STATUS_NEW,symbol)
        if len(ordres_ouverts) == 2:
            changement = self.bin.changement_status(symbol)
            print("changement : "+ str(changement))
            if changement == []:
                GO = True
            else:
                self.bin.changement_update(changement)
        print("GO : "+str(GO))
        if GO == False:
            changement = self.bin.changement_status(symbol)
            self.bin.changement_update(changement)
            ordres_ouverts = self.sql.get_orders_status_symbol_filter(self.bin.client.ORDER_STATUS_NEW,symbol)
            for ordre_ouvert in ordres_ouverts:
                self.bin.cancel_order(ordre_ouvert["ID"])
            last_close = self.sql.get_last_filled(symbol)
            if last_close != "":
                ID_ecart_last_close = last_close["ID_ecart"]
            else:
                ID_ecart_last_close = self.plus_proche(symbol)
            print(ID_ecart_last_close)
            self.bin.new_achat(symbol,ID_ecart_last_close)
            self.bin.new_vente(symbol,ID_ecart_last_close)
    
###########################################################################
#                                 MAIN                                    #
###########################################################################
def main():
    DEVISE="DOGEBTC"
    basic = Basics()

    ################################################
    #    Initialisation
    ################################################
    basic.initialise(DEVISE)
    while True:
        time.sleep(5)
        basic.sql.get_time_since_open(DEVISE)
        changement = basic.bin.changement_status(DEVISE)
        if changement != []:
            basic.bin.changement_update(changement)
            ordres_ouverts = basic.sql.get_orders_status_symbol_filter(basic.bin.client.ORDER_STATUS_NEW,DEVISE)
            for odb in ordres_ouverts:
                    basic.bin.cancel_order(odb["ID"])
            last_filled_order = basic.sql.get_last_filled(DEVISE)
            basic.bin.new_achat(DEVISE,last_filled_order["ID_ecart"])
            basic.bin.new_vente(DEVISE,last_filled_order["ID_ecart"])



if __name__ == '__main__':
     main()

