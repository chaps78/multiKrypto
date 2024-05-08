import time

from bininterface import binAcces
from sqlInterface import sqlAcces
from KPI import Kpi
from telegramInterface import teleAcces


class Basics():

    def __init__(self):
        self.sql = sqlAcces()
        self.bin = binAcces()
        self.kpi = Kpi()
        self.tele = teleAcces()

    def plus_proche(self,symbol):
        ecart_bet_dic = self.sql.get_ecart_bet_from_symbol(symbol)
        prix_tmp = self.bin.get_price(symbol)
        prix = prix_tmp["price"]
        delta = abs(float(ecart_bet_dic[0][1])-float(prix))
        prix_proche_ID=0
        keys = ecart_bet_dic.keys()
        for key in keys:
            if abs(float(prix)-float(ecart_bet_dic[key][0]))<delta:
                delta = abs(float(prix)-float(ecart_bet_dic[key][0]))
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
                self.bin.changement_update(changement,symbol)
        print(symbol + "\tGO : "+str(GO))
        if GO == False:
            changement = self.bin.changement_status(symbol)
            self.bin.changement_update(changement,symbol)
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

    def verification_2_ordres_V2(self,symbol):
        changement = self.bin.changement_status(symbol)
        self.bin.changement_update(changement,symbol)
        ordres_new = self.sql.get_orders_status_symbol_filter(self.bin.client.ORDER_STATUS_NEW,symbol)
        ordres_partial = self.sql.get_orders_status_symbol_filter(self.bin.client.ORDER_STATUS_PARTIALLY_FILLED,symbol)
        ordres_DB = ordres_partial + ordres_new

        if len(ordres_DB) ==1 :
            if len(ordres_new) == 1:
                last_filled = self.sql.get_last_filled(symbol)
                self.sql.add_bet_after_sell(symbol,last_filled)
                self.tele.send_message("FILLED "+symbol+" :"+str(last_filled["sens"])+"\n"+str(last_filled["montant_execute"]))
                self.sql.new_log_debug("verification_2_ordres_V2","un ordre FILLED et un NEW : "+str(ordres_DB),symbol)
                self.un_ordre_filled_autre_new(ordres_DB,symbol)
                # un ordre ferme et un NEW
            elif len(ordres_partial) == 1:
                self.tele.send_message("nouvel ordre avec un partial FILLED")
                self.sql.new_log_debug("verification_2_ordres_V2","un ordre FILLED et un PARTIALY : "+str(ordres_DB),symbol)
                self.un_ordre_filled_autre_partial(ordres_partial,symbol)
                # un ordre ferme et l autre partialy FILLED
        elif len(ordres_DB) == 0 :
            self.tele.send_message("deux ordres clos en meme temps")
            self.sql.new_log_debug("verification_2_ordres_V2","deux ordres FILLED : "+str(ordres_DB),symbol)
            self.deux_ordres_filled(symbol)
            #Deux ordres ont ete fermes
        elif len(ordres_DB) > 2 :
            self.sql.new_log_error("verification_2_ordres_V2","Plus de deux ordres ouverts : "+ordres_DB, symbol)

    def un_ordre_filled_autre_new(self,ordres_ouvert,symbol):
        for ordre_ouvert in ordres_ouvert:
            self.bin.cancel_order(ordre_ouvert["ID"])
        last_filled_order = self.sql.get_last_filled(symbol)
        ############## pour les ajouts progressifs #######################
        if int(last_filled_order["flag_ajout"]) == 1:
            self.sql.new_log_debug("verification_2_ordres_flag_ordre_ON",str(ordres_ouvert),symbol)
            self.sql.add_ajout_to_ecart(symbol)
        ##################################################################
        self.sql.new_log_debug("Nouveaux ordres apres filled",str(last_filled_order),symbol)
        #breakpoint()
        self.bin.new_achat(symbol,last_filled_order["ID_ecart"])
        self.bin.new_vente(symbol,last_filled_order["ID_ecart"])
        self.kpi.reste_sur_limites(symbol)

    def un_ordre_filled_autre_partial(self,ordres_partiel,symbol):
        keys = ordres_partiel.keys()
        for key in keys:
            self.bin.cancel_order(ordres_partiel[key]["ID"])
            sens = ordres_partiel[key]["sens"]
            if sens == self.bin.client.SIDE_BUY:
                self.bin.new_market_order(symbol,ordres_partiel[key]["executedQty"],self.bin.client.SIDE_SELL)
            if sens == self.bin.client.SIDE_SELL:
                self.bin.new_market_order(symbol,ordres_partiel[key]["executedQty"],self.bin.client.SIDE_BUY)
            self.bin.new_market_order
        last_filled_order = self.sql.get_last_filled(symbol)
        ############## pour les ajouts progressifs #######################
        if int(last_filled_order["flag_ajout"]) == 1:
            self.sql.new_log_debug("verification_2_ordres_flag_ordre_ON",str(ordres_partiel),symbol)
            self.sql.add_ajout_to_ecart(symbol)
        ##################################################################
        self.sql.new_log_debug("Nouveaux ordres apres filled",str(last_filled_order),symbol)

        self.bin.new_achat(symbol,last_filled_order["ID_ecart"])
        self.bin.new_vente(symbol,last_filled_order["ID_ecart"])
        self.kpi.reste_sur_limites(symbol)

    def deux_ordres_filled(self,symbol):
        last_filled_order_buy = self.sql.get_last_filled_buy(symbol)
        last_filled_order_sell = self.sql.get_last_filled_sell(symbol)
        montant_interval = self.sql.get_montant_entre_ordres(symbol,
                                                             last_filled_order_buy["ID_ecart"],
                                                             last_filled_order_sell["ID_ecart"])
        bet_ecart = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,last_filled_order_buy["ID_ecart"]-1)
        #breakpoint()
        self.bin.new_limite_order(symbol,
                                  bet_ecart[3]+montant_interval,
                                  bet_ecart[2],
                                  self.bin.client.SIDE_BUY,
                                  last_filled_order_buy["ID_ecart"]-1,
                                  0)

        bet_ecart = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,last_filled_order_sell["ID_ecart"]+1)
        self.bin.new_limite_order(symbol,
                                  bet_ecart[3]+montant_interval,
                                  bet_ecart[2],
                                  self.bin.client.SIDE_SELL,
                                  last_filled_order_sell["ID_ecart"]+1,
                                  0)




    def verification_2_ordres(self,symbol):
        changement = self.bin.changement_status(symbol)
        nbr_filled = 0
        for el in changement:
            if el["status"] == self.bin.client.ORDER_STATUS_FILLED:
                nbr_filled +=1
            self.sql.new_log_debug("verification_2_ordres_changement_identifie",str(changement),symbol)
        if nbr_filled == 1:
            self.bin.changement_update(changement,symbol)
            for ordre in changement:
                if ordre["status"] == self.bin.client.ORDER_STATUS_PARTIALLY_FILLED:
                    self.sql.new_log_debug("verification_2_ordres_status_partial",str(ordre),symbol)
                    sens = self.sql.get_order_info_by_ID(ordre["ID"])["sens"]
                    if sens == self.bin.client.SIDE_BUY:
                        self.bin.new_market_order(symbol,ordre["executedQty"],self.bin.client.SIDE_SELL)
                    if sens == self.bin.client.SIDE_SELL:
                        self.bin.new_market_order(symbol,ordre["executedQty"],self.bin.client.SIDE_BUY)
            ordres_ouverts = self.sql.get_orders_status_symbol_filter(self.bin.client.ORDER_STATUS_NEW,symbol)
            for odb in ordres_ouverts:
                self.bin.cancel_order(odb["ID"])
            last_filled_order = self.sql.get_last_filled(symbol)
            if int(ordres_ouverts[0]["flag_ajout"]) == 1:
                self.sql.new_log_debug("verification_2_ordres_flag_ordre_ON",str(ordres_ouverts),symbol)
                self.sql.add_ajout_to_ecart(symbol)
            self.sql.new_log_debug("Nouveaux ordres apres filled",str(last_filled_order),symbol)
            self.bin.new_achat(symbol,last_filled_order["ID_ecart"])
            self.bin.new_vente(symbol,last_filled_order["ID_ecart"])
            self.kpi.reste_sur_limites(symbol)
        elif nbr_filled == 2:
            self.sql.new_log_debug("Double vente",str(changement),symbol)
            self.bin.changement_update(changement,symbol)
            last_filled_order = self.sql.get_last_filled(symbol)
            if int(ordres_ouverts[0]["flag_ajout"]) == 1:
                self.sql.add_ajout_to_ecart(symbol)

            ordre_1 = self.sql.get_order_info_by_ID(changement[0]["orderId"])
            ordre_2 = self.sql.get_order_info_by_ID(changement[1]["orderId"])
            if ordre_1["sens"] == self.bin.client.SIDE_BUY:
                ordre_buy=ordre_1
                ordre_sell=ordre_2
            else:
                ordre_buy=ordre_2
                ordre_sell=ordre_1

            montant_interval = self.sql.get_montant_entre_ordres(symbol,ordre_1["ID_ecart"],ordre_2["ID_ecart"])
            bet_ecart = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ordre_buy["ID_ecart"]-1)
            self.bin.new_limite_order(symbol,
                                  bet_ecart[3]+montant_interval,
                                  bet_ecart[2],
                                  self.bin.client.SIDE_BUY,
                                  ordre_buy["ID_ecart"]-1,
                                  0)

            bet_ecart = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ordre_sell["ID_ecart"]+1)
            self.bin.new_limite_order(symbol,
                                  bet_ecart[3]+montant_interval,
                                  bet_ecart[2],
                                  self.bin.client.SIDE_SELL,
                                  ordre_sell["ID_ecart"]+1,
                                  0)
            #self.bin.new_achat(symbol,last_filled_order["ID_ecart"])
            #self.bin.new_vente(symbol,last_filled_order["ID_ecart"])
#            self.kpi.reste_sur_limites(symbol)

        if changement == []:
            ajout_flag = self.sql.get_ajout_flag(symbol)
            last_filled_order = self.sql.get_last_filled(symbol)
            if ajout_flag == 1:
                ordres_ouverts = self.sql.get_orders_status_symbol_filter(self.bin.client.ORDER_STATUS_NEW,symbol)
                if ordres_ouverts[0]["flag_ajout"] == 0:
                    for odb in ordres_ouverts:
                        self.bin.cancel_order(odb["ID"])
                    self.bin.new_achat(symbol,last_filled_order["ID_ecart"],flag_ajout=1)
                    self.bin.new_vente(symbol,last_filled_order["ID_ecart"],flag_ajout=1)

    def verification_niveau_VS_timer(self,symbol):
        niveaux = self.sql.get_time_since_open(symbol)
        keys = niveaux.keys()
        for key in keys:
            #Delais d attente de 30 min pour un ordre niveau 4
            if int(niveaux[key]["niveau"]) == 4 and niveaux[key]["time"].seconds > 1800:
                self.tele.send_message("baisse de niveau 4 a 3")
                self.bin.baisser_niveau_ordre(key)
            # Delas d attente de 3 heures pour un ordre de niveau 3
            if int(niveaux[key]["niveau"]) == 3 and niveaux[key]["time"].seconds > 10800:
                self.tele.send_message("baisse de niveau 3 a 1")
                self.bin.baisser_niveau_ordre(key)

###########################################################################
#                                 MAIN                                    #
###########################################################################
def main():
    basic = Basics()
    DEVISES=basic.sql.get_symbols()

    ################################################
    #    Initialisation
    ################################################
    for DEVISE in DEVISES:
        basic.initialise(DEVISE)
        time.sleep(3)
    while True:
        for DEVISE in DEVISES:
            basic.verification_2_ordres_V2(DEVISE)

            basic.verification_niveau_VS_timer(DEVISE)
            time.sleep(4)








if __name__ == '__main__':
     main()
