import chess
import chess.uci
import numpy as np
from board_basics import *
import chessboard_detection
import pyautogui
import cv2
import mss
import math



class Board_position:
    def __init__(self,minX,minY,maxX,maxY,factor):
        self.minX = minX
        self.minY = minY
        self.maxX = maxX
        self.maxY = maxY
        self.factor =factor
        self.current = None

    def print_custom(self):
        return ("from " + str(self.minX) + "," + str(self.minY) + " to " + str(self.maxX) + ","+ str(self.maxY))

class Game_state:

    def __init__(self):
        self.we_play_white = True #This store the player color, it will be changed later
        self.moves_to_detect_before_use_engine = -1 #The program uses the engine to play move every time that this variable is 0
        self.expected_move_to_detect = "" #This variable stores the move we should see next, if we don't see the right one in the next iteration, we wait and try again. This solves the slow transition problem: for instance, starting with e2e4, the screenshot can happen when the pawn is on e3, that is a possible position. We always have to double check that the move is done.
        self.previous_chessboard_image = [] #Storing the chessboard image from previous iteration
        self.executed_moves = [] #Store the move detected on san format
        self.engine = chess.uci.popen_engine("/Users/sebastiankoch/Downloads/chessbot_python-master 2/engine/stockfish-10-64")#The engine used is stockfish. It requires to have the command stockfish working on the shell
        self.board = chess.Board() #This object comes from the "chess" package, the moves are stored inside it (and it has other cool features such as showing all the "legal moves")
        self.board_position_on_screen = []
        self.sct = mss.mss()




    def get_valid_move(self, potential_starts, potential_arrivals, current_chessboard_image):

        print("Starts and arrivals:",potential_starts, potential_arrivals)
        if len( potential_arrivals)==0 or len( potential_starts)==0:
            return "",[]
        valid_move_string = ""
        # Detect castling king side with white
        if ("e1" in potential_starts) and ("h1" in potential_starts) and ("f1" in potential_arrivals) and (
                "g1" in potential_arrivals):
            valid_move_string = "e1g1"

        # Detect castling queen side with white
        if ("e1" in potential_starts) and ("a1" in potential_starts) and ("c1" in potential_arrivals) and (
                "d1" in potential_arrivals):
            valid_move_string = "e1c1"

        # Detect castling king side with black
        if ("e8" in potential_starts) and ("h8" in potential_starts) and ("f8" in potential_arrivals) and (
                "g8" in potential_arrivals):
            valid_move_string = "e8g8"

        # Detect castling queen side with black
        if ("e8" in potential_starts) and ("a8" in potential_starts) and ("c8" in potential_arrivals) and (
                "d8" in potential_arrivals):
            valid_move_string = "e8c8"

        if valid_move_string:
            return valid_move_string,[]

        if not valid_move_string and len(potential_starts)==2:
            print('premove')
            # problematic is a takes, takes premove

        rest = []
        if len(potential_starts)==2:
            print('premove!!!!')
        for start in potential_starts:
            for arrival in potential_arrivals:
                uci_move = start+arrival
                move = chess.Move.from_uci(uci_move)
                if move in self.board.legal_moves:
                    #problem with premove
                    # if len(potential_starts)<2:
                    #     if self.can_image_correspond_to_chessboard(move,current_chessboard_image):#We only keep the move if the current image looks like this move happenned
                    #         valid_move_string = uci_move
                    valid_move_string = uci_move
                    print("My:" + valid_move_string)
                    rest = []
                    if len(potential_starts) >= 2 or len(potential_arrivals) >= 2:
                        potential_starts = np.delete(potential_starts,np.argwhere(potential_starts == start))
                        # potential_arrivals = np.delete(potential_arrivals,np.argwhere(potential_arrivals == arrival))
                        rest=[potential_starts,potential_arrivals]
                else:
                    uci_move_promoted = uci_move + 'q'
                    promoted_move = chess.Move.from_uci(uci_move_promoted)
                    if promoted_move in self.board.legal_moves:
                        # if self.can_image_correspond_to_chessboard(move,current_chessboard_image):#We only keep the move if the current image looks like this move happenned
                        #     valid_move_string = uci_move_promoted
                        #     print("There has been a promotion to queen")
                        valid_move_string = uci_move_promoted
                        print("There has been a promotion to queen")
                    


        return valid_move_string, rest


    def register_move_if_needed(self):
        new_board = chessboard_detection.get_chessboard(self)
        #
        # info_handler = chess.uci.InfoHandler()
        # self.engine.info_handlers.append(info_handler)
        # self.engine.position(self.board)
        #
        # print(info_handler.info["score"])
        #cv2.imshow('old_image',self.previous_chessboard_image)
        #k = cv2.waitKey(10000)                
        potential_starts, potential_arrivals = get_potential_moves(self.previous_chessboard_image,new_board,self.we_play_white)
        valid_move_string1,rest = self.get_valid_move(potential_starts,potential_arrivals,new_board)
        if rest:
            print('premove to process')
            print("Valid move string 1:" + valid_move_string1)
            if len(valid_move_string1) > 0:
                valid_move_UCI = chess.Move.from_uci(valid_move_string1)
                valid_move_registered = self.register_move(valid_move_UCI,new_board)
                new_board = chessboard_detection.get_chessboard(self)
                potential_starts = rest[0]
                potential_arrivals = rest[1]
                valid_move_string1, rest = self.get_valid_move(potential_starts, potential_arrivals, new_board)
                if len(valid_move_string1) > 0:
                    valid_move_UCI = chess.Move.from_uci(valid_move_string1)
                    valid_move_registered = self.register_move(valid_move_UCI, new_board)

                    return True, valid_move_string1
        else:
            print("Valid move string 1:" + valid_move_string1)

            if len(valid_move_string1) > 0:
                # time.sleep(0.1)
                # 'Check that we were not in the middle of a move animation'
                # new_board = chessboard_detection.get_chessboard(self)
                # potential_starts, potential_arrivals = get_potential_moves(self.previous_chessboard_image,new_board,self.we_play_white)
                # valid_move_string2 = self.get_valid_move(potential_starts,potential_arrivals,new_board)
                # print("Valid move string 2:" + valid_move_string2)
                # if valid_move_string2 != valid_move_string1:
                #     return False, "The move has changed"
                valid_move_UCI = chess.Move.from_uci(valid_move_string1)
                valid_move_registered = self.register_move(valid_move_UCI,new_board)
                return True, valid_move_string1
        return False, "No move found"
    


        

    def register_move(self,move,board_image):
        if move in self.board.legal_moves:
            print("Move has been registered")
            self.executed_moves= np.append(self.executed_moves,self.board.san(move))
            self.board.push(move)
            self.moves_to_detect_before_use_engine  -= 1
            self.previous_chessboard_image = board_image
            return True
        else:
            return False

    def get_square_center(self,square_name):
        row,column = convert_square_name_to_row_column(square_name,self.we_play_white)
        position = self.board_position_on_screen
        centerX = int(position.minX + (column + 0.5) *(position.maxX-position.minX)/8)
        centerY = int(position.minY + (row + 0.5) *(position.maxY-position.minY)/8)
        return centerX,centerY

    def play_next_move(self,factor):
        from random import randint
        from time import sleep

        sleep(randint(1, 500)/1000)
        #This function calculates the next best move with the engine, and play it (by moving the mouse)
        print("\nUs to play: Calculating next move")
        info_handler = chess.uci.InfoHandler()
        self.engine.info_handlers.append(info_handler)
        self.engine.position(self.board)

        engine_process = self.engine.go(movetime=500)#random.randint(200,400))
        print(info_handler.info["score"])
        try:
            print(f"winrate = {1/(1+math.exp(-int(info_handler.info['score'].popitem()[1][0])/650))}")
        except:
            pass
        best_move = engine_process.bestmove
        best_move_string = best_move.uci()
        #print("Play next move")

        #print(bestMove)
        origin_square = best_move_string[0:2]
        destination_square = best_move_string[2:4]
        

        centerXOrigin, centerYOrigin = self.get_square_center(origin_square)
        centerXDest, centerYDest = self.get_square_center(destination_square)
        factor /= 2
        centerXOrigin *= factor
        centerYOrigin *= factor
        centerXDest *= factor
        centerYDest *= factor

        # Having the positions we can drag the piece:
        pyautogui.moveTo(int(centerXOrigin), int(centerYOrigin), 0.01)
        pyautogui.dragTo(int(centerXOrigin), int(centerYOrigin) + 1, button='left',
                         duration=0.01)  # This small click is used to get the focus back on the browser window
        pyautogui.dragTo(int(centerXDest), int(centerYDest), button='left', duration=0.3)

        if best_move.promotion != None:
            print("Promoting to a queen")
            # Deal with queen promotion:
            cv2.waitKey(100)
            pyautogui.dragTo(int(centerXDest), int(centerYDest) + 1, button='left',
                             duration=0.1)  # Always promoting to a queen

        print("Done playing move", origin_square, destination_square)
        # self.previous_chessboard_image = chessboard_detection.get_chessboard(self)
        self.moves_to_detect_before_use_engine = 2
        # self.moves_to_detect_before_use_engine = 2
        return

