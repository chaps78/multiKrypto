import sqlite3
from datetime import datetime, timezone


class sqlAcces():
    def __init__(self):
        self.con = sqlite3.connect("DB.db")
        self.cur = self.con.cursor()


    def new_order(self,ID,symbol,montant,limite,status,date_debut,date_fin,montant_exec,type,sens):
        try:
            self.cur.execute("INSERT INTO Ordres VALUES(?,?,?,?,?,?,?,?,?,?)",(ID,symbol,montant,limite,status,date_debut,date_fin,montant_exec,type,sens))
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
            self.cur.execute("UPDATE Ordres SET status=?,date_fin=?,montant_execute=? WHERE ID=?",(status,date_fin,montant_exec,str(ID)))
        except sqlite3.IntegrityError as inst:
            self.new_log("update_order_SQL",str(inst))
            return inst
        retour = self.con.commit()
        return retour

    def get_orders_status_filter(self,status):
        try:
            res = self.cur.execute("SELECT * FROM Ordres WHERE status='"+status+"'")

        except sqlite3.IntegrityError as inst:
            self.new_log("get_orders_status_filter_SQL",str(inst))
            return inst
        self.con.commit()
        return res.fetchall()
    
    def get_order_info_by_ID(self,ID):
        try:
            res = self.cur.execute("SELECT * FROM Ordres WHERE ID='"+str(ID)+"'")
        except sqlite3.IntegrityError as inst:
            self.new_log("get_order_info_by_ID_SQL",str(inst))
            return inst
        self.con.commit()
        return res.fetchall()
    
    def new_log(self,emplacement,message):
        try:
            self.cur.execute("INSERT INTO Log VALUES(?,?,?)",(datetime.now(timezone.utc),str(emplacement),str(message)))
        except Exception as inst:
            self.new_log("new_log_SQL",str(inst))
        self.con.commit()

    

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
sql.new_log("la","pas bien")