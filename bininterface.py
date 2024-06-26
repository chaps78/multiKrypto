from binance.client import Client
import json
from datetime import datetime, timezone
import time

from sqlInterface import sqlAcces

class binAcces():
    def __init__(self):
        with open('bin_key.json') as json_file:
            config = json.load(json_file)
        self.client = Client(config["api"], config["secret"])
        self.sql = sqlAcces()

    def new_limite_order(self,symbol,montant,limite,sens,ID_ecart,flag_ajout,niveau=1):
        try:
            #breakpoint()
            response = self.client.create_order(symbol=symbol, 
                                            side=sens, 
                                            type=Client.ORDER_TYPE_LIMIT, 
                                            quantity='%.8f' % montant, 
                                            price='%.8f' % limite,
                                            timeInForce='GTC')
        except Exception as inst:
            #breakpoint()
            self.sql.new_log_error("new_limite_order_Binance",str(inst),symbol)
            return ""
        
        self.sql.new_order(response["orderId"],symbol,montant,limite,response["status"],datetime.now(timezone.utc),"",0,Client.ORDER_TYPE_LIMIT,sens,ID_ecart,flag_ajout,niveau)
        return response["orderId"]
    
    def get_ajout_for_achat_order(self,symbol,flag_ajout,ID_ecart):
        ajout = 0.0
        if flag_ajout == 1:
            ajout_dico = self.sql.get_ajout_entier_dic(symbol)
            keys = ajout_dico.keys()
            for key in keys:
                if key > ID_ecart:
                    ajout += ajout_dico[key]

        return ajout

    ###############################
    #donner l ID du dernier FILLED (clos)
    ###############################
    def new_achat(self,symbol,ID_ecart,flag_ajout=0):
        last_ordre = self.sql.get_last_filled(symbol)
        #breakpoint()
        if last_ordre != "":
            if last_ordre["sens"]== Client.SIDE_SELL:
                bet_ecart = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart-1)
                ajout = self.get_ajout_for_achat_order(symbol,flag_ajout,ID_ecart-1)
                self.sql.new_log_debug("ouverture Achat limite apres une vente",
                                    "montant: "
                                    +str(bet_ecart[3]+ajout)
                                    +"limite: "+str(bet_ecart[2]),
                                    symbol)
                self.new_limite_order(symbol,
                                    bet_ecart[3]+ajout,
                                    bet_ecart[2],
                                    Client.SIDE_BUY,
                                    ID_ecart-1,
                                    flag_ajout)
            else:
                if int(last_ordre["niveau"])==1:
                    bet_ecart = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart-1)
                    ajout = self.get_ajout_for_achat_order(symbol,flag_ajout,ID_ecart-1)
                    self.sql.new_log_debug("ouverture Achat limite apres niveau 1 vers 2",
                                    "montant: "
                                    +str(bet_ecart[3]+ajout)
                                    +"limite: "+str(bet_ecart[2]),
                                    symbol)
                    self.new_limite_order(symbol,
                                        bet_ecart[3]+ajout,
                                        bet_ecart[2],
                                        Client.SIDE_BUY,
                                        ID_ecart-1,
                                        flag_ajout,
                                        2)
                
                elif int(last_ordre["niveau"])==2:
                    bet_ecart_1 = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart-1)
                    bet_ecart_2 = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart-2)
                    ajout = self.get_ajout_for_achat_order(symbol,flag_ajout,ID_ecart-2)
                    self.sql.new_log_debug("ouverture Achat limite apres niveau 2 vers 3",
                                    "montant: "
                                    +str(bet_ecart_1[3]+bet_ecart_2[3]+ajout)
                                    +"limite: "+str(bet_ecart_2[2]),
                                    symbol)
                    self.new_limite_order(symbol,
                                        bet_ecart_1[3]+bet_ecart_2[3]+ajout,
                                        bet_ecart_2[2],
                                        Client.SIDE_BUY,
                                        ID_ecart-2,
                                        flag_ajout,
                                        3)
                else:
                    bet_ecart_1 = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart-1)
                    bet_ecart_2 = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart-2)
                    bet_ecart_3 = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart-3)
                    ajout = self.get_ajout_for_achat_order(symbol,flag_ajout,ID_ecart-2)
                    self.sql.new_log_debug("ouverture Achat limite apres niveau 3 vers 4",
                                    "montant: "
                                    +str(bet_ecart_1[3]+bet_ecart_2[3]+bet_ecart_3[3]+ajout)
                                    +"limite: "+str(bet_ecart_3[2]),
                                    symbol)
                    self.new_limite_order(symbol,
                                        bet_ecart_1[3]+bet_ecart_2[3]+bet_ecart_3[3]+ajout,
                                        bet_ecart_3[2],
                                        Client.SIDE_BUY,
                                        ID_ecart-3,
                                        flag_ajout,
                                        4)
        else:
            bet_ecart = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart-1)
            ajout = self.get_ajout_for_achat_order(symbol,flag_ajout,ID_ecart-1)
            self.sql.new_log_debug("ouverture Achat limite apres une vente",
                                "montant: "
                                +str(bet_ecart[3]+ajout)
                                +"limite: "+str(bet_ecart[2]),
                                symbol)
            self.new_limite_order(symbol,
                                bet_ecart[3]+ajout,
                                bet_ecart[2],
                                Client.SIDE_BUY,
                                ID_ecart-1,
                                flag_ajout)


    ###############################
    #donner l ID du dernier FILLED (clos)
    ###############################
    def new_vente(self,symbol,ID_ecart,flag_ajout=0):
        last_ordre = self.sql.get_last_filled(symbol)
        #breakpoint()
        if last_ordre != "":
            if last_ordre["sens"]== Client.SIDE_BUY:
                bet_ecart_limite = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart+1)
                bet_ecart_montant = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart)
                ajout = self.get_ajout_for_achat_order(symbol,flag_ajout,ID_ecart+1)
                self.sql.new_log_debug("ouverture Vente limite apres un achat",
                                    "montant: "
                                    +str(bet_ecart_montant[3]-ajout)
                                    +"limite: "+str(bet_ecart_limite[2]),
                                    symbol)
                self.new_limite_order(symbol,
                                    bet_ecart_montant[3]-ajout,
                                    bet_ecart_limite[2],
                                    Client.SIDE_SELL,
                                    ID_ecart+1,
                                    flag_ajout)
            else:
                if int(last_ordre["niveau"])==1:
                    bet_ecart_limite = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart+1)
                    bet_ecart_montant = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart)
                    ajout = self.get_ajout_for_achat_order(symbol,flag_ajout,ID_ecart+1)
                    self.sql.new_log_debug("ouverture Vente limite passage niv 1 vers 2",
                                    "montant: "
                                    +str(bet_ecart_montant[3]-ajout)
                                    +"limite: "+str(bet_ecart_limite[2]),
                                    symbol)
                    self.new_limite_order(symbol,
                                        bet_ecart_montant[3]-ajout,
                                        bet_ecart_limite[2],
                                        Client.SIDE_SELL,
                                        ID_ecart+1,
                                        flag_ajout,
                                        2)
                elif int(last_ordre["niveau"])==2:
                    bet_ecart_limite = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart+2)
                    bet_ecart_montant = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart)
                    bet_ecart_montant_2 = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart+1)
                    ajout = self.get_ajout_for_achat_order(symbol,flag_ajout,ID_ecart+2)
                    self.new_limite_order(symbol,
                                        bet_ecart_montant[3]+bet_ecart_montant_2[3]-ajout,
                                        bet_ecart_limite[2],
                                        Client.SIDE_SELL,
                                        ID_ecart+2,
                                        flag_ajout,
                                        3)
                else:
                    bet_ecart_limite = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart+3)
                    bet_ecart_montant = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart)
                    bet_ecart_montant_2 = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart+1)
                    bet_ecart_montant_3 = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart+2)
                    ajout = self.get_ajout_for_achat_order(symbol,flag_ajout,ID_ecart+2)
                    self.new_limite_order(symbol,
                                        bet_ecart_montant[3]+bet_ecart_montant_2[3]+bet_ecart_montant_3[3]-ajout,
                                        bet_ecart_limite[2],
                                        Client.SIDE_SELL,
                                        ID_ecart+3,
                                        flag_ajout,
                                        4)
        else:
            bet_ecart_limite = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart+1)
            bet_ecart_montant = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart)
            ajout = self.get_ajout_for_achat_order(symbol,flag_ajout,ID_ecart+1)
            self.sql.new_log_debug("ouverture Vente limite apres un achat",
                                "montant: "
                                +str(bet_ecart_montant[3])
                                +"limite: "+str(bet_ecart_limite[2]),
                                symbol)
            self.new_limite_order(symbol,
                                bet_ecart_montant[3],
                                bet_ecart_limite[2],
                                Client.SIDE_SELL,
                                ID_ecart+1,
                                flag_ajout)


    def new_market_order(self,symbol,montant,sens):
        try:
            response = self.client.create_order(symbol=symbol, 
                                        side=sens, 
                                        type=Client.ORDER_TYPE_MARKET, 
                                        quantity=montant)
        except Exception as inst:
            self.sql.new_log_error("new_market_order_Binance",str(inst),symbol)
            return ""
        
        self.sql.new_order(response["orderId"],symbol,montant,"",response["status"],datetime.now(timezone.utc),"",0,Client.ORDER_TYPE_MARKET,sens,0,0)
        return response["orderId"]
        

    def cancel_order(self,ID):
        try:
            symbol = self.sql.get_order_info_by_ID(ID)["symbol"]
            ordre = self.client.cancel_order(symbol=symbol,orderId=int(ID))
        except Exception as inst:
            self.sql.new_log_error("cancel_order_Binance",str(inst),symbol)
            return ""
        self.sql.update_order(ID,ordre["status"],datetime.now(timezone.utc),ordre["executedQty"])
        retour = [ordre["status"],ordre["executedQty"]]
        return retour
    
    #######################################
    #  Regarde les differences entre des ordres donnes et ce qu il y a sur binance
    #  Renvoi les differences
    #######################################
    def changement_status(self,symbol):
        try:
            ordres_new = self.sql.get_orders_status_symbol_filter(self.client.ORDER_STATUS_NEW,symbol)
            ordres_partial = self.sql.get_orders_status_symbol_filter(self.client.ORDER_STATUS_PARTIALLY_FILLED,symbol)
            ordres_DB = ordres_partial + ordres_new
            orders_Binance = self.client.get_all_orders(symbol=symbol)
            change = []
            for ob in orders_Binance:
                ordre = self.sql.get_order_info_by_ID(ob["orderId"])
#                if ordre == {}:
#                    self.sql.new_log_error("changement_status_Binance",
#                                           "ordre binance non present en DB : "+str(ob["orderId"]),
#                                           symbol)
                for odb in ordres_DB:
                    if ob["orderId"] == odb["ID"]:
                        if ob["status"] != odb["status"]:
                            change.append({"orderId":ob["orderId"],"status":ob["status"],"executedQty":ob["executedQty"]})
        except Exception as inst:
            self.sql.new_log_error("changement_status_Binance",str(inst),symbol)
            time.sleep(60)
            change = []
        return change
    
    ####################################
    #Met a jour la DB a partir d une liste en input
    ####################################
    def changement_update(self,liste_ordres,symbol):
        try:
            for ordre in liste_ordres:
                self.sql.update_order(ordre["orderId"],ordre["status"],datetime.now(timezone.utc),ordre["executedQty"])
        except Exception as inst:
            self.sql.new_log_error("changement_update_Binance",str(inst),symbol)
    
    #####################################
    # input liste des devises dont on souhaite avoir le solde
    #ex : ["EUR","DOGE","BTC"]
    #####################################
    def get_found(self,devises,symbol):
        try:
            info = self.client.get_account()
            retour = {}
            for el in info["balances"]:
                if el["asset"] in devises:
                    retour[el["asset"]]=float(el["free"])+float(el["locked"])
        except Exception as inst:
            self.sql.new_log_error("get_found_Binance",str(inst),symbol)
            retour = ["ERROR"]
        return retour
    
    
    def get_price(self,symbol):
        try:
            result = self.client.get_symbol_ticker(symbol=symbol)
        except Exception as inst:
            self.sql.new_log_error("get_price_Binance",str(inst),symbol)
            return "ERROR"
        return result
    
    def baisser_niveau_ordre(self,ID_ordre):
        ordre = self.sql.get_order_info_by_ID(ID_ordre)
        if ordre["sens"] == self.client.SIDE_BUY:
            self.baisse_niveau_achat(ordre)
        if ordre["sens"] == self.client.SIDE_SELL:
            self.baisse_niveau_vente(ordre)
    
    def baisse_niveau_achat(self,ordre):
        if ordre["niveau"] == 4:
            self.cancel_order(ordre["ID"])
            bet_ecart_1 = self.sql.get_ecart_bet_from_symbol_and_ID(ordre["symbol"],int(ordre["ID_ecart"])+1)
            bet_ecart_2 = self.sql.get_ecart_bet_from_symbol_and_ID(ordre["symbol"],int(ordre["ID_ecart"])+2)
            self.new_limite_order(ordre["symbol"],
                                  float(bet_ecart_1[3])+float(bet_ecart_2[3]),
                                  float(bet_ecart_1[2]),
                                  ordre["sens"],
                                  int(ordre["ID_ecart"])+1,
                                  ordre["flag_ajout"],
                                  3)
        elif ordre["niveau"] == 3:
            self.cancel_order(ordre["ID"])
            bet_ecart_1 = self.sql.get_ecart_bet_from_symbol_and_ID(ordre["symbol"],int(ordre["ID_ecart"])+1)
            self.new_limite_order(ordre["symbol"],
                                  float(bet_ecart_1[3]),
                                  float(bet_ecart_1[2]),
                                  ordre["sens"],
                                  int(ordre["ID_ecart"])+1,
                                  ordre["flag_ajout"],
                                  1)

    def baisse_niveau_vente(self,ordre):
        if ordre["niveau"] == 4:
            self.cancel_order(ordre["ID"])
            bet_ecart_limite = self.sql.get_ecart_bet_from_symbol_and_ID(ordre["symbol"],int(ordre["ID_ecart"])-1)
            bet_ecart_montant = self.sql.get_ecart_bet_from_symbol_and_ID(ordre["symbol"],int(ordre["ID_ecart"])-3)
            bet_ecart_montant_2 = self.sql.get_ecart_bet_from_symbol_and_ID(ordre["symbol"],int(ordre["ID_ecart"])-2)
            self.new_limite_order(ordre["symbol"],
                                      bet_ecart_montant[3]+bet_ecart_montant_2[3],
                                      bet_ecart_limite[2],
                                      ordre["sens"],
                                      int(ordre["ID_ecart"])-1,
                                      ordre["flag_ajout"],
                                      3)
        elif ordre["niveau"] == 3:
            self.cancel_order(ordre["ID"])
            bet_ecart_limite = self.sql.get_ecart_bet_from_symbol_and_ID(ordre["symbol"],int(ordre["ID_ecart"])-1)
            bet_ecart_montant = self.sql.get_ecart_bet_from_symbol_and_ID(ordre["symbol"],int(ordre["ID_ecart"])-2)
            self.new_limite_order(ordre["symbol"],
                                      bet_ecart_montant[3],
                                      bet_ecart_limite[2],
                                      ordre["sens"],
                                      int(ordre["ID_ecart"])-1,
                                      ordre["flag_ajout"],
                                      1)


def main():    
    bin = binAcces()

    #bin.new_limite_order("XRPEUR",40,0.3,"BUY")
    #bin.cancel_order("646164940")
    #exec = bin.new_limite_order("XRPEUR",19,0.3,"BUY")
    #print("exec : "+str(exec))
    #exec = bin.new_limite_order("XRPEUR",20,0.3,"BUY")
    #print("exec : "+str(exec))
    #exec = bin.new_limite_order("XRPEUR",21,0.3,"BUY")
    #print("exec : "+str(exec))
    #retour = bin.changement_status("XRPEUR")
    #print(retour)
    #bin.changement_update(retour)
    #found = bin.get_price("DOGEBTC")

    #print(found)
    


if __name__ == '__main__':
     main()