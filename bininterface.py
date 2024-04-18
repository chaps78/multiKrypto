from binance.client import Client
import json
from datetime import datetime, timezone

from sqlInterface import sqlAcces

class binAcces():
    def __init__(self):
        with open('bin_key.json') as json_file:
            config = json.load(json_file)
        self.client = Client(config["api"], config["secret"])
        self.sql = sqlAcces()

    def new_limite_order(self,symbol,montant,limite,sens,ID_ecart,niveau=1):
        try:
            response = self.client.create_order(symbol=symbol, 
                                            side=sens, 
                                            type=Client.ORDER_TYPE_LIMIT, 
                                            quantity=montant, 
                                            price='%.8f' % limite,
                                            timeInForce='GTC')
        except Exception as inst:
            self.sql.new_log("new_limite_order_Binance",str(inst))
            return ""
        
        self.sql.new_order(response["orderId"],symbol,montant,limite,response["status"],datetime.now(timezone.utc),"",0,Client.ORDER_TYPE_LIMIT,sens,ID_ecart,niveau)
        return response["orderId"]
    
    ###############################
    #donner l ID du dernier FILLED (clos)
    ###############################
    def new_achat(self,symbol,ID_ecart):
        last_ordre = self.sql.get_last_filled(symbol)
        if last_ordre["sens"]== Client.SIDE_SELL:
            bet_ecart = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart-1)
            self.new_limite_order(symbol,
                                  bet_ecart[3],
                                  bet_ecart[2],
                                  Client.SIDE_BUY,
                                  ID_ecart-1)
        else:
            if int(last_ordre["niveau"])==1:
                bet_ecart = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart-1)
                self.new_limite_order(symbol,
                                      bet_ecart[3],
                                      bet_ecart[2],
                                      Client.SIDE_BUY,
                                      ID_ecart-1,
                                      2)
            
            if int(last_ordre["niveau"])==2:
                bet_ecart_1 = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart-1)
                bet_ecart_2 = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart-2)
                self.new_limite_order(symbol,
                                      bet_ecart_1[3]+bet_ecart_2[3],
                                      bet_ecart_2[2],
                                      Client.SIDE_BUY,
                                      ID_ecart-2,
                                      3)
            else:
                bet_ecart_1 = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart-1)
                bet_ecart_2 = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart-2)
                bet_ecart_3 = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart-3)
                self.new_limite_order(symbol,
                                      bet_ecart_1[3]+bet_ecart_2[3]+bet_ecart_3[3],
                                      bet_ecart_3[2],
                                      Client.SIDE_BUY,
                                      ID_ecart-3,
                                      4)




    ###############################
    #donner l ID du dernier FILLED (clos)
    ###############################
    def new_vente(self,symbol,ID_ecart):
        last_ordre = self.sql.get_last_filled(symbol)
        if last_ordre["sens"]== Client.SIDE_BUY:
            bet_ecart_limite = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart+1)
            bet_ecart_montant = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart)
            self.new_limite_order(symbol,
                                  bet_ecart_montant[3],
                                  bet_ecart_limite[2],
                                  Client.SIDE_SELL,
                                  ID_ecart+1)
        else:
            if int(last_ordre["niveau"])==1:
                bet_ecart_limite = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart+1)
                bet_ecart_montant = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart)
                self.new_limite_order(symbol,
                                      bet_ecart_montant[3],
                                      bet_ecart_limite[2],
                                      Client.
                                      SIDE_SELL,
                                      ID_ecart+1,
                                      2)
            if int(last_ordre["niveau"])==2:
                bet_ecart_limite = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart+2)
                bet_ecart_montant = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart)
                bet_ecart_montant_2 = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart+1)
                self.new_limite_order(symbol,
                                      bet_ecart_montant[3]+bet_ecart_montant_2[3],
                                      bet_ecart_limite[2],
                                      Client.SIDE_SELL,
                                      ID_ecart+2,
                                      3)
            else:
                bet_ecart_limite = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart+3)
                bet_ecart_montant = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart)
                bet_ecart_montant_2 = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart+1)
                bet_ecart_montant_3 = self.sql.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart+2)
                self.new_limite_order(symbol,
                                      bet_ecart_montant[3]+bet_ecart_montant_2[3]+bet_ecart_montant_3[3],
                                      bet_ecart_limite[2],
                                      Client.SIDE_SELL,
                                      ID_ecart+3,
                                      4)


    def new_market_order(self,symbol,montant,sens):
        try:
            response = self.client.create_order(symbol=symbol, 
                                        side=sens, 
                                        type=Client.ORDER_TYPE_MARKET, 
                                        quantity=montant)
        except Exception as inst:
            self.sql.new_log("new_market_order_Binance",str(inst))
            return ""
        
        self.sql.new_order(response["orderId"],symbol,montant,"",response["status"],datetime.now(timezone.utc),"",0,Client.ORDER_TYPE_MARKET,sens)
        return response["orderId"]
        

    def cancel_order(self,ID):
        try:
            symbol = self.sql.get_order_info_by_ID(ID)[0][1]
            ordre = self.client.cancel_order(symbol=symbol,orderId=int(ID))
        except Exception as inst:
            self.sql.new_log("cancel_order_Binance",str(inst))
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
            ordres_DB = self.sql.get_orders_status_symbol_filter(self.client.ORDER_STATUS_NEW,symbol)
            orders_Binance = self.client.get_all_orders(symbol=symbol)
            change = []
            for ob in orders_Binance:
                for odb in ordres_DB:
                    if ob["orderId"] == odb["ID"]:
                        if ob["status"] != odb["status"]:
                            change.append({"orderId":ob["orderId"],"status":ob["status"],"executedQty":ob["executedQty"]})
        except Exception as inst:
            self.sql.new_log("changement_status_Binance",str(inst))
        return change
    
    ####################################
    #Met a jour la DB a partir d une liste en input
    ####################################
    def changement_update(self,liste_ordres):
        try:
            for ordre in liste_ordres:
                self.sql.update_order(ordre["orderId"],ordre["status"],datetime.now(timezone.utc),ordre["executedQty"])
        except Exception as inst:
            self.sql.new_log("changement_update_Binance",str(inst))
    
    #####################################
    # input liste des devises dont on souhaite avoir le solde
    #ex : ["EUR","DOGE","BTC"]
    #####################################
    def get_found(self,devises):
        try:
            info = self.client.get_account()
            retour = {}
            for el in info["balances"]:
                if el["asset"] in devises:
                    retour[el["asset"]]=float(el["free"])+float(el["locked"])
        except Exception as inst:
            self.sql.new_log("get_found_Binance",str(inst))
            retour = ["ERROR"]
        return retour
    
    
    def get_price(self,symbol):
        try:
            result = self.client.get_symbol_ticker(symbol=symbol)
        except Exception as inst:
            self.sql.new_log("get_price_Binance",str(inst))
            return "ERROR"
        return result

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
    #breakpoint()
    #retour = bin.changement_status("XRPEUR")
    #print(retour)
    #bin.changement_update(retour)
    #found = bin.get_price("DOGEBTC")

    #print(found)


if __name__ == '__main__':
     main()