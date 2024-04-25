import sqlite3
from datetime import datetime, timezone

from telegramInterface import teleAcces


class sqlAcces():
    def __init__(self):
        self.con = sqlite3.connect("DB.db")
        self.cur = self.con.cursor()
        self.tele = teleAcces()


    def new_order(self,ID,symbol,montant,limite,status,date_debut,date_fin,montant_exec,type,sens,ID_ecart,flag_ajout,niveau=1):
        try:
            self.cur.execute("INSERT INTO Ordres VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                             (ID,symbol,montant,limite,status,date_debut,date_fin,montant_exec,type,sens,ID_ecart,int(niveau),int(flag_ajout)))
        except sqlite3.IntegrityError as inst:
            self.new_log_error("new_order_SQL",str(inst),symbol)
            return inst
        retour = self.con.commit()
        return retour


    def delete_order(self,ID,symbol):
        try:
            self.cur.execute("DELETE FROM Ordres WHERE ID="+str(ID))
        except sqlite3.IntegrityError as inst:
            self.new_log_error("delete_order_SQL",str(inst),symbol)
            return inst
        retour = self.con.commit()
        return retour


    def update_order(self,ID,status,date_fin="",montant_exec="0"):
        try:
            self.cur.execute("UPDATE Ordres SET status=?,date_fin=?,montant_execute=? WHERE ID=?",
                             (status,date_fin,montant_exec,str(ID)))
        except sqlite3.IntegrityError as inst:
            ordre = self.get_order_info_by_ID(ID)
            self.new_log_error("update_order_SQL",str(inst),ordre["symbol"])
            return inst
        retour = self.con.commit()
        return retour


    def get_orders_status_symbol_filter(self,status,symbol):
        try:
            res = self.cur.execute("SELECT * FROM Ordres WHERE status=? AND symbol=?",(str(status),str(symbol)))

        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_orders_status_filter_SQL",str(inst),symbol)
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
            self.con.commit()
            ordre_sql = res.fetchall()
            if ordre_sql != []:
                ordre_format = self.convert_fetch_to_dico(ordre_sql[0])
            else:
                return {}
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_order_info_by_ID_SQL",str(inst),ordre_format["symbol"])
            return inst
        return ordre_format
    

    def new_log_error(self,emplacement,message,symbol):
        try:
            self.cur.execute("INSERT INTO Log VALUES(?,?,?,?,?)",
                             (datetime.now(timezone.utc),str(emplacement),str(message),"ERREUR",symbol))
            self.tele.send_message("log erreur : "+str(message))
        except Exception as inst:
            self.new_log_error("new_log_error_SQL",str(inst),symbol)
        self.con.commit()

    def new_log_debug(self,emplacement,message,symbol):
        res = self.cur.execute("SELECT debug_log FROM Config")
        self.con.commit()
        debug_activate = res.fetchall()[0]
        if debug_activate[0] == 1:
            try:
                self.cur.execute("INSERT INTO Log VALUES(?,?,?,?,?)",(datetime.now(timezone.utc),str(emplacement),str(message),"DEBUG",symbol))
            except Exception as inst:
                self.new_log_error("new_log_debug_SQL",str(inst),symbol)
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
            self.new_log_error("set_ecart_bet_SQL",str(inst),"NA")
        self.con.commit()


    def get_ecart_bet_from_symbol(self,symbol):
        try:
            res = self.cur.execute("SELECT * FROM ecart_bet WHERE symbol='"+str(symbol)+"'")
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_ecart_bet_from_symbol_SQL",str(inst),symbol)
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
            self.new_log_error("get_ecart_bet_from_symbol_and_ID_SQL",str(inst),symbol)
            return inst
        self.con.commit()
        ###############
        #Idealement renvoyer un dictionnaire au lieu du tableau
        ###############
        ret = res.fetchall()
        return ret[0]
    
    def get_last_filled(self,symbol):
        try:
            res = self.cur.execute("SELECT *, MAX(date_debut) FROM Ordres WHERE status='FILLED' AND symbol='"+str(symbol)+"'")
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_last_filled_SQL",str(inst),symbol)
            return ""
        self.con.commit()
        ordres = res.fetchall()
        if ordres[0] == (None, None, None, None, None, None, None, None, None, None, None, None, None, None):
            return ""
        ordre = self.convert_fetch_to_dico(ordres[0])
        return ordre
        
    def get_last_filled_buy(self,symbol):
        try:
            res = self.cur.execute("SELECT *, MAX(date_debut) FROM Ordres WHERE sens='BUY' AND status='FILLED' AND symbol='"+str(symbol)+"'")
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_last_filled_SQL",str(inst),symbol)
            return ""
        self.con.commit()
        ordres = res.fetchall()
        if ordres[0] == (None, None, None, None, None, None, None, None, None, None, None, None, None, None):
            return ""
        ordre = self.convert_fetch_to_dico(ordres[0])
        return ordre
    
    def get_last_filled_sell(self,symbol):
        try:
            res = self.cur.execute("SELECT *, MAX(date_debut) FROM Ordres WHERE sens='SELL' AND status='FILLED' AND symbol='"+str(symbol)+"'")
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_last_filled_SQL",str(inst),symbol)
            return ""
        self.con.commit()
        ordres = res.fetchall()
        if ordres[0] == (None, None, None, None, None, None, None, None, None, None, None, None, None, None):
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
                      "flag_ajout":ordre[12],
                 }
        return ordre_dico
    
    def get_symbols(self):
        try:
            res = self.cur.execute("SELECT * FROM Devises")

        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_symbols_SQL",str(inst),"GET_SYMBOL")
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
            self.new_log_error("get_devises_from_symbol_SQL",str(inst),symbol)
            return inst
        devises = res.fetchall()[0]
        formated_devises = [devises[1],devises[2]]
        formated_devises = {"devise1":devises[1],
                            "devise2":devises[2],
                            "down":devises[3],
                            "local":devises[4],
                            "up":devises[5]}
        return(formated_devises)
    
    def set_KPI_restes(self,symbol,restes,last_ID):
        try:
            self.cur.execute("INSERT INTO reste VALUES(?,?,?,?,?)",
                                 (datetime.now(timezone.utc),symbol,restes[0],restes[1],int(last_ID)))
        except sqlite3.IntegrityError as inst:
            self.new_log_error("set_KPI_restes_SQL",str(inst),symbol)
            return inst
        ret = self.con.commit()
        return ret
    
    def get_last_reste(self,symbol):
        try:
            res = self.cur.execute("SELECT max(date),symbol,devise1,devise2,last_ID FROM reste WHERE symbol='"+symbol+"'")
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_last_reste_SQL",str(inst),symbol)
            return inst
        self.con.commit()
        reste = res.fetchall()[0]
        reste_dic = {"devise1":reste[2],"devise2":reste[3]}
        return reste_dic
    
    def get_ajout_reel_by_ID(self,symbol,ID_ecart):
        try:

            res = self.cur.execute("SELECT * FROM ajout WHERE ID_ecart="+str(ID_ecart)+" AND symbol='"+symbol+"'",)
        except Exception as inst:
            self.new_log_error("set_ajout_tab_SQL",str(inst),symbol)
        self.con.commit()
        reste = res.fetchall()
        return reste[0][2]
    
    def set_ajout_tab(self,symbol,ajout_dic):
        try:
            keys = ajout_dic.keys()
            for ID_ecart in keys:
                valeur_init = self.get_ajout_reel_by_ID(symbol,ID_ecart)
                valeur_to_update = valeur_init + ajout_dic[ID_ecart]
                self.cur.execute("UPDATE ajout SET ajout="+str(valeur_to_update)+" WHERE ID_ecart="+str(ID_ecart)+" AND symbol='"+symbol+"'")
                self.con.commit()
        except Exception as inst:
            self.new_log_error("set_ajout_tab_SQL",str(inst),symbol)

    def get_ajout_flag(self,symbol):
        try:
            res = self.cur.execute("SELECT * FROM ajout WHERE symbol='"+symbol+"'")
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_ajout_flag_SQL",str(inst),symbol)
            return inst
        self.con.commit()
        restes = res.fetchall()
        for reste in restes:
            if reste[2]>1:
                return 1
        return 0
 
        
    def get_ajout_entier_dic(self,symbol):
        try:
            res = self.cur.execute("SELECT * FROM ajout WHERE symbol='"+symbol+"'")
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_ajout_entier_dic_SQL",str(inst),symbol)
            return inst
        self.con.commit()
        reste = res.fetchall()
        ajout_dico = {}
        for ajout_sql in reste:
            if ajout_sql[2]>1:
                ajout_dico[ajout_sql[0]]=int(ajout_sql[2])
        return ajout_dico
    
    def add_ajout_to_ecart(self,symbol):
        ajout = self.get_ajout_entier_dic(symbol)
        keys = ajout.keys()
        for key in keys:
            current_bet = self.get_ecart_bet_from_symbol_and_ID(symbol,key)[3]
            try:
                self.cur.execute("UPDATE ecart_bet SET bet="
                                 +str(float(ajout[key]+current_bet))
                                 +" WHERE ID="
                                 +str(key)
                                 +" AND symbol='"+symbol+"'")
            except sqlite3.IntegrityError as inst:
                self.new_log_error("add_ajout_to_ecart_SQL_1",str(inst),symbol)
                return inst
            self.con.commit()
        try:
            for key in keys:
                valeur_courante = self.get_ajout_reel_by_ID(symbol,key)
                valeur_to_set = valeur_courante - ajout[key]
                self.cur.execute("UPDATE ajout SET ajout="+str(valeur_to_set)+" WHERE ID_ecart="+str(key)+" AND symbol='"+symbol+"'")
                self.con.commit()
        except sqlite3.IntegrityError as inst:
            self.new_log_error("add_ajout_to_ecart_SQL_2",str(inst),symbol)
            return inst
        

    #Pour un double achat on recupere le montant entre les deux ordres
    def get_montant_entre_ordres(self,symbol,ID_bas,ID_haut):
        if ID_bas>ID_haut:
            tmp=ID_bas
            ID_bas=ID_haut
            ID_haut=tmp
        somme=0
        ID_bas +=1
        while ID_bas < ID_haut:
            somme += self.get_ecart_bet_from_symbol_and_ID(symbol,ID_bas)[3]
            ID_bas +=1
        return somme

    
def main():
    sql = sqlAcces()
    DEVISE='DOGEBTC'

    #sql.add_ajout_to_ecart(DEVISE)
    #print(sql.get_ajout_flag(DEVISE))
    #print(sql.get_ajout_entier_dic(DEVISE))
    #print(sql.get_ajout_reel_by_ID(DEVISE,30))
    #dic={4:0.7,5:0.7,6:0.7}
    #print(sql.set_ajout_tab(DEVISE,dic))
    #sql.add_ajout_to_ecart(DEVISE)
    #print(sql.get_montant_entre_ordres(DEVISE,9,6))
    #print(sql.new_log_debug("ici","message","XRPEUR"))
    #sql.set_ecart_bet("XRPEUR.csv")
    print(sql.get_last_filled("XRPEUR"))

if __name__ == '__main__':
     main()