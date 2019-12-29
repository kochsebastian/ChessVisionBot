
import tkinter as tk
import ttk
import chessboard_detection
import board_basics
from game_state_classes import Game_state
from tkinter.simpledialog import askstring
import ml_model
import chess
from PIL import ImageTk, Image
import cv2
import numpy as np
import sys
import os


function_parser = ""




def clear_logs():
    logs_text.delete('1.0', tk.END)
    #add_log("Logs have been cleared:")

def add_log(log):
    logs_text.insert(tk.END,log + "\n")

def stop_playing():
    global running
    running = False
    button_start = ttk.Button(tab1, text="Start playing", command=start_playing)
    button_start.grid(column=0, row=1, pady=10, columnspan=2)

    # raise SystemExit

def start_playing():
    global function_parser
    global running
    global slider_str
    global slider_var
    running = True
    strength = slider_str.get()+1
    variance = slider_var.get()+1
    slider_str.config(state=tk.DISABLED)
    slider_var.config(state=tk.DISABLED)
    game_state = Game_state()
    add_log("Looking for a chessboard...")

    found_chessboard, position  = chessboard_detection.find_chessboard()

    if found_chessboard:
        add_log("Found the chessboard " + position.print_custom())
        game_state.board_position_on_screen = position
    else:
        add_log("Could not find the chessboard")
        add_log("Please try again when the board is open on the screen\n")
        return
    

    button_start = ttk.Button(tab1,text="Stop playing", command =stop_playing)
    button_start.grid(column=0,row = 1,pady=10,columnspan=2)



    add_log("Checking if we are black or white...")
    resized_chessboard = chessboard_detection.get_chessboard(game_state)
    game_state.previous_chessboard_image = resized_chessboard

    position_detection = chessboard_detection.get_chessboard(game_state,(800,800))
    # cv2.imshow('fjfh',position_detection)
    # cv2.waitKey(0)
    we_are_white = v.get()#board_basics.is_white_on_bottom(position_detection)
    game_state.we_play_white = we_are_white


    to_move = 'w' if v.get() else 'b'

    game_state.moves_to_detect_before_use_engine = 0 #if v.get() else 1

    pieces = sorted(os.listdir('/Users/sebastiankoch/OnlineChessBot/pieces'))

    vis_glob = np.array([])
    piece_notation =['b','k','n','p','q','r','*','B','K','N','P','Q','R']
    fen_str=''

    rochade ='KQkq'
    en_passant='-'
    halfmoves='0'
    move='1'
    
    order = range(8) if we_are_white else reversed(range(8))
    for i in order:
        vis = np.array([])
        order2 = range(8) if we_are_white else reversed(range(8))
        for j in order2:
            image = board_basics.get_square_image(i,j,position_detection)
            answer = board_basics.piece_on_square(image)
            im = cv2.imread(os.path.join('/Users/sebastiankoch/OnlineChessBot/pieces',pieces[answer]))
            if vis.size==0:
                vis=im
                fen_str+=piece_notation[answer]
            else:
                vis = np.concatenate((vis, im), axis=1)
                fen_str+=piece_notation[answer]
        fen_str+='/'
        if vis_glob.size ==0:
            vis_glob = vis
        else:
            vis_glob = np.concatenate((vis_glob, vis), axis=0)
    
    
    fen_str = fen_str[:-1] + ' ' + to_move + ' ' + rochade + ' ' + en_passant + ' ' + halfmoves + ' ' + move

    for i in range(len(fen_str)):
        if fen_str[i] == ' ':
            break
        count = 0
        if fen_str[i] == '*':
            while fen_str[i] == '*':
                count += 1
                if count==8:
                    print()
                fen_str = fen_str[0 : i : ] + fen_str[i + 1 : :]
            fen_str = fen_str[:i] + str(count) + fen_str[i:]
    print(fen_str)
    game_state.board.set_fen(fen_str)

    # if we_are_white:
    #     add_log("We are white" )
    #     game_state.moves_to_detect_before_use_engine = 0
    # else:
    #     add_log("We are black")
    #     game_state.moves_to_detect_before_use_engine = 1
    #     first_move_registered = False
    #     while first_move_registered == False:
    #         window.attributes('-topmost', 0)
    #         first_move_string = askstring('First move', 'What was the first move played by white?')
    #         if len(first_move_string) > 0:
    #             first_move = chess.Move.from_uci(first_move_string)
    #             first_move_registered = game_state.register_move(first_move,resized_chessboard)
    #             window.attributes('-topmost', 1)

    #     add_log("First move played by white :"+ first_move_string)        

 
    while running:
        window.update()

        #cv2.imshow('Resized image',game_state.previous_chessboard_image)
        #add_log("Moves to detect before use engine" + str(game_state.moves_to_detect_before_use_engine))
        if game_state.moves_to_detect_before_use_engine == 0:
            #add_log("Our turn to play:")
            score,winrate = game_state.play_next_move(position.factor,strength,variance)

            position_eval = ttk.Label(tab1,text=f"Score: {score} \t Winrate: {winrate}",anchor="e", wraplength = 300)
            position_eval.grid(column =0,row = 9,columnspan=2)
            #add_log("We are done playing")
        found_move=False
        move = "no move"
        img_boards = (game_state.previous_chessboard_image,game_state.previous_chessboard_image)
        try:
            found_move, move,img_boards = game_state.register_move_if_needed()
        except:
            stop_playing()
        if found_move:
            v.set(not v.get())
            diff = abs(img_boards[0] - img_boards[1])
            numpy_horizontal = np.vstack((img_boards[0], img_boards[1], diff))
            image = cv2.resize(numpy_horizontal, (200, 600))
            img = ImageTk.PhotoImage(Image.fromarray(np.uint8(image)))
            imglabel = tk.Label(tab1, image=img).grid(row=2, column=2,rowspan = 100)
        
        
        if function_parser:
            move = function_parser
            function_parser=""
            new_board = chessboard_detection.get_chessboard(game_state)
            valid_move_UCI = chess.Move.from_uci(move)
            valid_move_registered = game_state.register_move(valid_move_UCI, new_board)

        if found_move:
            clear_logs()
            add_log("The board :\n" + str(game_state.board) + "\n")
            add_log("\nAll moves :\n" + str(game_state.executed_moves))
    
def new_move():
    global function_parser
    window.attributes('-topmost', 0)
    new_move = askstring('Missed Move', 'What is the next move')
    window.attributes('-topmost', 1)
    function_parser = new_move
    window.attributes('-topmost', 1)
    print(new_move)

    # if len(new_move) > 0:
    #     first_move = chess.Move.from_uci(new_move)
    #     first_move_registered = game_state.register_move(first_move, resized_chessboard)


ml_model.init_binary()
ml_model.init_class()

window = tk.Tk()


window.wm_attributes("-topmost", 1)
window.geometry('%dx%d+%d+%d' % (590,730, 1000, 100))
window.title("OnlineChessBot")

label_title = tk.Label(window,text="Computer Vision based Chessbot for Online-Chess-Websites by Sebastian Koch",anchor="e", wraplength = 300)
label_title.grid(column = 0,row = 0,columnspan=100,pady=5)

note = ttk.Notebook(window)
tab1 = ttk.Frame(note)
tab2 = ttk.Frame(note)
note.add(tab1, text='Computer')
note.add(tab2, text='Analysis')
note.grid(column = 0,row = 1,columnspan=100,padx=10)


button_start = ttk.Button(tab1,text="Start playing", command =start_playing)
button_start.grid(column=0,row = 1,pady=10,columnspan=2)

button_enter_move=ttk.Button(tab1,text="Missed Move",command=new_move)
button_enter_move.grid(column=2,row = 1,pady=10)
v = tk.BooleanVar()
v.set(1)

ttk.Label(tab1, 
      text="To Move:",
      justify = tk.LEFT).grid(row=2, column=0)
ttk.Radiobutton(tab1, 
            text="White",
            # indicatoron = 0,
            # padx = 20, 
            variable=v, 
            value=True).grid(row=3, column=0)
ttk.Radiobutton(tab1, 
            text="Black",
            # indicatoron = 0,
            # padx = 20, 
            variable=v, 
            value=False).grid(row=3, column=1)


strength = tk.IntVar()
slider_str = tk.Scale(tab1, from_= 0, to=2000,tickinterval=500, 
                    orient=tk.HORIZONTAL,sliderlength=10,length=250,
                    resolution=10,label="Time to think [ms]",variable=strength)
slider_str.set(600)

slider_str.grid(column = 0,row = 5,padx=10, pady=10,columnspan=2)
variance = tk.IntVar()
slider_var = tk.Scale(tab1, from_= 0, to=2000,tickinterval=500, 
                    orient=tk.HORIZONTAL,sliderlength=10,length=250,
                    resolution=10,label="Maximum move delay variance [ms]",variable=variance)
slider_var.set(1000)

slider_var.grid(column = 0,row = 6,padx=10, pady=10,columnspan=2)
logs_text = tk.Text(tab1,width=45,height=15,background='gray')
logs_text.grid(column = 0,row = 7,padx=10, pady=10,columnspan=2)
gui_image=np.zeros((600,200), dtype=int)
img = ImageTk.PhotoImage(Image.fromarray(np.uint8(gui_image)))
imglabel = tk.Label(tab1, image=img).grid(row=2, column=2,rowspan = 100) 



running = True
window.mainloop()
