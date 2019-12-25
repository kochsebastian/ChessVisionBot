import numpy as np
import cv2
import pyautogui
from mss import mss
import os
import glob
import game_state_classes


def image_square(im,desired_size):

    old_size = im.shape[:2]  # old_size is in (height, width) format

    ratio = float(desired_size) / max(old_size)
    new_size = tuple([int(x * ratio) for x in old_size])

    # new_size should be in (width, height) format

    im = cv2.resize(im, (new_size[1], new_size[0]))

    delta_w = desired_size - new_size[1]
    delta_h = desired_size - new_size[0]
    top, bottom = delta_h // 2, delta_h - (delta_h // 2)
    left, right = delta_w // 2, delta_w - (delta_w // 2)

    color = [0, 0, 0]
    new_im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT,
                                value=color)
    return new_im


def image_resize(image, width = None, height = None, inter = cv2.INTER_AREA):
    # initialize the dimensions of the image to be resized and
    # grab the image size
    dim = None
    (h, w) = image.shape[:2]
    factor = w/width
    # if both the width and height are None, then return the
    # original image
    if width is None and height is None:
        return image

    # check to see if the width is None
    if width is None:
        # calculate the ratio of the height and construct the
        # dimensions
        r = height / float(h)
        dim = (int(w * r), height)

    # otherwise, the height is None
    else:
        # calculate the ratio of the width and construct the
        # dimensions
        r = width / float(w)
        dim = (width, int(h * r))

    # resize the image
    resized = cv2.resize(image, dim, interpolation = inter)

    # return the resized image
    return resized, factor

def find_chessboard():
    img = pyautogui.screenshot()
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    factor=1
    img, factor = image_resize(img, 800)
    # cv2.imshow('test', img)
    # cv2.imwrite('testim.png',img)
    # cv2.waitKey(0)
    gray = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
    is_found, current_chessboard_image,minX,minY,maxX,maxY,test_image = find_chessboard_from_image(img)
    position = game_state_classes.Board_position(minX,minY,maxX,maxY,factor)
    # cv2.imshow('test',current_chessboard_image)
    # cv2.waitKey(0)
    return is_found, position

def get_chessboard(game_state):
    position = game_state.board_position_on_screen
    factor = position.factor
    factor/=2
    # factor=1
    x1 = position.minX * (factor)
    y1 = position.minY * (factor)
    x2 = position.maxX * (factor)
    y2 = position.maxY * (factor)
    img = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
    with mss() as sct:
        monitor = {'top': y1+1, 'left': x1+1, 'width': x2-x1-2 , 'height': (y2-y1)}
        img = np.array(np.array(sct.grab(monitor)))
    # img, factor = image_resize(img, 800)
    # cv2.imwrite('testim2.png', img)
    # cv2.imshow('test',img)
    # cv2.waitKey(0)
    # img = np.array(img)
    #Converting the image in grayscale:
    image = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)


    # resizedChessBoard = cv2.resize(image[position.minY:position.maxY, position.minX:position.maxX], dim, interpolation = cv2.INTER_AREA)
    # resizedChessBoard, factor = image_resize(image,600)
    resizedChessBoard = cv2.resize(image,(400,400))
    return resizedChessBoard

def find_chessboard_from_image(img):
    image = cv2.GaussianBlur(img, (3, 3), 0)
    # img = cv.GaussianBlur(img, (5, 5), 0)
    # bilateral_filtered_image = cv.bilateralFilter(img, 5, 175, 175)
    squares = []
    for gray in cv2.split(img):
        for thrs in range(0, 255, 1):
            # thrs = 0
            if thrs == 0:
                bin = cv2.Canny(gray, 0, 1)
                bin = cv2.dilate(bin, None)
            else:
                _retval, bin = cv2.threshold(gray, thrs, 255, cv2.THRESH_BINARY)
            bin, contours, _hierarchy = cv2.findContours(bin, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True)

                if ((len(approx) == 4)) and cv2.contourArea(contour) > 1000:  # cv2.isContourConvex(contour)
                    (x, y, w, h) = cv2.boundingRect(approx)
                    if not ((float(w) / h) < 0.995 or (float(w) / h) > 1.005):
                        squares.append(contour)
    minX = 10000000
    minY = 100000000
    maxX = -1
    maxY = -1
    for square in squares:
        x, y, w, h = cv2.boundingRect(square)
        minX = x if x < minX else minX
        minY = y if y < minY else minY
        maxX = x + w if x + w > maxX else maxX
        maxY = y + h if y + h > maxY else maxY
    # cv2.drawContours(img, squares, -1, (0, 255, 0), 3)
    # cv2.rectangle(img, (minX, minY), (maxX, maxY), (0, 0, 255), 3)
    # cv2.imshow('test',img)
    # cv2.waitKey(0)
    return True, img, minX, minY, maxX, maxY, img

