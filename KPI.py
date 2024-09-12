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
            

    def gain_month_global(self,year,month):
        print("\n\n#########################################################")
        print("#              KPI YEAR "+str(year) + " MONTH "+str(month)+ "\t                #")
        print("#########################################################")
        symbols = self.sql.get_symbols()
        #symbols.append("PEPEEUR")
        total=0
        for symbol in symbols:
            #print("#\t\t" + symbol + "\t\t#")
            resultat = self.sql.get_gain_mois(symbol,year,month)
            if resultat != None:
                devise_info = self.sql.get_devises_from_symbol(symbol)
                if devise_info["devise2"] == "EUR":
                    print("#\t" + symbol +" : \t\t## \t"+str(round(resultat,2))+" EUR  \t#")
                    total += resultat
                else:
                    Price = float(self.bin.get_price(devise_info["devise2"]+"EUR")["price"])
                    print("#\t"+symbol +" : "+ str(round(resultat,2))
                          + " " + devise_info["devise2"] 
                          + "\t## \t"+str(round(resultat*Price,2))+" EUR  \t#")
                    total+=resultat*Price
        print("#########################################################")
        print("#\t\t\tTOTAL : "+ str(round(total,2))+ "\t\t\t#")
        print("#########################################################")





###########################################################################
#                                 MAIN                                    #
###########################################################################
def main():
    DEVISE="XRPEUR"
    kpi = Kpi()
    sql = sqlAcces()
    mois = 9
    """
    print("\nXRPEUR:\n")
    kpi.stat_mois("XRPEUR",2024,mois)
    print("\nDOGEEUR:\n")
    kpi.stat_mois("DOGEEUR",2024,mois)
    print("\nPEPEEUR:\n")
    kpi.stat_mois("PEPEEUR",2024,mois)
    #kpi.reste_sur_limites("XRPEUR")
    #"""
    """
    bin = binAcces()
    sql = sqlAcces()
    resultat = sql.get_gain_mois("XRPEUR",2024,mois)
    print("XRPEUR: "+str(resultat))
    total = resultat
    resultat = sql.get_gain_mois("DOGEBTC",2024,mois)
    print("DOGEBTC: "+str(resultat))
    BTCEUR_Price = float(bin.get_price("BTCEUR")["price"])
    print("DOGEBTC (EUR): "+str(resultat*BTCEUR_Price))
    total += resultat*BTCEUR_Price
    resultat = sql.get_gain_mois("DOGEEUR",2024,mois)
    print("DOGEEUR: "+str(resultat))
    total += resultat
    resultat = sql.get_gain_mois("XRPETH",2024,mois)
    print("XRPETH: "+str(resultat))
    ETHEUR_Price = float(bin.get_price("ETHEUR")["price"])
    print("XRPETH (EUR): "+str(resultat*ETHEUR_Price))
    total += resultat*ETHEUR_Price
    resultat = sql.get_gain_mois("PEPEEUR",2024,mois)
    print("PEPEEUR: "+str(resultat))
    total += resultat
    print("total: "+str(total))
    #"""
    print("1-Gain du mois\n2-Recap de la quantitée d'ordres")
    choice = input("Enter your choice [1-2]: ")
    if choice == '1':
        kpi.gain_month_global(2024,6)
        kpi.gain_month_global(2024,7)
        kpi.gain_month_global(2024,8)
        kpi.gain_month_global(2024,mois)
    symbols = sql.get_symbols()
    if choice == '2':
        print("sur quelle paire?")
        for el in symbols:
            print(str(symbols.index(el))+"-"+el)
        choice2 = input("?")

        print("\n"+str(symbols[int(choice2)])+":\n")
        kpi.stat_mois(symbols[int(choice2)],2024,mois)


if __name__ == '__main__':
     main()
