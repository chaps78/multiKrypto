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
    
###########################################################################
#                                 MAIN                                    #
###########################################################################
def main():
    DEVISE="DOGEBTC"
    basic = Basics()

    ################################################
    #    Initialisation
    ################################################
    GO = False
    ordres_ouverts = basic.sql.get_orders_status_symbol_filter(basic.bin.client.ORDER_STATUS_NEW,DEVISE)
    if len(ordres_ouverts) == 2:
        changement = basic.bin.changement_status
        if changement == []:
            GO = True
    
    if GO == False:
        for ordre_ouver in ordres_ouverts:
            basic.bin.close_order(ordre_ouver[0])
    




if __name__ == '__main__':
     main()

