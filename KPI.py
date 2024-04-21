from bininterface import binAcces


class Kpi():

    def __init__(self):
        self.bin = binAcces()

    def reste_sur_limites(self,symbol):
        last_filled = self.bin.sql.get_last_filled(symbol)
        devises=self.bin.sql.get_devises_from_symbol(symbol)
        founds = self.bin.get_found([devises["devise1"],devises["devise2"]])
        devise1 = founds[devises["devise1"]]
        devise2 = founds[devises["devise2"]]
        ecart_bet_dic = self.bin.sql.get_ecart_bet_from_symbol(symbol)
        ID_max = max(ecart_bet_dic.keys())
        ID_ecart_courant = last_filled["ID_ecart"]
        while ID_ecart_courant < ID_max:
            ID_ecart_courant+=1
            devise1 -= ecart_bet_dic[ID_ecart_courant][1]
        ID_ecart_courant = last_filled["ID_ecart"]
        while ID_ecart_courant > 0:
            ID_ecart_courant -= 1
            devise2 -= ecart_bet_dic[ID_ecart_courant][1]*ecart_bet_dic[ID_ecart_courant][0]
        ret=[devise1,devise2]
        self.bin.sql.set_KPI_restes(symbol,ret,last_filled["ID_ecart"])
        return ret

    def calcul_ajout(self,symbol,restes):
        last_filled = self.bin.sql.get_last_filled(symbol)
        ecart_bet = self.bin.sql.get_ecart_bet_from_symbol_and_ID(symbol,last_filled["ID_ecart"])
        benef = restes["devise2"]
        devise_percent = self.bin.sql.get_devises_from_symbol(symbol)
        down = benef*devise_percent["down"]/100
        local = benef*devise_percent["local"]/100
        up = benef*devise_percent["up"]/100
        ajout_local = {}
        ajout_local[last_filled["ID_ecart"]-2] = (local/5)/ecart_bet[2]
        ajout_local[last_filled["ID_ecart"]-1] = (local/5)/ecart_bet[2]
        ajout_local[last_filled["ID_ecart"]] = (local/5)/ecart_bet[2]
        ajout_local[last_filled["ID_ecart"]+1] = (local/5)/ecart_bet[2]
        ajout_local[last_filled["ID_ecart"]+2] = (local/5)/ecart_bet[2]
        print(ajout_local)
        data_up = self.position_up()
        for i in range(data_up[1]):
            ajout_local[data_up[0]+i]=up/data_up[1]
        self.bin.sql.set_ajout_tab(symbol,ajout_local,1)

    def position_up(self):
        ### TODO a penser #######
        position = 60
        largeur = 2
        return [position,largeur]




###########################################################################
#                                 MAIN                                    #
###########################################################################
def main():
    DEVISE="DOGEBTC"
    kpi = Kpi()

    kpi.reste_sur_limites(DEVISE)
    last_restes = kpi.bin.sql.get_last_reste(DEVISE)
    print(last_restes)
    kpi.calcul_ajout(DEVISE,last_restes)




if __name__ == '__main__':
     main()

