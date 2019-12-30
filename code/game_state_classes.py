import chess
import chess.uci
import numpy as np
from board_basics import *
import chessboard_detection
import pyautogui
import cv2
import mss
import math
from random import randint
from time import sleep
import copy
import os

class NoValidPosition(Exception):

   pass
class PositionChanged(Exception):

   pass


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
        self.engine = chess.uci.popen_engine("/Users/sebastiankoch/OnlineChessBot/engine/stockfish-10-64")
        self.board = chess.Board() #This object comes from the "chess" package, the moves are stored inside it (and it has other cool features such as showing all the "legal moves")
        self.board_position_on_screen = []
        self.sct = mss.mss()

    def check_for_castling(self,potential_starts, potential_arrivals):
        valid_move_string = ""
        # Detect castling king side with white
        if ("e1" in potential_starts) and ("h1" in potential_starts) and ("f1" in potential_arrivals) and (
                "g1" in potential_arrivals):
            valid_move_string = "e1g1"
            potential_starts = np.delete(potential_starts,np.argwhere(potential_starts == "e1"))
            potential_starts = np.delete(potential_starts,np.argwhere(potential_starts == "f1"))

        # Detect castling queen side with white
        if ("e1" in potential_starts) and ("a1" in potential_starts) and ("c1" in potential_arrivals) and (
                "d1" in potential_arrivals):
            valid_move_string = "e1c1"
            potential_starts = np.delete(potential_starts,np.argwhere(potential_starts == "e1"))
            potential_starts = np.delete(potential_starts,np.argwhere(potential_starts == "c1"))

        # Detect castling king side with black
        if ("e8" in potential_starts) and ("h8" in potential_starts) and ("f8" in potential_arrivals) and (
                "g8" in potential_arrivals):
            valid_move_string = "e8g8"
            potential_starts = np.delete(potential_starts,np.argwhere(potential_starts == "e8"))
            potential_starts = np.delete(potential_starts,np.argwhere(potential_starts == "f8"))

        # Detect castling queen side with black
        if ("e8" in potential_starts) and ("a8" in potential_starts) and ("c8" in potential_arrivals) and (
                "d8" in potential_arrivals):
            valid_move_string = "e8c8"
            potential_starts = np.delete(potential_starts,np.argwhere(potential_starts == "e8" ))
            potential_starts = np.delete(potential_starts,np.argwhere(potential_starts == "c8"))
        
        return valid_move_string,potential_starts

    def get_valid_move(self, potential_starts, potential_arrivals, current_chessboard_image):

        print("Starts and arrivals:",potential_starts, potential_arrivals)
        if len( potential_arrivals)==0 and len(potential_starts)==0:
            return "",[]

        valid_move_string,potential_starts = self.check_for_castling(potential_starts, potential_arrivals)
        
        if valid_move_string:
            return valid_move_string,[potential_starts,potential_arrivals]

        if not valid_move_string and len(potential_starts)==2:
            print('premove')
            # problematic is a takes, takes premove

        rest = []
        # if len(list(self.board.generate_legal_captures()))>0:
        #     legal_moves=list(self.board.generate_legal_captures())
        #     [print(chess.Move.uci(lm)) for lm in legal_moves]
            
        #     move_arrival=[lm[:-2] for lm in legal_moves] 
        if len(potential_starts)==2:
            print('premove!!!!')
        if len(potential_starts)==2 and len(potential_arrivals)==0:
            print('recapture with same piece')

            capture_moves_own=list(self.board.generate_legal_captures())
            for move in capture_moves_own:
                if chess.Move.uci(move)[:2] == potential_starts[0] or chess.Move.uci(move)[:2] == potential_starts[1]:
                    self.board.push(move)
                    capture_moves_opponent = list(self.board.generate_legal_captures())
                    for move_opp in capture_moves_opponent:
                        if chess.Move.uci(move_opp)[:2] == potential_starts[0] or chess.Move.uci(move_opp)[:2] == potential_starts[1]:
                            self.board.pop()
                            potential_arrivals.append(chess.Move.uci(move)[-2:])



        for start in potential_starts:
            for arrival in potential_arrivals:
                uci_move = start+arrival
                move = chess.Move.from_uci(uci_move)
                if move in self.board.legal_moves:
                    valid_move_string = uci_move
                    print(valid_move_string)
                    rest = []
                    if len(potential_starts) >= 2 or len(potential_arrivals) >= 2:
                        potential_starts = np.delete(potential_starts,np.argwhere(potential_starts == start))
                        rest = [potential_starts,potential_arrivals]
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
        # sleep(randint(200,300)/1000)
        new_board = chessboard_detection.get_chessboard(self)        
        old_board = self.previous_chessboard_image
        potential_starts, potential_arrivals = get_potential_moves(self.previous_chessboard_image,new_board,self.we_play_white)
        if len(potential_starts)>6 or len(potential_arrivals)>6:
            self.previous_chessboard_image=new_board
            print(potential_starts)
            print(potential_arrivals)
            potential_starts=[]
            potential_arrivals=[]
            raise PositionChanged
            # pass
        valid_move_string1, rest = self.get_valid_move(potential_starts,potential_arrivals,new_board)
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

                    return True, valid_move_string1,(old_board,new_board)
        else:
            print("Valid move string 1:" + valid_move_string1)
            if len(valid_move_string1) > 0:
                valid_move_UCI = chess.Move.from_uci(valid_move_string1)
                valid_move_registered = self.register_move(valid_move_UCI,new_board)
                return True, valid_move_string1,(old_board,new_board)
        return False, "No move found",(old_board,new_board)
    


        

    def register_move(self,move,board_image):
        if move in self.board.legal_moves:
            print("Move has been registered")
            self.executed_moves = np.append(self.executed_moves,self.board.san(move))
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

    def play_next_move(self,factor,strength,variance):
        
        score = 0
        winrate = 0
        # sleep(randint(1, variance)/1000)
        #This function calculates the next best move with the engine, and play it (by moving the mouse)
        print("\nUs to play: Calculating next move")
        info_handler = chess.uci.InfoHandler()
        self.engine.info_handlers.append(info_handler)
        self.engine.position(self.board)

        try:
            if strength<=2000:
                engine_process = self.engine.go(movetime=100)#(strength+(randint(1, variance)/1000)))
            else:
                engine_process = self.engine.go(depth=20)#
        except chess.engine.EngineTerminatedException:
            self.engine = chess.uci.popen_engine("/Users/sebastiankoch/OnlineChessBot/engine/stockfish-10-64")

        
        score = copy.deepcopy(info_handler.info["score"])
        try:
            winrate = 1/(1+math.exp(-int(info_handler.info['score'].popitem()[1][0])/650))
            print(f"winrate = {winrate}")
            
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
        # new_board = chessboard_detection.get_chessboard(self)  
        # self.register_move(best_move,self.previous_chessboard_image)
        # self.moves_to_detect_before_use_engine = 1
        self.moves_to_detect_before_use_engine = 2
        return score, winrate


    def build_fen(self,we_are_white,rochade = 'KQkq' ):
        position_detection = chessboard_detection.get_chessboard(self, (800, 800))
        # cv2.imshow('dsd',position_detection)
        # cv2.waitKey(0)
        #   board_basics.is_white_on_bottom(position_detection)
        self.we_play_white = we_are_white

        to_move = 'w' if we_are_white else 'b'

        self.moves_to_detect_before_use_engine = 0  # if v.get() else 1

        pieces = sorted(os.listdir('/Users/sebastiankoch/OnlineChessBot/pieces'))

        vis_glob = np.array([])
        piece_notation = ['b', 'k', 'n', 'p', 'q', 'r', '*', 'B', 'K', 'N', 'P', 'Q', 'R']
        fen_str = ''

        # rochade = 'KQkq'
        en_passant = '-'
        halfmoves = '0'
        move = '1'

        order = range(8) if we_are_white else reversed(range(8))
        for i in order:
            vis = np.array([])

            image_list = [get_square_image(i, j, position_detection) for j in (range(8) if we_are_white else reversed(range(8)))]
            answers = piece_on_square_list(image_list)
            for answer in answers:
            # order2 = range(8) if we_are_white else reversed(range(8))
            # for j in order2:
            #     image = get_square_image(i, j, position_detection)
            #     answer = piece_on_square(image)
                im = cv2.imread(os.path.join('/Users/sebastiankoch/OnlineChessBot/pieces', pieces[answer]))
                if vis.size == 0:
                    vis = im
                    fen_str += piece_notation[answer]
                else:
                    if we_are_white:
                        vis = np.concatenate((vis,im), axis=1)
                    else:
                        vis = np.concatenate((im, vis), axis=1)
                    fen_str += piece_notation[answer]

            fen_str += '/'
            if vis_glob.size == 0:
                vis_glob = vis
            else:
                if we_are_white:
                    vis_glob = np.concatenate(( vis_glob,vis), axis=0)
                else:
                    vis_glob = np.concatenate((vis, vis_glob), axis=0)
        fen_str = fen_str[:-1] + ' ' + to_move + ' ' + rochade + ' ' + en_passant + ' ' + halfmoves + ' ' + move

        for i in range(len(fen_str)):
            if fen_str[i] == ' ':
                break
            count = 0
            if fen_str[i] == '*':
                while fen_str[i] == '*':
                    count += 1

                    fen_str = fen_str[0: i:] + fen_str[i + 1::]
                fen_str = fen_str[:i] + str(count) + fen_str[i:]
        # print(fen_str)
        return fen_str,vis_glob

    def our_side(self):
        # TODO use pawns to get side
        position_detection = chessboard_detection.get_chessboard(self, (800, 800))
        piece_notation = ['b', 'k', 'n', 'p', 'q', 'r', '*', 'B', 'K', 'N', 'P', 'Q', 'R']

        black_king_position=()
        white_king_position = ()
        order = range(8)
        for i in order:
            vis = np.array([])
            order2 = range(8)
            image_list = [get_square_image(i, j, position_detection) for j in range(8)]
            answers = piece_on_square_list(image_list)
            if piece_notation.index('k') in answers:
                black_king_position = (i, 0)
            if piece_notation.index('K') in answers:
                white_king_position= (i,0)
            # for j in order2:
            #     image = get_square_image(i, j, position_detection)
            #     answer = piece_on_square(image)
            #     if  piece_notation[answer] == 'k':
            #         black_king_position = (i,j)
            #     if  piece_notation[answer] == 'K':
            #         white_king_position = (i,j)

        if not white_king_position or not black_king_position:
            raise NoValidPosition
        if black_king_position[0]<white_king_position[0]:
            return 'white'
        elif black_king_position[0]>white_king_position[0]:
            return 'black'
        else:
            return 'unsure'