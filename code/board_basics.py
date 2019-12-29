import cv2
import numpy as np
from tensorflow.keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array
import ml_model

def get_square_image(row,column,board_img): #this functions assumes that there are 8*8 squares in the image, and that it is grayscale
    height, width = board_img.shape
    minX =  int(column * width / 8 ) 
    maxX = int((column + 1) * width / 8 )
    minY = int(row * width / 8 )
    maxY = int((row + 1) * width / 8 )
    square = board_img[minY:maxY, minX:maxX]
    square_without_borders = square[3:-3, 3:-3]
    # cv2.imshow('test',square_without_borders)
    # cv2.waitKey(0)
    return square_without_borders

def convert_row_column_to_square_name(row,column, is_white_on_bottom):
    if is_white_on_bottom == True:
        number = repr(8 - row)
        letter = str(chr(97 + column))
        return letter+number
    else:
        number = repr(row + 1)
        letter = str(chr(97 + (7 - column)))
        return letter+number

def convert_square_name_to_row_column(square_name,is_white_on_bottom): #Could be optimized
    #print("Looking for " + repr(square_name))
    for row in range(8):
        for column in range(8):
            this_square_name = convert_row_column_to_square_name(row,column,is_white_on_bottom)
            #print(this_square_name)
            if  this_square_name == square_name:
                return row,column
    return 0,0

def get_square_center_from_image_and_move(square_name, is_white_on_bottom , minX,minY,maxX,maxY):
    row,column = convert_square_name_to_row_column(square_name,is_white_on_bottom)
    
    centerX = int(minX + (column + 0.5) *(maxX-minX)/8)
    centerY = int(minY + (row + 0.5) *(maxY-minY)/8)
    return centerX,centerY

#Basic operation with square images:
def has_square_image_changed(old_square, new_square,coord):#If there has been a change -> the image difference will be non null -> the average intensity will be > treshold

    # pre = is_square_empty(old_square)
    # post = is_square_empty(new_square)
    # if pre == True and post == True:
    #     return False
    diff = cv2.absdiff(old_square,new_square)
    # print(f"{coord}: {diff.mean()}")
    if diff.mean() > 2: #8 works pretty nicely but would require optimization
        return True
    else:
        return False
    # if coord == (5,5):
    #     print()
    # a=img_to_array(cv2.cvtColor(cv2.resize(old_square, (32, 32)), cv2.COLOR_GRAY2RGB))
    # b=img_to_array(cv2.cvtColor(cv2.resize(new_square, (32, 32)), cv2.COLOR_GRAY2RGB))
    # x = np.stack((a, b),axis=0)
    # array = ml_model.model.predict(x)
    # result = array
    # answer = [np.argmax(result[0]),np.argmax(result[1])]
    # # print(answer[0]==answer[1])
    # return not answer[0]==answer[1]


def is_square_empty(square): # A square is empty if its pixels have no variations
    # square,factor = chessboard_detection.image_resize(square,90)
    square = cv2.cvtColor(square, cv2.COLOR_GRAY2RGB)

    # square, factor = chessboard_detection.image_resize(square, 90,90)
    # square = chessboard_detection.image_square(square,90)
    square = cv2.resize(square,(32,32))
    x = square
    x = img_to_array(x)
    x = np.expand_dims(x, axis=0)
    array = ml_model.binary_model.predict(x)
    result = array[0]
    answer = np.argmax(result)
    if answer == 0:
        return True
    else:
        return False
    # return square.std() < 10 # 10 works pretty well -> the mouse pointer is not enought to disturb (but sometimes it actually does, especially with small chessboards and big pointer)

def piece_on_square(square):
    square = cv2.cvtColor(square, cv2.COLOR_GRAY2RGB)
    square = cv2.resize(square,(128,128))
    x = square
    x = img_to_array(x)
    x = np.expand_dims(x, axis=0)
    array = ml_model.class_model.predict(x)
    result = array[0]
    answer = np.argmax(result)
    return answer

def is_white_on_bottom(current_chessboard_image):
    #This functions compares the mean intensity from two squares that have the same background (opposite corners) but different pieces on it.
    #The one brighter one must be white
    m1 = get_square_image(0,0,current_chessboard_image).mean() #Rook on the top left
    m2 = get_square_image(7,7,current_chessboard_image).mean() #Rook on the bottom right
    if m1 < m2: #If the top is darker than the bottom
        return True
    else:
        return False


#This function goes over every square, check if it moves, and detect if the square emptiness on the old vs new
#If the square had a piece previously -> it is a potential starting point
#If the square has a piece now -> it is a potential arrival
def get_potential_moves(old_image,new_image,is_white_on_bottom):
    
    diff = abs(old_image - new_image)
    numpy_horizontal = np.vstack((old_image, new_image, diff))
    image = cv2.resize(numpy_horizontal, (200, 600))
    # winname = "both"
    # cv2.namedWindow(winname)  # Create a named window
    # cv2.moveWindow(winname, 1100, 200)  # Move it to (40,30)
    # cv2.imshow(winname, image)
    # # cv2.resizeWindow(winname, 50, 50)
    # cv2.waitKey(500)
    # cv2.destroyAllWindows()
    # update_ui(image)
    potential_starts = []
    potential_arrivals = []
    for row in range(8):
        #print("\nRow",row,"")
        for column in range(8):
            old_square = get_square_image(row,column,old_image)
            new_square = get_square_image(row,column,new_image)
            if has_square_image_changed(old_square, new_square,(row,column)):
                square_name = convert_row_column_to_square_name(row,column,is_white_on_bottom)
                if square_name =='e4':
                    print()
                square_was_empty = is_square_empty(old_square)
                square_is_empty = is_square_empty(new_square)
                if square_was_empty == False:# and square_is_empty == True:
                    potential_starts = np.append(potential_starts,square_name)
                if square_is_empty == False:
                    potential_arrivals = np.append(potential_arrivals,square_name)
    return potential_starts, potential_arrivals

