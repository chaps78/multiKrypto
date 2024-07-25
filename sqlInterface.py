import sqlite3
from datetime import datetime, timezone

from telegramInterface import teleAcces


class sqlAcces():
    def __init__(self):
        self.con = sqlite3.connect("DB.db")
        self.cur = self.con.cursor()
        self.tele = teleAcces()


    def new_order(self,ID,symbol,montant,limite,status,date_debut,date_fin,montant_exec,type,sens,ID_ecart,flag_ajout,niveau=1,benefice=0.0):
        try:
            self.cur.execute("INSERT INTO Ordres VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                             (ID,symbol,montant,limite,status,date_debut,date_fin,montant_exec,type,sens,ID_ecart,int(niveau),int(flag_ajout),benefice))
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

    def set_ajout(self,fichier_CSV):
        file = open(fichier_CSV, "r")
        lines = file.readlines()
        file.close()
        try:
            for ligne in lines:
                tab_ligne = ligne.split(",")
                self.cur.execute("INSERT INTO ajout VALUES(?,?,?,?)",
                                 (tab_ligne[0],tab_ligne[1],float(tab_ligne[2]),datetime.now(timezone.utc)))
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
            res = self.cur.execute("SELECT *, MAX(date_debut) FROM Ordres WHERE status='FILLED' AND type='LIMIT' AND symbol='"+str(symbol)+"'")
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_last_filled_SQL",str(inst),symbol)
            return ""
        self.con.commit()
        ordres = res.fetchall()
        if ordres[0] == (None, None, None, None, None, None, None, None, None, None, None, None, None, None, None):
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
        if ordres[0] == (None, None, None, None, None, None, None, None, None, None, None, None, None, None, None):
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
        if ordres[0] == (None, None, None, None, None, None, None, None, None, None, None, None, None, None, None):
            return ""
        ordre = self.convert_fetch_to_dico(ordres[0])
        return ordre

    def update_bet_with_ID(self,symbol,ID,bet_value):
        try:

            self.cur.execute("UPDATE ecart_bet SET bet="
                             +str(bet_value)
                             +" WHERE ID="
                             +str(ID)
                             +" AND symbol='"+symbol+"'")
        except sqlite3.IntegrityError as inst:
            self.new_log_error("update_bet_with_ID_SQL",str(inst),symbol)
            return inst
        self.con.commit()


    def add_to_ajout(self,symbol,ID_ecart,valeur_to_add):
        try:
            curent_value = self.get_ajout_reel_by_ID(symbol,ID_ecart)
            valeur_to_update = curent_value + valeur_to_add
            self.cur.execute("UPDATE ajout SET ajout="+str(valeur_to_update)+" WHERE ID_ecart="+str(ID_ecart)+" AND symbol='"+symbol+"'")
        except sqlite3.IntegrityError as inst:
            self.new_log_error("add_to_ajout_SQL",str(inst),symbol)
            return inst
        self.con.commit()

    def add_to_ecart(self,symbol,ID_ecart,valeur_to_add):
        try:
            curent_value = self.get_ecart_bet_from_symbol_and_ID(symbol,ID_ecart)[3]
            breakpoint()
            valeur_to_update = curent_value + valeur_to_add
            self.cur.execute("UPDATE ecart_bet SET bet="+str(valeur_to_update)+" WHERE ID="+str(ID_ecart)+" AND symbol='"+symbol+"'")
        except sqlite3.IntegrityError as inst:
            self.new_log_error("add_to_ecart_SQL",str(inst),symbol)
            return inst
        self.con.commit()

    def calcul_delta_pour_ajout(self,symbol,last_filled,qtt_init):
        qtt = qtt_init
        benef = self.calcul_benef(symbol,last_filled)
        prix_reduce = (last_filled["limite"]-benef/qtt_init)*qtt_init/qtt
        if prix_reduce<0:
            return "NA"
        ecart_tab = self.get_ecart_bet_from_symbol(symbol)
        keys = ecart_tab.keys()
        ID_down = 0
        for key in keys:
            if ecart_tab[key][0]>prix_reduce:
                ID_down=key
                break
        self.add_to_ajout(symbol,int(ID_down),-qtt)
        self.update_bet_with_ID(symbol,ID_down,ecart_tab[ID_down][1]-qtt)
        return ID_down

    def calcul_benef(self,symbol,last_filled):
        FEE = 0.00075
        ecart_dessous = self.get_ecart_bet_from_symbol_and_ID(symbol,last_filled["ID_ecart"]-1)
        delta=float(last_filled["limite"])-float(ecart_dessous[2])
        benef = delta*last_filled["montant"]-2*FEE*last_filled["montant"]*last_filled["limite"]
        return benef
    
    def get_calcul_benef_with_ID(self,symbol,ID):
        FEE = 0.00075
        ec_b = self.get_ecart_bet_from_symbol(symbol)
        delta = ec_b[ID+1][0]-ec_b[ID][0]
        benef = delta*ec_b[ID][1]-2*FEE*ec_b[ID][1]*ec_b[ID][0]
        return benef
    
    def get_ID_to_UP(self,symbol,ID_courant):
        devises = self.get_devises_from_symbol(symbol)
        local = devises["local"]
        UP = devises["up"]
        ec_b = self.get_ecart_bet_from_symbol(symbol)
        for ID in range(len(ec_b)-ID_courant-1):
            benef = self.get_calcul_benef_with_ID(symbol,ID+ID_courant+1)
            if benef/ec_b[ID+ID_courant+1] < (local + UP):
                return ID+ID_courant+1



    
    def ajout_benef_paire_devise(self,symbol,qtt):
        epargne = self.get_devises_from_symbol(symbol)["epargne"]
        try:
            self.cur.execute("UPDATE Devises SET epargne=? WHERE symbol=?",
                             (qtt+epargne,symbol))
        except sqlite3.IntegrityError as inst:
            ordre = self.get_order_info_by_ID(ID)
            self.new_log_error("ajout_benef_paire_devise",str(inst),ordre["symbol"])
            return inst
        retour = self.con.commit()
        return retour
    
    def ajout_up_bet(self,symbol,ID,qtt):
        try:
            self.cur.execute("UPDATE ecart_bet SET UP=? WHERE symbol=? AND ID=?",
                             (qtt,symbol,ID))
        except sqlite3.IntegrityError as inst:
            ordre = self.get_order_info_by_ID(ID)
            self.new_log_error("ajout_up_bet",str(inst),ordre["symbol"])
            return inst
        retour = self.con.commit()
        return retour

    def add_bet_after_sell(self,symbol,last_filled):
        if last_filled["sens"] == "SELL":
            infos_devise = self.get_devises_from_symbol(symbol)
            ajout_qtt = infos_devise["local"]
            UP = infos_devise["up"]
            current_bet = self.get_ecart_bet_from_symbol_and_ID(symbol,int(last_filled["ID_ecart"])-1)[3]
            if int(last_filled["niveau"]) == 1 or int(last_filled["niveau"]) == 2:
                benef = self.calcul_benef(symbol,last_filled)
                benef_ratio = benef/last_filled["limite"]
                if benef_ratio < ajout_qtt:
                    self.update_bet_with_ID(symbol,int(last_filled["ID_ecart"])-1,int(current_bet)+ajout_qtt)
                    self.add_to_ajout(symbol,int(last_filled["ID_ecart"])-1,ajout_qtt)
                    self.calcul_delta_pour_ajout(symbol,last_filled,ajout_qtt)
                elif benef_ratio >= ajout_qtt and benef_ratio <= (ajout_qtt + UP):
                    self.update_bet_with_ID(symbol,int(last_filled["ID_ecart"])-1,int(current_bet)+ajout_qtt)
                    self.add_to_ajout(symbol,int(last_filled["ID_ecart"])-1,ajout_qtt)
                    self.ajout_benef_paire_devise(symbol,(benef_ratio-ajout_qtt)*last_filled["limite"])
                else:
                    self.update_bet_with_ID(symbol,int(last_filled["ID_ecart"])-1,int(current_bet)+ajout_qtt)
                    self.add_to_ajout(symbol,int(last_filled["ID_ecart"])-1,ajout_qtt)
                    self.ajout_benef_paire_devise(symbol,(benef_ratio-ajout_qtt-UP)*last_filled["limite"])
                    self.ajout_up_bet(symbol,int(last_filled["ID_ecart"])-1,UP)
            elif int(last_filled["niveau"]) == 3:
                self.update_bet_with_ID(symbol,int(last_filled["ID_ecart"])-1,int(current_bet)+2)
                self.add_to_ajout(symbol,int(last_filled["ID_ecart"])-1,2)
                bet_NV_3 = self.get_ecart_bet_from_symbol_and_ID(symbol,int(last_filled["ID_ecart"])-2)[3]
                self.update_bet_with_ID(symbol,int(last_filled["ID_ecart"])-2,int(bet_NV_3)+1)
                self.add_to_ajout(symbol,int(last_filled["ID_ecart"])-2,1)
            elif int(last_filled["niveau"]) == 4:
                self.update_bet_with_ID(symbol,int(last_filled["ID_ecart"])-1,int(current_bet)+2)
                self.add_to_ajout(symbol,int(last_filled["ID_ecart"])-1,2)
                bet_NV_3 = self.get_ecart_bet_from_symbol_and_ID(symbol,int(last_filled["ID_ecart"])-2)[3]
                self.update_bet_with_ID(symbol,int(last_filled["ID_ecart"])-2,int(bet_NV_3)+1)
                self.add_to_ajout(symbol,int(last_filled["ID_ecart"])-2,1)
                bet_NV_4 = self.get_ecart_bet_from_symbol_and_ID(symbol,int(last_filled["ID_ecart"])-3)[3]
                self.update_bet_with_ID(symbol,int(last_filled["ID_ecart"])-3,int(bet_NV_4)+1)
                self.add_to_ajout(symbol,int(last_filled["ID_ecart"])-3,1)

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
                      "benefice":ordre[13],
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
                            "up":devises[5],
                            "epargne":devises[6]
                            }
        return(formated_devises)

    def set_KPI_restes(self,symbol,restes,last_ID,EUR,XRP,XRP_Prix,DOGE,DOGE_Prix,BTC,BTC_Prix,Total):
        try:
            self.cur.execute("INSERT INTO reste VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                 (datetime.now(timezone.utc)
                                  ,symbol,restes[0]
                                  ,restes[1]
                                  ,int(last_ID)
                                  ,float(EUR)
                                  ,float(XRP)
                                  ,float(XRP_Prix)
                                  ,float(DOGE)
                                  ,float(DOGE_Prix)
                                  ,float(BTC)
                                  ,float(BTC_Prix)
                                  ,float(Total)
                                  ))
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
            self.new_log_error("get_ajout_reel_by_ID_SQL",str(inst),symbol)
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
    
    def get_ajout(self,symbol):
        try:
            res = self.cur.execute("SELECT * FROM ajout WHERE symbol='"+symbol+"'")
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_ajout_SQL",str(inst),symbol)
            return inst
        self.con.commit()
        ajout = res.fetchall()
        return ajout

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

    def get_epargne(self,symbol):
        try:
            res = self.cur.execute("SELECT * FROM Devises WHERE symbol='"+symbol+"'")
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_ajout_entier_dic_SQL",str(inst),symbol)
            return inst
        self.con.commit()
        epargne = res.fetchall()[0][6]
        return epargne
    
    def calcul_benefice(self,symbol,last_filled):
        FEE=0.00075
        ecart_bet = self.get_ecart_bet_from_symbol(symbol)
        ID_ecart_filled = last_filled["ID_ecart"]

        if last_filled["sens"]=="SELL":
            if last_filled["niveau"] == 1 or last_filled["niveau"] == 2:
                fee_courant=last_filled["montant"]*FEE*last_filled["limite"]
                benef=last_filled["montant"]*(ecart_bet[ID_ecart_filled+1][0]-ecart_bet[ID_ecart_filled][0])
                self.update_order_benef(last_filled["ID"],str(benef-fee_courant))
            elif last_filled["niveau"] == 3:
                fee_courant=last_filled["montant"]*FEE*last_filled["limite"]
                B1=ecart_bet[ID_ecart_filled-1][1]
                B2=ecart_bet[ID_ecart_filled-2][1]
                if int(B1+B2) != int(last_filled["montant"]):
                    self.tele.send_message("probleme de montant:")
                    self.tele.send_message("B1: "+str(B1))
                    self.tele.send_message("B2: "+str(B2))
                    self.tele.send_message("montant: "+str(last_filled["montant"]))
                Benef1 = B1*(ecart_bet[ID_ecart_filled+1][0]-ecart_bet[ID_ecart_filled][0])
                Benef2 = B2*(ecart_bet[ID_ecart_filled+1][0]-ecart_bet[ID_ecart_filled-1][0])
                self.update_order_benef(last_filled["ID"],str(Benef1+Benef2-fee_courant))
            elif last_filled["niveau"] == 4:
                fee_courant=last_filled["montant"]*FEE*last_filled["limite"]
                B1=ecart_bet[ID_ecart_filled-1][1]
                B2=ecart_bet[ID_ecart_filled-2][1]
                B3=ecart_bet[ID_ecart_filled-3][1]
                if int(B1+B2+B3) != int(last_filled["montant"]):
                    self.tele.send_message("probleme de montant:")
                    self.tele.send_message("B1: "+str(B1))
                    self.tele.send_message("B2: "+str(B2))
                    self.tele.send_message("B3: "+str(B3))
                    self.tele.send_message("montant: "+str(last_filled["montant"]))
                Benef1 = B1*(ecart_bet[ID_ecart_filled+1][0]-ecart_bet[ID_ecart_filled][0])
                Benef2 = B2*(ecart_bet[ID_ecart_filled+1][0]-ecart_bet[ID_ecart_filled-1][0])
                Benef3 = B3*(ecart_bet[ID_ecart_filled+1][0]-ecart_bet[ID_ecart_filled-2][0])
                self.update_order_benef(last_filled["ID"],str(Benef1+Benef2+Benef3-fee_courant))

        elif last_filled["sens"]=="BUY":
            if last_filled["niveau"] == 1 or last_filled["niveau"] == 2:
                fee_courant=last_filled["montant"]*FEE*last_filled["limite"]
                self.update_order_benef(last_filled["ID"],str(-fee_courant))

            elif last_filled["niveau"] == 3:
                fee_courant=last_filled["montant"]*FEE*last_filled["limite"]
                B1=ecart_bet[ID_ecart_filled][1]        #B1 utilise uniquement pour la verification
                B2=ecart_bet[ID_ecart_filled+1][1]
                if int(B1+B2) != int(last_filled["montant"]):
                    self.tele.send_message("probleme de montant:")
                    self.tele.send_message("B1: "+str(B1))
                    self.tele.send_message("B2: "+str(B2))
                    self.tele.send_message("montant: "+str(last_filled["montant"]))
                Benef2 = B2 * (ecart_bet[ID_ecart_filled+1][0]-ecart_bet[ID_ecart_filled][0])
                self.update_order_benef(last_filled["ID"],str(Benef2-fee_courant))
            
            elif last_filled["niveau"] == 4:
                fee_courant=last_filled["montant"]*FEE*last_filled["limite"]
                B1=ecart_bet[ID_ecart_filled][1]        #B1 utilise uniquement pour la verification
                B2=ecart_bet[ID_ecart_filled+1][1]
                B3=ecart_bet[ID_ecart_filled+2][1]
                if int(B1+B2+B3) != int(last_filled["montant"]):
                    self.tele.send_message("probleme de montant:")
                    self.tele.send_message("B1: "+str(B1))
                    self.tele.send_message("B2: "+str(B2))
                    self.tele.send_message("B3: "+str(B3))
                    self.tele.send_message("montant: "+str(last_filled["montant"]))
                Benef2 = B2 * (ecart_bet[ID_ecart_filled+1][0]-ecart_bet[ID_ecart_filled][0])
                Benef3 = B3 * (ecart_bet[ID_ecart_filled+2][0]-ecart_bet[ID_ecart_filled][0])
                self.update_order_benef(last_filled["ID"],str(Benef2+Benef3-fee_courant))
    
    def update_order_benef(self,ID,benef):
        benef_round= str(round(float(benef),8))
        try:
            self.cur.execute("UPDATE Ordres SET benefice=? WHERE ID=?",
                             (benef_round,str(ID)))
        except sqlite3.IntegrityError as inst:
            ordre = self.get_order_info_by_ID(ID)
            self.new_log_error("update_order_benef_SQL",str(inst),ordre["symbol"])
            return inst
        retour = self.con.commit()
        return retour
    
    def get_gain_jour(self,symbol,annee,mois,jour):
        date = str(annee)+"-"+"%02.0f"%mois+"-"+"%02.0f"%jour
        print(date)
        try:
            res = self.cur.execute("SELECT SUM(benefice) FROM Ordres WHERE symbol='"
                                   +str(symbol)+"' AND date_debut LIKE '"+date+"%'")
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_last_filled_SQL",str(inst),symbol)
            return ""
        self.con.commit()
        ordres = res.fetchall()
        return ordres[0][0]
    
    def get_gain_mois(self,symbol,annee,mois):
        date = str(annee)+"-"+"%02.0f"%mois
        try:
            res = self.cur.execute("SELECT SUM(benefice) FROM Ordres WHERE symbol='"
                                   +str(symbol)+"' AND date_debut LIKE '"+date+"%'")
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_last_filled_SQL",str(inst),symbol)
            return ""
        self.con.commit()
        ordres = res.fetchall()
        return ordres[0][0]
    
    def min_sell(self,symbol,annee,mois):
        date = str(annee)+"-"+"%02.0f"%mois
        try:
            res = self.cur.execute("SELECT MIN(ID_ecart) FROM Ordres WHERE sens='SELL' AND status='FILLED' AND symbol='"
                                   +str(symbol)+"' AND date_debut LIKE '"+date+"%'")
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_last_filled_SQL",str(inst),symbol)
            return ""
        self.con.commit()
        ordres = res.fetchall()
        min_sell = ordres[0][0]
        print("min sel: "+str(min_sell))
        return min_sell
    
    def max_sell(self,symbol,annee,mois):
        date = str(annee)+"-"+"%02.0f"%mois
        try:
            res = self.cur.execute("SELECT MAX(ID_ecart) FROM Ordres WHERE sens='SELL' AND status='FILLED' AND symbol='"
                                   +str(symbol)+"' AND date_debut LIKE '"+date+"%'")
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_last_filled_SQL",str(inst),symbol)
            return ""
        self.con.commit()
        ordres = res.fetchall()
        max_sell = ordres[0][0]
        return max_sell

    def min_buy(self,symbol,annee,mois):
        date = str(annee)+"-"+"%02.0f"%mois
        try:
            res = self.cur.execute("SELECT MIN(ID_ecart) FROM Ordres WHERE sens='BUY' AND status='FILLED' AND symbol='"
                                   +str(symbol)+"' AND date_debut LIKE '"+date+"%'")
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_last_filled_SQL",str(inst),symbol)
            return ""
        self.con.commit()
        ordres = res.fetchall()
        min_sell = ordres[0][0]
        return min_sell
    
    def max_buy(self,symbol,annee,mois):
        date = str(annee)+"-"+"%02.0f"%mois
        try:
            res = self.cur.execute("SELECT MAX(ID_ecart) FROM Ordres WHERE sens='BUY' AND status='FILLED' AND symbol='"
                                   +str(symbol)+"' AND date_debut LIKE '"+date+"%'")
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_last_filled_SQL",str(inst),symbol)
            return ""
        self.con.commit()
        ordres = res.fetchall()
        max_buy = ordres[0][0]
        return max_buy

    def count_sell_ID_ecart(self,symbol,annee,mois,ID_ecart):
        date = str(annee)+"-"+"%02.0f"%mois
        try:
            res = self.cur.execute("SELECT COUNT() FROM Ordres "
                                   +"WHERE sens='SELL' AND status='FILLED' AND symbol='"
                                   +str(symbol)+"' AND date_debut LIKE '"+date+"%' AND ID_ecart='"+str(ID_ecart)+"'"
                                   +" AND niveau<3" )
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_last_filled_SQL",str(inst),symbol)
            return ""
        self.con.commit()
        ordres = res.fetchall()
        count_1_2 = ordres[0][0]
        try:
            res = self.cur.execute("SELECT COUNT() FROM Ordres "
                                   +"WHERE sens='SELL' AND status='FILLED' AND symbol='"
                                   +str(symbol)+"' AND date_debut LIKE '"+date+"%' AND ID_ecart='"+str(ID_ecart)+"'"
                                   +" AND niveau=3" )
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_last_filled_SQL",str(inst),symbol)
            return ""
        self.con.commit()
        ordres = res.fetchall()
        count_3 = ordres[0][0]
        try:
            res = self.cur.execute("SELECT COUNT() FROM Ordres "
                                   +"WHERE sens='SELL' AND status='FILLED' AND symbol='"
                                   +str(symbol)+"' AND date_debut LIKE '"+date+"%' AND ID_ecart='"+str(ID_ecart)+"'"
                                   +" AND niveau=4" )
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_last_filled_SQL",str(inst),symbol)
            return ""
        self.con.commit()
        ordres = res.fetchall()
        count_4 = ordres[0][0]
        count=[count_1_2,count_3,count_4]
        return count
    
    def count_buy_ID_ecart(self,symbol,annee,mois,ID_ecart):
        date = str(annee)+"-"+"%02.0f"%mois
        try:
            res = self.cur.execute("SELECT COUNT() FROM Ordres "
                                   +"WHERE sens='BUY' AND status='FILLED' AND symbol='"
                                   +str(symbol)+"' AND date_debut LIKE '"+date+"%' AND ID_ecart='"+str(ID_ecart)+"'"
                                   +" AND niveau<3" )
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_last_filled_SQL",str(inst),symbol)
            return ""
        self.con.commit()
        ordres = res.fetchall()
        count_1_2 = ordres[0][0]
        try:
            res = self.cur.execute("SELECT COUNT() FROM Ordres "
                                   +"WHERE sens='BUY' AND status='FILLED' AND symbol='"
                                   +str(symbol)+"' AND date_debut LIKE '"+date+"%' AND ID_ecart='"+str(ID_ecart)+"'"
                                   +" AND niveau=3" )
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_last_filled_SQL",str(inst),symbol)
            return ""
        self.con.commit()
        ordres = res.fetchall()
        count_3 = ordres[0][0]
        try:
            res = self.cur.execute("SELECT COUNT() FROM Ordres "
                                   +"WHERE sens='BUY' AND status='FILLED' AND symbol='"
                                   +str(symbol)+"' AND date_debut LIKE '"+date+"%' AND ID_ecart='"+str(ID_ecart)+"'"
                                   +" AND niveau=4" )
        except sqlite3.IntegrityError as inst:
            self.new_log_error("get_last_filled_SQL",str(inst),symbol)
            return ""
        self.con.commit()
        ordres = res.fetchall()
        count_4 = ordres[0][0]
        count=[count_1_2,count_3,count_4]
        return count
    
    def baisser_niveau_ordre_SQL(self,key,new_niveau):
        try:
            self.cur.execute("UPDATE Ordres SET niveau=? WHERE ID=?",
                             (str(new_niveau),str(key)))
        except sqlite3.IntegrityError as inst:
            ordre = self.get_order_info_by_ID(key)
            self.new_log_error("update_order_benef_SQL",str(inst),ordre["symbol"])
            return inst
        retour = self.con.commit()
        return retour

    def arrangement_DB(self,symbol):
        tab = {185:-10,
               186:-10,
               187:-10,
               188:10,
               189:10,
               190:10,
               191:10,
               192:10,
               193:10,
               194:3}
        keys = tab.keys()
        for key in keys:
            print(key)
            print(self.get_ajout_reel_by_ID(symbol,key))
            bet = self.get_ecart_bet_from_symbol_and_ID(symbol,key)[3]
            new_bet = bet + tab[key]
            print(bet)
            print(new_bet)
            self.update_bet_with_ID(symbol,key,new_bet)
            #self.add_to_ajout(symbol,key,tab[key])
            #self

def main():
    sql = sqlAcces()
    DEVISE='XRPEUR'

    #sql.add_ajout_to_ecart(DEVISE)
    #print(sql.get_ajout_flag(DEVISE))
    #print(sql.get_ajout_entier_dic(DEVISE))
    #print(sql.get_ajout_reel_by_ID(DEVISE,30))
    #dic={4:0.7,5:0.7,6:0.7}
    #print(sql.set_ajout_tab(DEVISE,dic))
    #sql.add_ajout_to_ecart(DEVISE)
    #print(sql.get_montant_entre_ordres(DEVISE,9,6))
    #print(sql.new_log_debug("ici","message","XRPEUR"))
    #sql.set_ecart_bet("DOGEEUR.csv")
    #print(sql.get_last_filled("XRPEUR"))
    #sql.set_ecart_bet("XRPEUR.csv")
    #sql.set_ajout("DOGEEUR_Ajout.csv")
    #print(sql.get_epargne("XRPEUR"))
    #sql.add_to_ajout("XRPEUR",57,1)
    #lastfilled = sql.get_last_filled(DEVISE)
    #for i in range(180):
    #    sql.calcul_delta_pour_ajout("XRPEUR",lastfilled,2,158+2*i)
    #sql.calcul_delta_pour_ajout("XRPEUR",lastfilled,4)
    #sql.calcul_benefice(DEVISE,lastfilled)

    #resultat = sql.get_gain_mois("XRPEUR",2024,7)
    """
    sql.min_sell("XRPEUR",2024,5)
    sql.max_sell("XRPEUR",2024,5)
    sql.min_buy("XRPEUR",2024,5)
    sql.max_buy("XRPEUR",2024,5)
    sql.count_sell_ID_ecart("XRPEUR",2024,7,157)
    print("XRPEUR: "+str(resultat))
    total = resultat
    resultat = sql.get_gain_mois("DOGEBTC",2024,7)
    print("DOGEBTC: "+str(resultat))
    print("DOGEBTC (EUR): "+str(resultat*60000))
    total += resultat*60000
    resultat = sql.get_gain_mois("DOGEEUR",2024,7)
    print("DOGEEUR: "+str(resultat))
    total += resultat
    print("total: "+str(total))
    #sql.arrangement_DB("XRPEUR")"""
    #sql.ajout_up_bet("XRPEUR",30,5)
    #last_filled = sql.get_last_filled("XRPEUR")
    #print(last_filled)
    #sql.get_calcul_benef_with_ID("XRPEUR",172)
    #sql.get_ID_to_UP("XRPEUR",172)
    sql.add_to_ajout("XRPEUR",172,8)
    sql.add_to_ecart("XRPEUR",172,8)

if __name__ == '__main__':
     main()
