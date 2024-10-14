import sqlite3
import os



class hist_recup():
    def __init__(self):
        self.con = sqlite3.connect("histo_price.db")
        self.cur = self.con.cursor()

    def file2DB(self,file_name,symbol):
        print(file_name)
        print(symbol)
        file  = open(file_name,"r",encoding="utf8")
        lines = file.readlines()
        for line in lines:
            try:
                self.cur.execute("INSERT INTO prix VALUES(?,?,?,?,?,?)",
                                (symbol
                                ,int(line.split(",")[0])
                                ,float(line.split(",")[1])
                                ,float(line.split(",")[2])
                                ,float(line.split(",")[3])
                                ,float(line.split(",")[4])))
                self.con.commit()
            except sqlite3.IntegrityError as inst:
                print("Integrity probleme " + symbol)
                print("OUIII " + str(inst) + " : ")

        file.close()




def main():
    hist = hist_recup()
    symbol = "ETHBTC"
    liste_fichiers = os.listdir(symbol)
    for fichier in liste_fichiers:
        print("FICHIER : " + str(fichier))
        if "csv" in fichier and "lock" not in fichier:
            hist.file2DB(symbol+"/"+fichier,symbol)

if __name__ == '__main__':
     main()

     
