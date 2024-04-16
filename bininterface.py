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

    def new_limite_order(self,symbol,montant,limite,sens):
        try:
            response = self.client.create_order(symbol=symbol, 
                                            side=sens, 
                                            type=Client.ORDER_TYPE_LIMIT, 
                                            quantity=montant, 
                                            price=limite,
                                            timeInForce='GTC')
        except Exception as inst:
            self.sql.new_log("new_limite_order_Binance",str(inst))
            return ""
        
        self.sql.new_order(response["orderId"],symbol,montant,limite,response["status"],datetime.now(timezone.utc),"",0,Client.ORDER_TYPE_LIMIT,sens)
        return response["orderId"]
    
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
        

    def close_order(self,ID):
        try:
            symbol = self.sql.get_order_info_by_ID(ID)[0][1]
            ordre = self.client.cancel_order(symbol=symbol,orderId=int(ID))
        except Exception as inst:
            self.sql.new_log("close_order_Binance",str(inst))
            return ""
        self.sql.update_order(ID,ordre["status"],datetime.now(timezone.utc),ordre["executedQty"])
        retour = [ordre["status"],ordre["executedQty"]]
        return retour
    
    def changement_status(self,symbol):
        try:
            ordres_DB = self.sql.get_orders_status_filter(self.client.ORDER_STATUS_NEW)

            orders_Binance = self.client.get_all_orders(symbol=symbol)
            change = []
            for ob in orders_Binance:
                for odb in ordres_DB:
                    if ob["orderId"] == odb[0]:
                        if ob["status"] != odb[4]:
                            change.append({"orderId":ob["orderId"],"status":ob["status"],"executedQty":ob["executedQty"]})
        except Exception as inst:
            self.sql.new_log("changement_status_Binance",str(inst))
        return change
    
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
    ##############    TODO   ####################
    def get_price(self,symbol):
        result = self.client..ticker_price("XRPEUR")
        return result

    
bin = binAcces()

#bin.new_limite_order("XRPEUR",40,0.3,"BUY")
#bin.close_order("646164940")
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
found = bin.get_price("DOGEBTC")

print(found)
