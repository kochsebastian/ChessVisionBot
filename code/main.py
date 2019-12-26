
import tkinter as tk
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


function_parser = ""


def clear_logs():
    logs_text.delete('1.0', tk.END)
    #add_log("Logs have been cleared:")

def add_log(log):
    logs_text.insert(tk.END,log + "\n")

def stop_playing():
    global running
    running = False
    raise SystemExit

def start_playing():
    global function_parser
    global running
    global slider_str
    global slider_var
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
    

    button_start = tk.Button(text="Stop playing", command =stop_playing)
    button_start.grid(column=0,row = 1)



    add_log("Checking if we are black or white...")
    resized_chessboard = chessboard_detection.get_chessboard(game_state)

    game_state.previous_chessboard_image = resized_chessboard

    we_are_white = board_basics.is_white_on_bottom(resized_chessboard)
    game_state.we_play_white = we_are_white
    if we_are_white:
        add_log("We are white" )
        game_state.moves_to_detect_before_use_engine = 0
    else:
        add_log("We are black")
        game_state.moves_to_detect_before_use_engine = 1
        first_move_registered = False
        while first_move_registered == False:
            first_move_string = askstring('First move', 'What was the first move played by white?')
            if len(first_move_string) > 0:
                first_move = chess.Move.from_uci(first_move_string)
                first_move_registered = game_state.register_move(first_move,resized_chessboard)

        add_log("First move played by white :"+ first_move_string)        
 
    while running:
        window.update()

        #cv2.imshow('Resized image',game_state.previous_chessboard_image)
        #add_log("Moves to detect before use engine" + str(game_state.moves_to_detect_before_use_engine))
        if game_state.moves_to_detect_before_use_engine == 0:
            #add_log("Our turn to play:")
            score,winrate = game_state.play_next_move(position.factor,strength,variance)
            position_eval = tk.Label(text=f"Score: {score} \t Winrate: {winrate}",anchor="e", wraplength = 300)
            position_eval.grid(column =0,row = 5)
            #add_log("We are done playing")
        
        found_move, move,img_boards = game_state.register_move_if_needed()
        diff = abs(img_boards[0] - img_boards[1])
        numpy_horizontal = np.vstack((img_boards[0], img_boards[1], diff))
        image = cv2.resize(numpy_horizontal, (200, 600))
        img = ImageTk.PhotoImage(Image.fromarray(np.uint8(image)))
        imglabel = tk.Label(window, image=img).grid(row=2, column=1,rowspan = 5) 
        
        
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
    new_move = askstring('Missed Move', 'What is the next move')
    function_parser = new_move
    print(new_move)
    # if len(new_move) > 0:
    #     first_move = chess.Move.from_uci(new_move)
    #     first_move_registered = game_state.register_move(first_move, resized_chessboard)



ml_model.init()

window = tk.Tk()

window.geometry('%dx%d+%d+%d' % (525,700, 1000, 100))
window.title("ChessBot")

label_title = tk.Label(text="Computer Vision based Chessbot for Online-Chess-Websites by Sebastian Koch",anchor="e", wraplength = 300)
label_title.grid(column = 0,row = 0,columnspan=2)


button_start = tk.Button(text="Start playing", command =start_playing)
button_start.grid(column=0,row =1)
button_enter_move=tk.Button(text="Missed Move",command=new_move)
button_enter_move.grid(column=1,row =1)
strength = tk.IntVar()
slider_str = tk.Scale(window, from_= 0, to=2000,tickinterval=500, 
                    orient=tk.HORIZONTAL,sliderlength=10,length=250,
                    resolution=10,label="Time to think [ms]",variable=strength)
slider_str.set(1100)

slider_str.grid(column = 0,row = 2,padx=10, pady=10)
variance = tk.IntVar()
slider_var = tk.Scale(window, from_= 0, to=2000,tickinterval=500, 
                    orient=tk.HORIZONTAL,sliderlength=10,length=250,
                    resolution=10,label="Maximum move delay variance [ms]",variable=variance)
slider_var.set(0)

slider_var.grid(column = 0,row = 3,padx=10, pady=10)
logs_text = tk.Text(window,width=40,height=25,background='gray')
logs_text.grid(column = 0,row = 4,padx=10, pady=10)
gui_image=np.zeros((600,200), dtype=int)
img = ImageTk.PhotoImage(Image.fromarray(np.uint8(gui_image)))
imglabel = tk.Label(window, image=img).grid(row=2, column=1,rowspan = 5) 
running = True
window.mainloop()
