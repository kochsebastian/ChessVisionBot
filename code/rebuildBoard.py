import numpy as np
import cv2
import pyautogui
from mss import mss
import os
import glob
from game_state_classes import Game_state
import board_basics
import chessboard_detection
import ml_model
import chess
import copy

if __name__ == '__main__':
    ml_model.init_class()
    game_state = Game_state()
    # game_state.board.set_fen('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
    
    found_chessboard, position  = chessboard_detection.find_chessboard()
    print(position)
    print(found_chessboard)
    game_state.board_position_on_screen = position
    resized_chessboard = chessboard_detection.get_chessboard(game_state,(800,800))
    # cv2.imshow('test',resized_chessboard)
    # cv2.waitKey(0)
    pieces = sorted(os.listdir('/Users/sebastiankoch/OnlineChessBot/pieces'))
    vis = np.array([])
    vis_glob = np.array([])
    piece_notation =['b','k','n','p','q','r','*','B','K','N','P','Q','R']
    fen_str=''
    to_move ='w'
    rochade ='-'
    en_passant='-'
    halfmoves='0'
    move='1'

    for i in range(8):
        vis = np.array([])
        for j in range(8):
            image = board_basics.get_square_image(i,j,resized_chessboard)
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
    print(game_state.board)
    score = 0
    winrate = 0
    print("\nUs to play: Calculating next move")
    info_handler = chess.uci.InfoHandler()
    game_state.engine.info_handlers.append(info_handler)
    game_state.engine.position(game_state.board)

    engine_process = game_state.engine.go(depth=20)
    
    score = copy.deepcopy(info_handler.info["score"])
    try:
        winrate = 1/(1+math.exp(-int(info_handler.info['score'].popitem()[1][0])/650))
        print(f"winrate = {winrate}")
    except:
        pass
    best_move = engine_process.bestmove
    best_move_string = best_move.uci()
    print(best_move_string)
    # cv2.imshow('col', vis_glob)
    # cv2.waitKey(0)
