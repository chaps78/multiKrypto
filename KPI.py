from bininterface import binAcces
from sqlInterface import sqlAcces


class Kpi():

    def __init__(self):
        self.bin = binAcces()
        self.sql = sqlAcces()

    def reste_sur_limites(self,symbol):
        last_filled = self.bin.sql.get_last_filled(symbol)
        devises=self.bin.sql.get_devises_from_symbol(symbol)
        #founds = self.bin.get_found([devises["devise1"],devises["devise2"]],symbol)
        founds = self.bin.get_found(["XRP","EUR","BTC","DOGE","ETH","PEPE"],symbol)
        XRPEUR_Price = float(self.bin.get_price("XRPEUR")["price"])
        DOGEEUR_Price = float(self.bin.get_price("DOGEEUR")["price"])
        BTCEUR_Price = float(self.bin.get_price("BTCEUR")["price"])
        PEPEEUR_Price = float(self.bin.get_price("PEPEEUR")["price"])
        ETHEUR_Price = float(self.bin.get_price("ETHEUR")["price"])
        total = founds["EUR"] + founds["XRP"] * XRPEUR_Price
        total += founds["DOGE"] * DOGEEUR_Price + founds["BTC"] * BTCEUR_Price
        total += founds["ETH"] * ETHEUR_Price + founds["PEPE"] * PEPEEUR_Price
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
        self.bin.sql.set_KPI_restes(symbol
                                    ,ret
                                    ,last_filled["ID_ecart"]
                                    ,founds["EUR"]
                                    ,founds["XRP"]
                                    ,XRPEUR_Price
                                    ,founds["DOGE"]
                                    ,DOGEEUR_Price
                                    ,founds["BTC"]
                                    ,BTCEUR_Price
                                    ,total
                                    ,founds["ETH"]
                                    ,ETHEUR_Price
                                    ,founds["PEPE"]
                                    ,PEPEEUR_Price
                                    )
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

    print("\nXRPEUR:\n")
    kpi.stat_mois("XRPEUR",2024,6)
    print("\nDOGEEUR:\n")
    kpi.stat_mois("DOGEEUR",2024,6)
    print("\nDOGEBTC:\n")
    kpi.stat_mois("DOGEBTC",2024,6)
    #kpi.reste_sur_limites("XRPEUR")
    bin = binAcces()
    sql = sqlAcces()
    resultat = sql.get_gain_mois("XRPEUR",2024,8)
    print("XRPEUR: "+str(resultat))
    total = resultat
    resultat = sql.get_gain_mois("DOGEBTC",2024,8)
    print("DOGEBTC: "+str(resultat))
    BTCEUR_Price = float(bin.get_price("BTCEUR")["price"])
    print("DOGEBTC (EUR): "+str(resultat*BTCEUR_Price))
    total += resultat*60000
    resultat = sql.get_gain_mois("DOGEEUR",2024,8)
    print("DOGEEUR: "+str(resultat))
    total += resultat
    resultat = sql.get_gain_mois("XRPETH",2024,8)
    print("XRPETH: "+str(resultat))
    ETHEUR_Price = float(bin.get_price("ETHEUR")["price"])
    print("XRPETH (EUR): "+str(resultat*ETHEUR_Price))
    total += resultat*2400
    resultat = sql.get_gain_mois("PEPEEUR",2024,8)
    print("PEPEEUR: "+str(resultat))
    total += resultat
    print("total: "+str(total))


if __name__ == '__main__':
     main()
