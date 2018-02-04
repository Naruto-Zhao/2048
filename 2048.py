#!/usr/bin/python3
# -*- coding: utf-8 -*- 
# Copyright: Zhao Guo
# Opertion Environment: Ubuntu 16.04


import curses
from collections import defaultdict
from random import randrange, choice

actions = ['Up', 'Left', 'Down', 'Right', 'Restart', 'Exit', 'Back']      #记录操作种类
letter_codes = [ord(ch) for ch in 'WASDRQBwasdrqb']                 #根据人的习惯设置常用按键，还要考虑大小写
action_dict = dict(zip(letter_codes, actions * 2))                #将操作与按键连接起来
memory_field = []
curpos = 0

#获取用户的操作
def get_usr_action(keyboard):
    ch = 'N'
    while ch not in action_dict:
        ch = keyboard.getch()
    return action_dict[ch]

#矩阵转置
def transpose(field):
    return [list(row) for row in zip(*field)]

#矩阵反转
def invert(field):
    return [row[::-1] for row in field]


#建立游戏的一个类，并设置相应的操作
class GameField():
    def __init__(self, height=6, width=6, win=2048):
        self.height = height
        self.width = width
        self.win_value = win 
        self.score = 0
        self.high_score = 0
        self.reset()
    
    #随机数产生函数
    def spawn(self):
        #随机产生2或4
        new_element = 4 if randrange(100) > 89 else 2
        (i, j) = choice([(i, j) for i in range(self.height) for j in range(self.width) if self.field[i][j] == 0])
        self.field[i][j] = new_element

    #重置
    def reset(self):
        global curpos
        #重置棋盘
        if self.score > self.high_score: 
            self.high_score = self.score    #记录最高分
        self.score = 0 
        self.field = [[0 for i in range(self.width)] for j in range(self.height)]
        self.spawn()
        self.spawn()

        memory_field.clear()                            #重置时清空上次的记录
        memory_field.append((self.field, self.score))
        curpos = 0

    #判断是否可以朝一个方向移动
    def move_is_possible(self, direction):
        def movable(row):
            def change(i):
                if row[i] == 0 and row[i + 1] != 0:
                    return True
                if row[i] != 0 and row[i + 1] == row[i]:
                    return True
                return False

            return any(change(i) for i in range(len(row) - 1))

        ##检查各个方向是否可以移动
        check = {}
        check['Left'] = lambda field: any(movable(row) for row in field)
        check['Right'] = lambda field: check['Left'](invert(field))
        check['Up'] = lambda field: check['Left'](transpose(field))
        check['Down'] = lambda field: check['Right'](transpose(field))

        if direction in check:
            return check[direction](self.field)
        else:
            return False

    ##移动一步
    def move(self, direction):
        global curpos
        def move_row_left(row):
            #将散开的数向左挤在一起
            def tighten(row):        
                new_row = [i for i in row if i != 0]
                new_row += [0 for i in range(len(row) - len(new_row))]
                return new_row

            #合并数据
            def merge(row):
                flag = False
                new_row = []
                for i in range(len(row)):
                    if flag:                              #可以合并
                        new_row.append(2 * row[i])
                        self.score += 2 * row[i]
                        flag = False
                    else:                                 #不可以合并
                        if i + 1 < len(row) and row[i] == row[i + 1]:
                            flag = True
                            new_row.append(0)
                        else:
                            new_row.append(row[i])
                
                assert len(new_row) == len(row)           #看一行格子是否一样
                return new_row
            return tighten(merge(tighten(row)))           #先挤压在合并，然后再挤压
        
        moves = {}
        moves['Left'] = lambda field: [move_row_left(row) for row in field]
        moves['Right'] = lambda field: invert(moves['Left'](invert(field)))
        moves['Up'] = lambda field: transpose(moves['Left'](transpose(field)))
        moves['Down'] = lambda field: transpose(moves['Right'](transpose(field))) 

        if direction in moves:
            if self.move_is_possible(direction):            #判断是否可以移动
                self.field = moves[direction](self.field)   #更新数据
                self.spawn()                                #并随机产生一个数
                
                #保存上一次的记录
                if len(memory_field) > 0 and curpos != len(memory_field) - 1:
                    curpos += 1 
                    memory_field[curpos] = (self.field, self.score)       
                else:
                    memory_field.append((self.field, self.score))             
                    curpos = len(memory_field) - 1

                return True
            else:
                return False
    
    def is_win(self):                                       #判断是否胜利
        return any(any(i >= self.win_value for i in row) for row in self.field)

    def is_gameover(self):                                  #当四个方向都不可以移动时，游戏结束
        return not any(self.move_is_possible(movement) for movement in actions)

    #绘制游戏界面
    def draw(self, screen):
        help_string1 = '(W)Up (S)Down (A)Left (D)Right'
        help_string2 = '  (R)Restart (Q)Exit (B)Back '
        gameover_string = '           GAME OVER'
        win_string = '          YOU WIN!'
        def cast(string):
            screen.addstr(string + '\n')

        #绘制水平分割线
        def draw_hor_separator():
            line = '+------' * self.width + '+'
            separator = defaultdict(lambda: line)
            if not hasattr(draw_hor_separator, "counter"):
                draw_hor_separator.counter = 0
            cast(separator[draw_hor_separator.counter])
            draw_hor_separator.counter += 1

        #输出竖线和数字
        def draw_row(row):
            cast(''.join('|{: ^5} '.format(num) if num > 0 else '|      ' for num in row) + '|')

        screen.clear()

        cast('SCORE: ' + str(self.score))
        if 0 != self.high_score:
            cast('HIGHSCORE: ' + str(self.high_score))

        for row in self.field:
            draw_hor_separator()
            draw_row(row)

        draw_hor_separator()

        if self.is_win():
            cast(win_string)
        else:
            if self.is_gameover():
                cast(gameover_string)
            else:
                cast(help_string1)
        cast(help_string2)


    
def main(stdscr):
    def init():                     #初始化棋盘
        game_field.reset()
        return 'Game'

    def not_game(state):            #记录Gameover状态
        game_field.draw(stdscr)     #绘制图像
        action = get_usr_action(stdscr)   #用户输入

        response = defaultdict(lambda: state)
        response['Restart'], response['Exit'], response['Back'] = 'Init', 'Exit', 'Back'
        return response[action]

    def game():
        game_field.draw(stdscr)    #绘制图像
        action = get_usr_action(stdscr)  #用户输入

        if action == 'Restart':
            return 'Init'
        if action == 'Exit':
            return 'Exit'
        if action == 'Back':
            return 'Back'
        if game_field.move(action):
            if game_field.is_win():     #胜利了
                return 'Win'
            if game_field.is_gameover():  #失败了
                return 'Gameover'
        return 'Game'

    def back_former_step():               #若想悔棋，可以返回到上一次记录
        global curpos                     #使用全局变量
        if len(memory_field) > 0 and curpos > 0:
            curpos -= 1
            game_field.field = memory_field[curpos][0]
            game_field.score = memory_field[curpos][1]

        return 'Game'

                   
    state_actions = {
        'Init':init,
        'Win':game,       #胜利后还可以继续玩，直到游戏结束，或者重新开始或退出
        'Gameover':lambda: not_game('Gameover'),
        'Game':game,
        'Back':back_former_step
    }
    
    curses.use_default_colors()
    game_field = GameField(6, 6, 2048)     #创建一个棋盘

    state = 'Init'      #初始状态

    while state != 'Exit':
        state = state_actions[state]()    #不断进行状态切换

curses.wrapper(main)

