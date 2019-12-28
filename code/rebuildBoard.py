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


if __name__ == '__main__':
    ml_model.init_class()
    game_state = Game_state()
    found_chessboard, position  = chessboard_detection.find_chessboard()
    print(position)
    print(found_chessboard)
    game_state.board_position_on_screen = position
    resized_chessboard = chessboard_detection.get_chessboard(game_state)
    pieces = sorted(os.listdir('/Users/sebastiankoch/OnlineChessBot/pieces'))
    vis = np.array([])
    vis_glob = np.array([])

    for i in range(8):
        vis = np.array([])
        for j in range(8):
            image = board_basics.get_square_image(i,j,resized_chessboard)
            answer = board_basics.piece_on_square(image)
            im = cv2.imread(os.path.join('/Users/sebastiankoch/OnlineChessBot/pieces',pieces[answer]))
            if vis.size==0:
                vis=im
            else:
                vis = np.concatenate((vis, im), axis=1)
            # cv2.imshow('row',vis)
            # cv2.waitKey(250)
        if vis_glob.size ==0:
            vis_glob = vis
        else:
            vis_glob = np.concatenate((vis_glob, vis), axis=0)
        # cv2.imshow('col', vis_glob)
        # cv2.waitKey(250)
    cv2.imshow('col', vis_glob)
    cv2.waitKey(0)