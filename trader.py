import time

from bininterface import binAcces
from sqlInterface import sqlAcces
from KPI import Kpi
from telegramInterface import teleAcces
from sheetInterface import sheetAcces


class Basics():

    def __init__(self):
        self.sql = sqlAcces()
        self.bin = binAcces()
        self.kpi = Kpi()
        self.tele = teleAcces()
        self.sheet = sheetAcces()

    def plus_proche(self,symbol,ID_client):
        ecart_bet_dic = self.sql.get_ecart_bet_from_symbol(symbol)
        prix_tmp = self.bin.get_price(symbol,ID_client)
        prix = prix_tmp["price"]
        delta = abs(float(ecart_bet_dic[0][1])-float(prix))
        prix_proche_ID=0
        keys = ecart_bet_dic.keys()
        for key in keys:
            if abs(float(prix)-float(ecart_bet_dic[key][0]))<delta:
                delta = abs(float(prix)-float(ecart_bet_dic[key][0]))
                prix_proche_ID = key
        return prix_proche_ID

    def initialise(self,symbol,ID_client):
        GO = False
        ordres_ouverts = self.sql.get_orders_status_symbol_filter(self.bin.client.ORDER_STATUS_NEW,symbol,ID_client)
        if len(ordres_ouverts) == 2:
            changement = self.bin.changement_status(symbol,ID_client)
            print("changement : "+ str(changement))
            if changement == []:
                GO = True
            else:
                self.bin.changement_update(changement,symbol,ID_client)
        print(symbol + "\tGO : "+str(GO))
        if GO == False:
            changement = self.bin.changement_status(symbol,ID_client)
            self.bin.changement_update(changement,symbol,ID_client)
            ordres_ouverts = self.sql.get_orders_status_symbol_filter(self.bin.client.ORDER_STATUS_NEW,symbol,ID_client)
            for ordre_ouvert in ordres_ouverts:
                self.bin.cancel_order(ordre_ouvert["ID"],ID_client)
            last_close = self.sql.get_last_filled(symbol,ID_client)
            if last_close != "":
                ID_ecart_last_close = last_close["ID_ecart"]
            else:
                ID_ecart_last_close = self.plus_proche(symbol,ID_client)
            print(ID_ecart_last_close)
            self.bin.new_vente(symbol,ID_ecart_last_close,ID_client)
            self.bin.new_achat(symbol,ID_ecart_last_close,ID_client)

    def verification_2_ordres_V2(self,symbol,ID_client):
        try:
            changement = self.bin.changement_status(symbol,ID_client)
            self.bin.changement_update(changement,symbol,ID_client)
            ordres_new = self.sql.get_orders_status_symbol_filter(self.bin.client.ORDER_STATUS_NEW,symbol,ID_client)
            ordres_partial = self.sql.get_orders_status_symbol_filter(self.bin.client.ORDER_STATUS_PARTIALLY_FILLED,symbol,ID_client)
            ordres_DB = ordres_partial + ordres_new

            if len(ordres_DB) ==1 :
                if len(ordres_new) == 1:
                    last_filled = self.sql.get_last_filled(symbol,ID_client)
                    self.sql.calcul_benefice(symbol,last_filled)
                    self.sql.add_bet_after_sell(symbol,last_filled,ID_client)
                    clients = self.sql.get_clients_infos()

                    self.tele.send_message("FILLED "+symbol+" :"+str(last_filled["sens"])+"\n"+str(last_filled["montant_execute"]),clients[ID_client]["tele"])
                    self.sql.new_log_debug("verification_2_ordres_V2","un ordre FILLED et un NEW : "+str(ordres_DB),symbol)
                    self.un_ordre_filled_autre_new(ordres_DB,symbol,ID_client)
                    self.sheet.update_all_info(symbol)
                    # un ordre ferme et un NEW
                elif len(ordres_partial) == 1:
                    self.tele.send_message("nouvel ordre avec un partial FILLED")
                    self.sql.new_log_debug("verification_2_ordres_V2","un ordre FILLED et un PARTIALY : "+str(ordres_DB),symbol)
                    self.un_ordre_filled_autre_partial(ordres_partial,symbol,ID_client)
                    # un ordre ferme et l autre partialy FILLED
            elif len(ordres_DB) == 0 :
                self.tele.send_message("deux ordres clos en meme temps")
                self.sql.new_log_debug("verification_2_ordres_V2","deux ordres FILLED : "+str(ordres_DB),symbol)
                self.deux_ordres_filled(symbol,ID_client)
                #Deux ordres ont ete fermes
            elif len(ordres_DB) > 2 :
                self.sql.new_log_error("verification_2_ordres_V2_trader","probleme de trade", symbol)
        except Exception as inst:
            self.sql.new_log_debug("Ordres V2",str(inst),symbol)
            return inst

    def un_ordre_filled_autre_new(self,ordres_ouvert,symbol,ID_client):
        for ordre_ouvert in ordres_ouvert:
            self.bin.cancel_order(ordre_ouvert["ID"],ID_client)
        last_filled_order = self.sql.get_last_filled(symbol,ID_client)
        self.sql.new_log_debug("Nouveaux ordres apres filled",str(last_filled_order),symbol)
        self.bin.new_achat(symbol,last_filled_order["ID_ecart"],ID_client)
        self.bin.new_vente(symbol,last_filled_order["ID_ecart"],ID_client)
        #self.kpi.reste_sur_limites(symbol,ID_client)

    def un_ordre_filled_autre_partial(self,ordres_partiel,symbol,ID_client):
        for ordre in ordres_partiel:
            self.bin.cancel_order(ordre["ID"],ID_client)
            sens = ordre["sens"]
            if sens == self.bin.client.SIDE_BUY:
                self.bin.new_market_order(symbol,ordre["montant_execute"],self.bin.client.SIDE_SELL,ID_client)
            if sens == self.bin.client.SIDE_SELL:
                self.bin.new_market_order(symbol,ordre["montant_execute"],self.bin.client.SIDE_BUY,ID_client)
        last_filled_order = self.sql.get_last_filled(symbol,ID_client)
        self.sql.new_log_debug("Nouveaux ordres apres filled",str(last_filled_order),symbol)

        self.bin.new_achat(symbol,last_filled_order["ID_ecart"],ID_client)
        self.bin.new_vente(symbol,last_filled_order["ID_ecart"],ID_client)
        #self.kpi.reste_sur_limites(symbol,ID_client)

    def deux_ordres_filled(self,symbol,ID_client):
        last_filled_order_buy = self.sql.get_last_filled_buy(symbol)
        last_filled_order_sell = self.sql.get_last_filled_sell(symbol)
        montant_interval = self.sql.get_montant_entre_ordres(symbol,
                                                             last_filled_order_buy["ID_ecart"],
                                                             last_filled_order_sell["ID_ecart"])
        bet_ecart = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,last_filled_order_buy["ID_ecart"]-1)
        self.bin.new_limite_order(symbol,
                                  bet_ecart[3]+montant_interval,
                                  bet_ecart[2],
                                  self.bin.client.SIDE_BUY,
                                  last_filled_order_buy["ID_ecart"]-1,
                                  0,
                                  ID_client)

        bet_ecart = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,last_filled_order_sell["ID_ecart"]+1)
        self.bin.new_limite_order(symbol,
                                  bet_ecart[3]+montant_interval,
                                  bet_ecart[2],
                                  self.bin.client.SIDE_SELL,
                                  last_filled_order_sell["ID_ecart"]+1,
                                  0,
                                  ID_client)

    def verification_niveau_VS_timer(self,symbol,ID_client):
        niveaux = self.sql.get_time_since_open(symbol,ID_client)
        keys = niveaux.keys()
        for key in keys:
            #Delais d attente de 30 min pour un ordre niveau 4
            if int(niveaux[key]["niveau"]) == 4 and niveaux[key]["time"].seconds > 1800:
                self.bin.baisser_niveau_ordre(key,ID_client)
            # Delas d attente de 1 heures pour un ordre de niveau 3
            if int(niveaux[key]["niveau"]) == 3 and niveaux[key]["time"].seconds > 3600:
                self.bin.baisser_niveau_ordre(key,ID_client)
            # Delas d attente de 2 heures pour un ordre de niveau 2
            if int(niveaux[key]["niveau"]) == 2 and niveaux[key]["time"].seconds > 7200:
                self.sql.baisser_niveau_ordre_SQL(key,1)

###########################################################################
#                                 MAIN                                    #
###########################################################################
def main():
    basic = Basics()
    DEVISES=basic.sql.get_symbols_actif()

    ################################################
    #    Initialisation
    ################################################
    basic.tele.send_message("Bonjour")
    #for DEVISE in DEVISES:
    #basic.initialise("EURUSDT_seb",3)
    #basic.initialise("PEPEEUR_3")
    #    time.sleep(3)
    while True:
        users_IDs=DEVISES.keys()
        for user_ID in users_IDs:
            for DEVISE in DEVISES[user_ID]:
                basic.verification_2_ordres_V2(DEVISE,user_ID)

                basic.verification_niveau_VS_timer(DEVISE,user_ID)
                time.sleep(4)








if __name__ == '__main__':
     main()
