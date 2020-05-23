import numpy as np
import cv2
import pyautogui
from mss import mss
import os
import glob
from game_state_classes import Game_state
import board_basics
import chessboard_detection



if __name__ == '__main__':
    game_state = Game_state()
    found_chessboard, position  = chessboard_detection.find_chessboard()
    print(position)
    print(found_chessboard)
    game_state.board_position_on_screen = position
    resized_chessboard = chessboard_detection.get_chessboard(game_state)

    for i in range(8):
        for j in range(8):
            image =board_basics.get_square_image(i,j,resized_chessboard)
            cv2.imwrite(f"pieces/{i}{j}.png", image)

