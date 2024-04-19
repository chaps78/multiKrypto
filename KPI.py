from bininterface import binAcces


class Kpi():

    def __init__(self):
        self.bin = binAcces()

    def reste_sur_limites(self,symbol):
        last_filled = self.bin.sql.get_last_filled(symbol)
        ID_ecart_last_filled = last_filled["ID_ecart"]
        devises=self.bin.sql.get_devises_from_symbol(symbol)
        founds = self.bin.get_found(devises)
        print(founds)
        devise1 = founds[devises[0]]
        devise2 = founds[devises[1]]
        print(founds)
        ecart_bet_dic = self.bin.sql.get_ecart_bet_from_symbol(symbol)
        ID_max = max(ecart_bet_dic.keys())
        ID_ecart_courant = last_filled["ID_ecart"]
        while ID_ecart_courant < ID_max:
            ID_ecart_courant+=1
            devise1 -= ecart_bet_dic[ID_ecart_courant][1]
            print(ecart_bet_dic[ID_ecart_courant])
            print(devise1)




###########################################################################
#                                 MAIN                                    #
###########################################################################
def main():
    DEVISE="DOGEBTC"
    kpi = Kpi()

    ################################################
    #    Initialisation
    ################################################
    kpi.reste_sur_limites(DEVISE)






if __name__ == '__main__':
     main()

