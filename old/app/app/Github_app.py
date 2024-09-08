import numpy as np
from datetime import datetime
from app.Modules.Github_Module import GitHub
from app.Modules.GithubSnake_Module import Git_Snake
from tools.font import FONT

class git:
    def __init__(self,cfg):
        # begin class with data
        self.res = []
        self.mat = []
        self.point = []
        self.base_mat = []

        self.gh = GitHub(cfg)
        self.sk = Git_Snake()
        self.F = FONT()

        self.tittle = self.F.pixel("Git hub", (255,255,255))
        self.name = self.F.pixel("Gabriel-br2",(255,255,255))
        self.tittle = self.F.limited(self.tittle,30)
        self.name = self.F.limited(self.name,40)

        self.update_data()
        
    def update_data(self):
        # update all info on git
        try:
            self.gh.get_repo()
            self.gh.get_commits()

            self.res = self.gh.commits
            
            self.create_WeekMat()
            self.create_Wallpaper()
        except Exception as e:
            print("Error in Github_app (update data): ",e) 

    def create_Wallpaper(self):
        # create de background of the snake
        try:
            base = np.zeros((32, 64, 3), dtype=int)

            x,y = 0,0
            for b in range(7):
                for a in range(32):
                    color = self.mat[b][a]*85
                    
                    if color == 0: 
                        self.mat[b][a] = False
                    else: 
                        self.mat[b][a] = True
                        self.point.append([b*2,a*2])

                    base[y][x][1] =     color
                    base[y][x+1][1] =   color
                    base[y+1][x][1] =   color
                    base[y+1][x+1][1] = color
                    x += 2
                y += 2
                x = 0 
            self.base_mat = base       
        except Exception as e:
            print('Error in Git_hub app (create wallpaper): ',e)

    def create_WeekMat(self):
        # format the matrixes to marge then
        try:
            hoje = datetime.today()
            self.mat = np.zeros((7, 32), dtype=int)
            for data in self.res:
                try:
                    ano, mes, dia = data
                    data_formatada = datetime(ano, mes, dia)
                    diferenca = hoje - data_formatada
                    semana = diferenca.days // 7
                    dia_semana = data_formatada.weekday()
                    if semana < 32:
                        valor = min(self.res.count(data), 3)
                        self.mat[dia_semana][31-semana] = valor
                except Exception as e:
                    print(e)
                    pass
        except Exception as e:
            print('Error in git hub app (create WeekMat)')

    def put_data(self):
        # put data in matrix
        try:
            self.main_mat[17:22, 5:5+30,:] = self.tittle[0]
            self.main_mat[25:30, 5:5+40,:] = self.name[0]
        except IndexError: pass
        except TypeError: pass
        except Exception as e:
            print("Error in Github app (put_text): ",e)

    def git_loop(self):
        # main loop
        self.point = self.sk.movement_IA(self.point)
        self.main_mat = self.sk.update(self.base_mat,self.sk.c)
        if self.sk.reset: self.update_data()
        self.put_data()

        return self.main_mat




        

        


