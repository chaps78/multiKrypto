from bininterface import binAcces
from sqlInterface import sqlAcces
from datetime import datetime, timezone, timedelta
import sys


class Kpi():

    def __init__(self):
        self.bin = binAcces()
        self.sql = sqlAcces()

    def reste_sur_limites(self,symbol,ID_client):
        last_filled = self.bin.sql.get_last_filled(symbol)
        devises=self.bin.sql.get_devises_from_symbol(symbol)
        #founds = self.bin.get_found([devises["devise1"],devises["devise2"]],symbol)
        founds = self.bin.get_found(["XRP","EUR","BTC","DOGE","ETH","PEPE"],symbol,ID_client)
        XRPEUR_Price = float(self.bin.get_price("XRPEUR")["price"],ID_client)
        DOGEEUR_Price = float(self.bin.get_price("DOGEEUR")["price"],ID_client)
        BTCEUR_Price = float(self.bin.get_price("BTCEUR")["price"],ID_client)
        PEPEEUR_Price = float(self.bin.get_price("PEPEEUR")["price"],ID_client)
        ETHEUR_Price = float(self.bin.get_price("ETHEUR")["price"],ID_client)
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
            

    def gain_month_global(self,year,month,ID_client):
        print("\n\n#########################################################")
        print("#              KPI YEAR "+str(year) + " MONTH "+str(month)+ "\t                #")
        print("#########################################################")
        symbols = self.sql.get_symbols_client(ID_client)
        base_client = self.sql.get_clients_infos()[ID_client]["base"]
        #symbols.append("PEPEEUR")
        total=0
        for symbol in symbols:
            #print("#\t\t" + symbol + "\t\t#")
            resultat = self.sql.get_gain_mois(symbol,year,month)
            if resultat != None:
                devise_info = self.sql.get_devises_from_symbol(symbol,ID_client)
                if devise_info["devise2"] == base_client:
                    print("#\t" + symbol +" : \t\t## \t"+str(round(resultat,2))+" "+base_client+"  \t#")
                    total += resultat
                else:
                    #breakpoint()
                    Price = float(self.bin.get_price(devise_info["devise2"]+base_client,ID_client)["price"])
                    print("#\t"+symbol +" : "+ str(round(resultat,2))
                          + " " + devise_info["devise2"] 
                          + "\t## \t"+str(round(resultat*Price,2))+" "+base_client+"  \t#")
                    total+=resultat*Price
        print("#########################################################")
        print("#\t\t\tTOTAL : "+ str(round(total,2))+ "\t\t\t#")
        print("#########################################################")
        return total

    def set_dashboard_info(self,symbol):
        date = datetime.now(timezone.utc)
        ID_client = self.sql.get_ID_client_from_symbol(symbol)
        symbol_plited = symbol.split("_")[0]
        instant_price = float(self.bin.get_price(symbol_plited,ID_client)["price"])
        e_b = self.sql.get_ecart_bet_from_symbol(symbol)
        graph_capital = 0.0
        qtt_crypto = 0.0
        for el in e_b:
            if e_b[el][0]<instant_price:
                graph_capital += e_b[el][0]*e_b[el][1]
            else:
                qtt_crypto += e_b[el][1]
        graph_capital += qtt_crypto*instant_price
        devise = self.sql.get_devises_from_symbol(symbol,ID_client)

        #Recuperation des gains de la veille
        veille = datetime.now() - timedelta(days=1)
        day_gain = self.sql.get_gain_jour(symbol,veille.year,veille.month,veille.day)
        epargne = devise["epargne"]
        factu = devise["factu"]
        tmp_up = devise["UP_tmp"]
        self.sql.set_dashboard(symbol,date,graph_capital,instant_price,day_gain,epargne,factu,tmp_up)



###########################################################################
#                                 MAIN                                    #
###########################################################################
def main():
    DEVISE="PEPEEUR_1"
    kpi = Kpi()
    sql = sqlAcces()
    bin = binAcces()
    mois = 9
    a=""
    if len(sys.argv) > 1:
        a = sys.argv[1]
    if a == "day":
        symbols = kpi.sql.get_symbols_actif()
        for ID_client in symbols:
            for symbol in symbols[ID_client]:
                kpi.set_dashboard_info(symbol)
    else:
        print("Select a client:")
        clients_liste = sql.get_clients_infos()
        for client in clients_liste:
            print(str(client)+" - "+ str(clients_liste[client]["name"]))
        ID_client = int(input("Enter your choice : "))
        print("1-Gain du mois\n2-Recap de la quantitée d'ordres")
        choice = input("Enter your choice [1-2]: ")
        if choice == '1':
            current_month = datetime.now().month
            current_year = datetime.now().year
            nbr_mois = int(input("combien de mois de rétro: "))
            somme = 0
            for i in range(nbr_mois):
                if current_month-i<0:
                    current_year -=1
                    current_month +=12
                somme += kpi.gain_month_global(current_year,current_month-(nbr_mois-i-1),ID_client)
            print("Total des "+str(nbr_mois)+" derniers mois: "+str(somme))

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
