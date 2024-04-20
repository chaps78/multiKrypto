import time

from bininterface import binAcces
from sqlInterface import sqlAcces
from KPI import Kpi


class Basics():

    def __init__(self):
        self.sql = sqlAcces()
        self.bin = binAcces()
        self.kpi = Kpi()

    def plus_proche(self,symbol):
        ecart_bet_dic = self.sql.get_ecart_bet_from_symbol(symbol)
        prix_tmp = self.bin.get_price(symbol)
        prix = prix_tmp["price"]
        delta = abs(float(ecart_bet_dic[0][1])-float(prix))
        prix_proche_ID=0
        keys = ecart_bet_dic.keys()
        for key in keys:
            if abs(float(prix)-float(ecart_bet_dic[key][1]))<delta:
                delta = abs(float(prix)-float(ecart_bet_dic[key][1]))
                prix_proche_ID = key
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
            self.bin.new_vente(symbol,ID_ecart_last_close)
            self.bin.new_achat(symbol,ID_ecart_last_close)

    def verification_2_ordres(self,symbol):
        changement = self.bin.changement_status(symbol)
        if changement != []:
            self.bin.changement_update(changement)
            ordres_ouverts = self.sql.get_orders_status_symbol_filter(self.bin.client.ORDER_STATUS_NEW,symbol)
            for odb in ordres_ouverts:
                    self.bin.cancel_order(odb["ID"])
            last_filled_order = self.sql.get_last_filled(symbol)
            self.bin.new_achat(symbol,last_filled_order["ID_ecart"])
            self.bin.new_vente(symbol,last_filled_order["ID_ecart"])
            self.kpi.reste_sur_limites(symbol)

    def verification_niveau_VS_timer(self,symbol):
        niveaux = self.sql.get_time_since_open(symbol)
        keys = niveaux.keys()
        for key in keys:
            #Delais d attente de 30 min pour un ordre niveau 4
            if int(niveaux[key]["niveau"]) == 4 and niveaux[key]["time"].seconds > 1800:
                self.bin.baisser_niveau_ordre(key)
            # Delas d attente de 3 heures pour un ordre de niveau 3
            if int(niveaux[key]["niveau"]) == 3 and niveaux[key]["time"].seconds > 10800:
                self.bin.baisser_niveau_ordre(key)
    
###########################################################################
#                                 MAIN                                    #
###########################################################################
def main():
    basic = Basics()
    DEVISE=basic.sql.get_symbols()[0]

    ################################################
    #    Initialisation
    ################################################
    basic.initialise(DEVISE)
    while True:
        time.sleep(5)
        basic.verification_2_ordres(DEVISE)

        basic.verification_niveau_VS_timer(DEVISE)





if __name__ == '__main__':
     main()

