import sqlite3
import time
from datetime import datetime

class graph_gen():
    def __init__(self):
        self.con = sqlite3.connect("histo_price.db")
        self.cur = self.con.cursor()

    def get_max(self,symbol):
        res = self.cur.execute("SELECT max(max) FROM prix WHERE symbol='"+symbol+"'")
        return res.fetchall()[0][0]
    

    def get_min(self,symbol):
        res = self.cur.execute("SELECT min(min) FROM prix WHERE symbol='"+symbol+"'")
        return res.fetchall()[0][0]
    
    def generate_10_ranges(self,symbol):
        max = self.get_max(symbol)
        min = self.get_min(symbol)
        nbr_steps=10
        delta = max-min
        band = {}
        start = min
        i=0
        while start < max:
            band[i]=[start,start+delta/nbr_steps]
            start+=delta/nbr_steps
            i+=1
        #keys = band.keys()
        #for key in keys:
        #    print(band[key])
        return band
    
    def get_all(self,symbol):
        res = self.cur.execute("SELECT * FROM prix WHERE symbol='"+symbol+"' ORDER BY date")
        all = res.fetchall()
        return all
    
    def get_all_between_dates(self,symbol,start,end):
        res = self.cur.execute("SELECT * FROM prix WHERE date>"+str(start)+" AND date<"+str(end)+" AND symbol='"+symbol+"' ORDER BY date")
        all = res.fetchall()
        return all
    
    def set_value(self,symbol,index,start,end,benef,ecart,date,nbstep):
        self.cur.execute("INSERT INTO stat VALUES(?,?,?,?,?,?,?,?)",
                                 (symbol,int(index),float(start),float(end),float(benef),float(ecart),str(date),int(nbstep)))
        self.con.commit()
    
    def emul(self,all,symbol,range,nbr_steps,capital,fee_percent,month_range):
        if all[0][2]<range[0]:
            buy_limit=0
            sell_limit= range[0]+(range[1]-range[0])/nbr_steps
        elif all[0][2]>range[1]:
            buy_limit= range[1]-(range[1]-range[0])/nbr_steps
            sell_limit= range[1]*50
        else:
            buy_limit=range[0]
            sell_limit=range[0]+2*(range[1]-range[0])/nbr_steps
            while sell_limit<all[0][2]:
                buy_limit+=(range[1]-range[0])/nbr_steps
                sell_limit+=(range[1]-range[0])/nbr_steps
        #print("buy limit"+str(buy_limit))
        #print("sell limit"+str(sell_limit))
        ordres_filled={"buy":[],"sell":[]}
        for prix in all:
            #print("buy limit : \t"+str(buy_limit))
            #print("sell limit : \t"+str(sell_limit))

            #print("plop : "+str(prix))
            if month_range == self.get_year_month_from_timestamp(prix[1]):
                sample_return = self.one_sample(buy_limit,sell_limit,prix,range,nbr_steps)
                buy_limit = sample_return[0]
                sell_limit = sample_return[1]
                if sample_return[2] != []:
                    for el in sample_return[2]:
                        ordres_filled["buy"].append(el)
                
                if sample_return[3] != []:
                    for el in sample_return[3]:
                        ordres_filled["sell"].append(el)
        #print("\n##################\n")
        #print("\n#########     BUY    #########\n")
        #print(ordres_filled["buy"])
        #print(len(ordres_filled["buy"]))
        #print("\n#########     SELL    #########\n")
        #print(ordres_filled["sell"])
        #print(len(ordres_filled["sell"]))
        benefice = self.calcul_benefices(ordres_filled,symbol,range,nbr_steps,capital,fee_percent)
        return benefice

    def calcul_benefices(self,liste_ordres,symbol,range,nbr_steps,capital,fee_percent):
        #ACHAT
        benef=0
        for buy in liste_ordres["buy"]:
            benef -= (capital)*buy*fee_percent
        #VENTE
        for sell in liste_ordres["sell"]:
            benef += (capital)*((range[1]-range[0])/nbr_steps) - (capital)*sell*fee_percent

        #print("Le benefice est de : "+str(benef))
        return benef

        

    def achat_simu(self,limites,achats_existant,prix,nbr_steps,range):
        i=0
        while prix[4]<limites[0]:
            #print("ACHAT")
            #print(limites)
            #if i > 0:
            #    print("Niveau achat : "+str(i))
            i+=1
            achats_existant.append(limites[0])
            limites[1] =limites[0] + (range[1]-range[0])/nbr_steps
            limites[0]-=(range[1]-range[0])/nbr_steps
            if limites[0]<range[0]:
                limites[0]=0
            #print("Limites ACHAT : " + str(limites))
            #print(achats_existant)

        retour={}
        retour["limites"]=limites
        retour["achat_ex"]=achats_existant
        #print("Limites : "+str(limites))
        #print(achats_existant)
        return retour
    
    def vente_simu(self,limites,vente_existant,prix,nbr_steps,range):
        i=0
        while prix[3]>limites[1]:
            #if i > 0:
            #    print("Niveau vente : "+str(i))
            #    print(vente_existant)
            #print("VENTE")
            #print(limites)
            i+=1
            vente_existant.append(limites[1])
            limites[0] = limites[1] - (range[1]-range[0])/nbr_steps
            limites[1]+=(range[1]-range[0])/nbr_steps
            if limites[1]>range[1]:
                limites[1]=range[1]*1000
            #print("Limites VENTES : "+str(limites))
            #print(vente_existant)


        retour={}
        retour["limites"]=limites
        retour["vente_ex"]=vente_existant
        #print("achat existant : " + str(achats_existant))

        return retour
    
    def one_sample(self,buy_limit,sell_limit,prix,range,nbr_steps):
        achats_init = []
        achat_simu = self.achat_simu([buy_limit,sell_limit],achats_init,prix,nbr_steps,range)
        achats_existant=achat_simu["achat_ex"]

        buy_limit = achat_simu["limites"][0]
        sell_limit = achat_simu["limites"][1]

        vente_init = []
        vente_simu = self.vente_simu([buy_limit,sell_limit],vente_init,prix,nbr_steps,range)
        vente_existant = vente_simu["vente_ex"]
        #if achats_existant != []:
        #    print("ACHAT : "+str(achats_existant))
        #if vente_existant != []:
        #    print("VENTE : "+str(vente_existant))
        #if vente_existant != []:
        #    print("OUIII")
        #    print(vente_existant)
        buy_limit = vente_simu["limites"][0]
        sell_limit = vente_simu["limites"][1]

        if buy_limit<range[0] and buy_limit!=0:
        #    print("PAS BON BUY")
            buy_limit=0
        if sell_limit>range[1] and sell_limit!=range[1]*50:
        #    print("PAS BON SELL")
        #    print(sell_limit)

            sell_limit = range[1]*50
        #    print(sell_limit)


        return [buy_limit,sell_limit,achats_existant,vente_existant]
    
    def get_year_month_from_timestamp(self,time_stamp):
        date_time = datetime.fromtimestamp(time_stamp/1000)
        year = date_time.year
        month = date_time.month
        #print(date_time)
        return [year,month]

    
    def global_generator(self,symbol,file):
        file.write("\n\n"+symbol+"\n")
        band = self.generate_10_ranges(symbol)
        DB_price = self.get_all(symbol)
        #bet = [1.917590776,10.38237504,12.02335899,8.655318932,8.911771239,8.427952071,8.863818381,4.896280112,2.71805439,0.8049937678]
        print(band)
        year_month_init = self.get_year_month_from_timestamp(DB_price[0][1])
        dates_tab=[]
        for el in DB_price:
            date_element = self.get_year_month_from_timestamp(el[1])
            if not(date_element in dates_tab):
                dates_tab.append(date_element)
                print(date_element)

        previus = 0
        flag = True
        for el in DB_price:
            if el[1]<previus:
                print("Problème d'ordre de dates")
                flag = False
            previus = el[1]
        if flag:
            print("ordre des dates OK")

        file.write(str(band)+"\n")
        for month_range in dates_tab:
            start_end = self.start_end_date_time_stamp(month_range)
            BD_date_range = self.get_all_between_dates(symbol,start_end[0],start_end[1])
            for tr in range(10):
                benef_max = [0,0]
                for el in range(100):
                    benefice = self.emul(BD_date_range,symbol,band[tr],el+1,10,0.00075,month_range)
                    #print("nbr steps : "+str(el+1)+"\t benef : " + str(benefice))
                    if benefice > benef_max[1]:
                        benef_max[0]=el+1
                        benef_max[1]=benefice
                if benef_max == [0,0]:
                    print(str(tr)+";"+str(benef_max[0])+";"+str(benef_max[1]).replace(".",",")+";0;"+str(month_range))
                    file.write(str(tr)+";"+str(benef_max[0])+";"+str(benef_max[1]).replace(".",",")+";0;"+str(month_range)+"\n")
                    self.set_value(symbol,tr,band[tr][0],band[tr][1],float(str(benef_max[1])),benef_max[0],month_range,0)
                else:
                    print(str(tr)+";"+str(benef_max[0])+";"+str(benef_max[1]).replace(".",",")+";"+str((band[tr][1]-band[tr][0])/benef_max[0])+";"+str(month_range))


                ######################################################################################################
                # Ajouter Ici pour écrire le resultat dans la DB
                ######################################################################################################
                    file.write(str(tr)+";"+str(benef_max[0])+";"+str(benef_max[1]).replace(".",",")+";"+str((band[tr][1]-band[tr][0])/benef_max[0])+";"+str(month_range)+"\n")
                    self.set_value(symbol,tr,band[tr][0],band[tr][1],float(str(benef_max[1])),(band[tr][1]-band[tr][0])/benef_max[0],month_range,benef_max[0])



    def start_end_date_time_stamp(self,date):
        start_date = datetime(date[0],date[1],1)
        start_stamp = int(1000*time.mktime(start_date.timetuple()))
        if date[1]<12:
            end_date = datetime(date[0],date[1]+1,1)
            end_stamp = int(1000*time.mktime(end_date.timetuple()))
        else:
            end_date = datetime(date[0]+1,1,1)
            end_stamp = int(1000*time.mktime(end_date.timetuple()))
        return[start_stamp,end_stamp]


def main():
    graph = graph_gen()
    fichier = open("data.txt", "a")

    symbols = ["BTCEUR","ETHBTC","ETHUSDT","EURUSDT","PEPEEUR","XRPEUR"]
    for symbol in symbols:
        graph.global_generator(symbol,fichier)




    #res = graph.start_end_date_time_stamp([2021,5])

    #print(len(graph.get_all_between_dates("BTCUSDT",res[0],res[1])))

    fichier.close()


if __name__ == '__main__':
     main()