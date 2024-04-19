import sqlite3
from datetime import datetime, timezone


class sqlAcces():
    def __init__(self):
        self.con = sqlite3.connect("DB.db")
        self.cur = self.con.cursor()


    def new_order(self,ID,symbol,montant,limite,status,date_debut,date_fin,montant_exec,type,sens,ID_ecart,niveau=1):
        try:
            self.cur.execute("INSERT INTO Ordres VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                             (ID,symbol,montant,limite,status,date_debut,date_fin,montant_exec,type,sens,ID_ecart,int(niveau)))
        except sqlite3.IntegrityError as inst:
            self.new_log("new_order_SQL",str(inst))
            return inst
        retour = self.con.commit()
        return retour


    def delete_order(self,ID):
        try:
            self.cur.execute("DELETE FROM Ordres WHERE ID="+str(ID))
        except sqlite3.IntegrityError as inst:
            self.new_log("delete_order_SQL",str(inst))
            return inst
        retour = self.con.commit()
        return retour


    def update_order(self,ID,status,date_fin="",montant_exec="0"):
        try:
            self.cur.execute("UPDATE Ordres SET status=?,date_fin=?,montant_execute=? WHERE ID=?",
                             (status,date_fin,montant_exec,str(ID)))
        except sqlite3.IntegrityError as inst:
            self.new_log("update_order_SQL",str(inst))
            return inst
        retour = self.con.commit()
        return retour


    def get_orders_status_symbol_filter(self,status,symbol):
        try:
            res = self.cur.execute("SELECT * FROM Ordres WHERE status=? AND symbol=?",(str(status),str(symbol)))

        except sqlite3.IntegrityError as inst:
            self.new_log("get_orders_status_filter_SQL",str(inst))
            return inst
        self.con.commit()
        ordres = []
        for ordre in res.fetchall():
            ordres.append(self.convert_fetch_to_dico(ordre))
        return ordres
    

    def get_time_since_open(self,symbol):
        ordres_ouverts = self.get_orders_status_symbol_filter("NEW",symbol)
        retour = {}
        for ordre_ouvert in ordres_ouverts:
            retour[ordre_ouvert["ID"]] = {"time":((datetime.now(timezone.utc)-datetime.fromisoformat(ordre_ouvert["date_debut"]))),
                                          "niveau":ordre_ouvert["niveau"]}
        return retour
            
    

    def get_order_info_by_ID(self,ID):
        try:
            res = self.cur.execute("SELECT * FROM Ordres WHERE ID='"+str(ID)+"'")
        except sqlite3.IntegrityError as inst:
            self.new_log("get_order_info_by_ID_SQL",str(inst))
            return inst
        self.con.commit()
        ordre_sql = res.fetchall()
        ordre_format = self.convert_fetch_to_dico(ordre_sql[0])
        return ordre_format
    

    def new_log(self,emplacement,message):
        try:
            self.cur.execute("INSERT INTO Log VALUES(?,?,?)",(datetime.now(timezone.utc),str(emplacement),str(message)))
        except Exception as inst:
            self.new_log("new_log_SQL",str(inst))
        self.con.commit()


    def set_ecart_bet(self,fichier_CSV):
        file = open(fichier_CSV, "r")
        lines = file.readlines()
        file.close()
        try:
            for ligne in lines:
                tab_ligne = ligne.split(",")
                self.cur.execute("INSERT INTO ecart_bet VALUES(?,?,?,?)",
                                 (tab_ligne[0],tab_ligne[1],float(tab_ligne[2]),tab_ligne[3]))
        except Exception as inst:
            self.new_log("set_ecart_bet_SQL",str(inst))
        self.con.commit()


    def get_ecart_bet_from_symbol(self,symbol):
        try:
            res = self.cur.execute("SELECT * FROM ecart_bet WHERE symbol='"+str(symbol)+"'")
        except sqlite3.IntegrityError as inst:
            self.new_log("get_ecart_bet_from_symbol_SQL",str(inst))
            return inst
        self.con.commit()
        ecarts_SQL = res.fetchall()
        ecart_dico = {}
        for ecart_SQL in ecarts_SQL:
            ecart_dico[int(ecart_SQL[0])]=[ecart_SQL[2],ecart_SQL[3]]
        return ecart_dico
    
    def get_ecart_bet_from_symbol_and_ID(self,symbol,ID):
        try:
            res = self.cur.execute("SELECT * FROM ecart_bet WHERE ID='"+str(ID)+"' AND symbol='"+str(symbol)+"'")
        except sqlite3.IntegrityError as inst:
            self.new_log("get_ecart_bet_from_symbol_and_ID_SQL",str(inst))
            return inst
        self.con.commit()
        ###############
        #Idealement renvoyer un dictionnaire au lieu du tableau
        ###############
        return res.fetchall()[0]
    
    def get_last_filled(self,symbol):
        try:
            res = self.cur.execute("SELECT *, MAX(date_fin) FROM Ordres WHERE status='FILLED' AND symbol='"+str(symbol)+"'")
        except sqlite3.IntegrityError as inst:
            self.new_log("get_last_filled_SQL",str(inst))
            return ""
        self.con.commit()
        ordres = res.fetchall()
        if ordres[0] == (None, None, None, None, None, None, None, None, None, None, None, None, None):
            return ""
        ordre = self.convert_fetch_to_dico(ordres[0])
        return ordre
    
    def convert_fetch_to_dico(self,ordre):
        ordre_dico = {"ID":ordre[0],
                      "symbol":ordre[1],
                      "montant":ordre[2],
                      "limite":ordre[3],
                      "status":ordre[4],
                      "date_debut":ordre[5],
                      "date_fin":ordre[6],
                      "montant_execute":ordre[7],
                      "type":ordre[8],
                      "sens":ordre[9],
                      "ID_ecart":ordre[10],
                      "niveau":ordre[11],
                 }
        return ordre_dico
    
    def get_symbols(self):
        try:
            res = self.cur.execute("SELECT * FROM Devises")

        except sqlite3.IntegrityError as inst:
            self.new_log("get_symbols_SQL",str(inst))
            return inst
        devises_SQL = res.fetchall()

        devises_ret=[]
        for devise_SQL in devises_SQL:
            devises_ret.append(devise_SQL[0])
        return devises_ret
    
    def get_devises_from_symbol(self,symbol):
        try:
            res = self.cur.execute("SELECT * FROM Devises WHERE symbol='"+str(symbol)+"'")

        except sqlite3.IntegrityError as inst:
            self.new_log("get_devises_from_symbol_SQL",str(inst))
            return inst
        devises = res.fetchall()[0]
        formated_devises = [devises[1],devises[2]]
        return(formated_devises)
        
        
    
def main():
    sql = sqlAcces()

    #sql.new_order(1,"XRPEUR",200,0.1,"FILLED",10,12,200)
    #sql.new_order(2,"XRPEUR",500,0.1,"FILLED",10,12,200)
    #sql.delete_order(1)
    #sql.delete_order(2)
    #Ordre = sql.get_order_info_by_ID("646164940")
    #sql.update_order(3,"PART","10/12/2017",50)
    #res = sql.get_orders_status_filter("FILLED")
    #print("toto")
    #print(res)
    #print("toto")
    #sql.new_log("la","pas bien")
    #sql.set_ecart_bet("DOGEBTC.csv")
    #retour = sql.get_ecart_bet_from_symbol("DOGEBTC")
    #print(retour)
    #last_close = sql.get_ecart_bet_from_symbol_and_ID("DOGEBTC",15)
    #print(last_close)
    devises = sql.get_symbols()
    sql.get_devises_from_symbol(devises[0])



if __name__ == '__main__':
     main()