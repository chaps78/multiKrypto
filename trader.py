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
                self.bin.close_order(ordre_ouvert[0])
            last_close = self.sql.get_last_close(symbol)
            if last_close != "":
                ID_ecart_last_close = last_close[10]
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
    




if __name__ == '__main__':
     main()

