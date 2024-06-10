from bininterface import binAcces
from sqlInterface import sqlAcces


class Kpi():

    def __init__(self):
        self.bin = binAcces()
        self.sql = sqlAcces()

    def reste_sur_limites(self,symbol):
        last_filled = self.bin.sql.get_last_filled(symbol)
        devises=self.bin.sql.get_devises_from_symbol(symbol)
        founds = self.bin.get_found([devises["devise1"],devises["devise2"]],symbol)
        devise1 = founds[devises["devise1"]]
        devise2 = founds[devises["devise2"]]
        ecart_bet_dic = self.bin.sql.get_ecart_bet_from_symbol(symbol)
        ID_max = max(ecart_bet_dic.keys())
        ID_ecart_courant = last_filled["ID_ecart"]-1
        while ID_ecart_courant < ID_max:
            ID_ecart_courant+=1
            devise1 -= ecart_bet_dic[ID_ecart_courant][1]
        ID_ecart_courant = last_filled["ID_ecart"]
        while ID_ecart_courant > 0:
            ID_ecart_courant -= 1
            devise2 -= ecart_bet_dic[ID_ecart_courant][1]*ecart_bet_dic[ID_ecart_courant][0]
        ret=[devise1,devise2]
        self.bin.sql.set_KPI_restes(symbol,ret,last_filled["ID_ecart"])
        return ret

    def stat_mois(self,symbol,annee,mois):
        min=self.sql.min_buy(symbol,annee,mois)
        max=self.sql.max_sell(symbol,annee,mois)
        result={}
        while min<max:
            result_inter={}
            result_inter["BUY"]=self.sql.count_buy_ID_ecart(symbol,annee,mois,min)
            result_inter["SELL"]=self.sql.count_sell_ID_ecart(symbol,annee,mois,min)
            result[min]=result_inter
            min+=1
        keys = result.keys()
        for key in keys:
            print(str(key)+":BUY:"
                  +str(result[key]["BUY"][0])
                  +":"+str(result[key]["BUY"][1])
                  +":"+str(result[key]["BUY"][2])
                  +":SELL:"
                  +str(result[key]["SELL"][0])
                  +":"+str(result[key]["SELL"][1])
                  +":"+str(result[key]["SELL"][2]))





###########################################################################
#                                 MAIN                                    #
###########################################################################
def main():
    DEVISE="XRPEUR"
    kpi = Kpi()

    #current_reste = kpi.reste_sur_limites(DEVISE)
    #print(current_reste)
    #last_restes = kpi.bin.sql.get_last_reste(DEVISE)
    #print(last_restes)
    #kpi.calcul_ajout(DEVISE,last_restes)
    kpi.stat_mois("XRPEUR",2024,6)




if __name__ == '__main__':
     main()
