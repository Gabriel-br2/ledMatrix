import random
import time

class Git_Snake:
    def __init__(self):
        # begin class with parameters
        self.color = (128,0,128)
        self.old_rab = [0,0]
        self.target = []
        self.aling = 0 
        self.pos = [[2,0],[1,0],[0,0]]
        
        self.reset = False
        self.valid = False
        self.hit_you = False
        self.hit_left = False
        self.hit_right = False
        
    def move_w(self):
        # movement in north
        try:
            next = [self.pos[2][0]-1,self.pos[2][1]]
            if next in self.pos: 
                self.hit_you = True
                self.valid = False
            elif next[0] < 0:    
                self.hit_left = True
                self.valid = False
            else:
                self.valid = True
                self.pos.append(next)
                self.old_rab = [self.pos[0][0]*2,self.pos[0][1]*2] 
                del(self.pos[0])
        except Exception as e:
            print("Error in git_hub snake (w): ",e)

    def move_a(self):
        # movement in west
        try:
            next = [self.pos[2][0],self.pos[2][1]-1]
            if next in self.pos: 
                self.hit_you = True 
                self.valid = False
            elif next[1] < 0:    
                self.hit_left = True
                self.valid = False
            else:
                self.valid = True
                self.pos.append(next)
                self.old_rab = [self.pos[0][0]*2,self.pos[0][1]*2]
                del(self.pos[0])
        except Exception as e:
            print("Error in git_hub snake (a): ",e)

    def move_s(self):
        # movement in south
        try:
            next = [self.pos[2][0]+1,self.pos[2][1]]
            if next in self.pos: 
                self.hit_you = True
                self.valid = False
            elif next[0] > 14:   
                self.hit_right = True
                self.valid = False        
            else:       
                self.valid = True 
                self.pos.append(next)
                self.old_rab = [self.pos[0][0]*2,self.pos[0][1]*2]
                del(self.pos[0])
        except Exception as e:
            print("Error in git_hub snake (s): ",e)

    def move_d(self):
        # movement in east
        try:
            next = [self.pos[2][0],self.pos[2][1]+1]
            if next in self.pos:  
                self.hit_you = True
                self.valid = False
            elif next[1] > 32:    
                self.hit_right = True
                self.valid = False
            else:       
                self.valid = True     
                self.pos.append(next)
                self.old_rab = [self.pos[0][0]*2,self.pos[0][1]*2]
                del(self.pos[0])
        except Exception as e:
            print("Error in git_hub snake (d): ",e)

    def update(self,base_mat,c):
        # make de update of the position of the snake
        try:
            if c == 'w': self.move_w()
            elif c == 'a': self.move_a()
            elif c == 's': self.move_s()
            elif c == 'd': self.move_d()
            elif c == 'p': return base_mat
    
            try:
                base_mat[self.old_rab[0]][self.old_rab[1]] = (0,0,0)
                base_mat[self.old_rab[0]][self.old_rab[1]+1] = (0,0,0)
                base_mat[self.old_rab[0]+1][self.old_rab[1]] = (0,0,0)
                base_mat[self.old_rab[0]+1][self.old_rab[1]+1] = (0,0,0)
            except: pass

            for a in range(3):
                try:
                    posY = self.pos[a][0]*2
                    posX = self.pos[a][1]*2
                    base_mat[posY][posX] = self.color
                    base_mat[posY+1][posX] = self.color
                    base_mat[posY][posX+1] = self.color
                    base_mat[posY+1][posX+1] = self.color
                except:
                    pass
        except Exception as e:
            print("Error in Git_hub snake (Update): ", e,)

        return base_mat
    
    def movement_IA(self,position):
        # IA of if's to meke the movement of the sneak
        c = 'p'
        if self.aling == 0: self.aling = random.randint(1, 2)
        if self.valid: self.hit_left = self.hit_right = self.hit_you = False
        if self.pos[2] in position: position.remove(self.pos[2])

        if self.target == []:
            if len(position) == 0:
                self.target = [0,0]
            else:                
                j = random.randint(0, len(position)-1)
                self.target = position[j][0]//2,position[j][1]//2
                del(position[j])

        if self.aling == 1 and self.pos[2][0] == self.target[0]:
            self.aling = 2
        if self.aling == 2 and self.pos[2][1] == self.target[1]:
            self.aling = 1

        if self.aling == 1: 
            if self.pos[2][0] < self.target[0]:
                if self.hit_you:
                    if self.hit_left or self.hit_right:
                        if self.pos[2][1] < self.target[1]:
                            c = 'a'
                        else:
                            c = 'd'
                    else:
                        if self.pos[2][1] < self.target[1]:
                            c = 'd'
                        else:
                            c = 'a'
                else:
                    c = 's'

            elif self.pos[2][0] > self.target[0]:
                if self.hit_you:
                    if self.hit_left or self.hit_right:
                        if self.pos[2][1] < self.target[1]:
                            c = 'a'
                        else:
                            c = 'd'
                    else:
                        if self.pos[2][1] < self.target[1]:
                            c = 'd'
                        else:
                            c = 'a'
                else:
                    c = 'w'

        if self.aling == 2:
            if self.pos[2][1] < self.target[1]:
                if self.hit_you:
                    if self.hit_left or self.hit_right:
                        if self.pos[2][0] < self.target[0]:
                            c = 's'
                        else:
                            c = 'w'
                    else:
                        if self.pos[2][0] < self.target[0]:
                            c = 'w'
                        else:
                            c = 's'
                else:   
                    c = 'd'

            elif self.pos[2][1] > self.target[1]:
                if self.hit_you:
                    if self.hit_left or self.hit_right:
                        if self.pos[2][0] < self.target[0]:
                            c = 's'
                        else:
                            c = 'w'
                    else:
                        if self.pos[2][0] < self.target[0]:
                            c = 'w'
                        else:
                            c = 's'
                else:
                    c = 'a'

        if self.pos[2] == list(self.target):
            self.target,self.aling = [],0
        
        self.reset = self.pos[2] == [0, 0] and not position

        time.sleep(0.1)
        self.c = c
        return position
