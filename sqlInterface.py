import sqlite3



class sqlAcces():
    def __init__(self):
        self.con = sqlite3.connect("DB.db")
        self.cur = self.con.cursor()


    def new_order(self,ID,symbol,montant,limite,status,date_debut,date_fin,montant_exec):
        try:
            self.cur.execute("INSERT INTO Ordres VALUES(?,?,?,?,?,?,?,?)",(ID,symbol,montant,limite,status,date_debut,date_fin,montant_exec))
        except sqlite3.IntegrityError as inst:
            return inst
        retour = self.con.commit()
        return retour

    def delete_order(self,ID):
        try:
            self.cur.execute("DELETE FROM Ordres WHERE ID="+str(ID))
        except sqlite3.IntegrityError as inst:
            return inst
        retour = self.con.commit()
        return retour

    def update_order(self,ID,status,date_fin="",montant_exec="0"):
        try:
            self.cur.execute("UPDATE Ordres SET status=?,date_fin=?,montant_execute=? WHERE ID=?",(status,date_fin,montant_exec,str(ID)))
        except sqlite3.IntegrityError as inst:
            print(inst)
            return inst
        retour = self.con.commit()
        return retour

    def get_orders_status_filter(self,status):
        try:
            res = self.cur.execute("SELECT * FROM Ordres WHERE status='"+status+"'")
            print(res.fetchall())

        except sqlite3.IntegrityError as inst:
            print(inst)
            return inst
        retour = self.con.commit()
        return res.fetchall()

    

sql = sqlAcces()

#sql.new_order(1,"XRPEUR",200,0.1,"FILLED",10,12,200)
#sql.new_order(2,"XRPEUR",500,0.1,"FILLED",10,12,200)
#sql.delete_order(3)
#sql.update_order(3,"PART","10/12/2017",50)
res = sql.get_orders_status_filter("FILLED")
print("toto")
print(res)
print("toto")