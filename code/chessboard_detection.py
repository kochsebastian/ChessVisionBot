import numpy as np
import cv2
import pyautogui
from mss import mss
import os
import glob
import game_state_classes
from random import randint
from time import sleep
import tensorflow as tf
import scipy.ndimage as nd
import scipy.signal
import PIL.Image


def image_square(im,desired_size):

    old_size = im.shape[:2]  # old_size is in (height, width) format

    ratio = float(desired_size) / max(old_size)
    new_size = tuple([int(x * ratio) for x in old_size])

    # new_size should be in (width, height) format

    im = cv2.resize(im, (new_size[1], new_size[0]),interpolation=cv2.INTER_CUBIC)

    delta_w = desired_size - new_size[1]
    delta_h = desired_size - new_size[0]
    top, bottom = delta_h // 2, delta_h - (delta_h // 2)
    left, right = delta_w // 2, delta_w - (delta_w // 2)

    color = [0, 0, 0]
    new_im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT,
                                value=color)
    return new_im


def image_resize(image, width = None, height = None, inter = cv2.INTER_CUBIC):
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
    # pyautogui.os.chmod('screencapture/',777)
    img = pyautogui.screenshot()
    # img = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
    # cv2.imshow('test',img)
    # cv2.waitKey(0)
    factor=1
    img = cv2.cvtColor(np.asarray(img), cv2.COLOR_BGR2RGB)

    # # Resize if image larger than 2k pixels on a side
    # if img.shape[1] > 2000 or img.shape[0] > 2000:
    #     print(f"Image too big ({img.shape[1]} x {img.shape[0]})")
    #     new_size = 1600.0  # px
    #     if img.shape[1] > img.shape[0]:
    #         # resize by width to new limit
    #         ratio = new_size / img.shape[1]
    #
    #     else:
    #         # resize by height
    #         ratio = new_size / img.shape[0]
    #     print(f"Reducing by factor of {(1./ratio)}")
    #     img = cv2.resize(img, (0, 0), fx=ratio, fy=ratio)
    #     print(f"New size: ({img.shape[1]} x {img.shape[0]})")
    img, factor = image_resize(img, 1000)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = np.asarray(gray, dtype=np.float32)
    is_found, current_chessboard_image,minX,minY,maxX,maxY,test_image = find_chessboard_from_image(gray)
    position = game_state_classes.Board_position(minX,minY,maxX,maxY,factor)

    return is_found, position

def get_chessboard(game_state,resolution=(200,200)):
    position = game_state.board_position_on_screen
    factor = position.factor
    factor/=2
    # factor=1
    x1 = position.minX * (factor)
    y1 = position.minY * (factor)
    x2 = position.maxX * (factor)
    y2 = position.maxY * (factor)
    # img = np.array(pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1)))
    # sleep(200 / 1000)
    with mss() as sct:
        monitor = {'top': y1+1, 'left': x1+1, 'width': x2-x1-2 , 'height': (y2-y1)}
        img = np.array(sct.grab(monitor))
    image = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)

    resizedChessBoard = cv2.resize(image,resolution,interpolation=cv2.INTER_CUBIC)
    return resizedChessBoard

def find_chessboard_from_image1(img):
    image = cv2.GaussianBlur(img, (3, 3), 0)
    # img = cv.GaussianBlur(img, (5, 5), 0)
    # bilateral_filtered_image = cv.bilateralFilter(img, 5, 175, 175)
    squares = []
    for gray in cv2.split(img):
        for thrs in range(0, 255, 5):
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

    return True, img, minX, minY, maxX, maxY, img


def find_chessboard_from_image(img_arr_gray, noise_threshold = 8000):
  # Load image grayscale as an numpy array
  # Return None on failure to find a chessboard
  #
  # noise_threshold: Ratio of standard deviation of hough values along an axis
  # versus the number of pixels, manually measured  bad trigger images
  # at < 5,000 and good  chessboards values at > 10,000

  # Get gradients, split into positive and inverted negative components 
  # img_arr_gray = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
  gx, gy = np.gradient(img_arr_gray)
  gx_pos = gx.copy()
  gx_pos[gx_pos<0] = 0
  gx_neg = -gx.copy()
  gx_neg[gx_neg<0] = 0

  gy_pos = gy.copy()
  gy_pos[gy_pos<0] = 0
  gy_neg = -gy.copy()
  gy_neg[gy_neg<0] = 0

  # 1-D ampltitude of hough transform of gradients about X & Y axes
  num_px = img_arr_gray.shape[0] * img_arr_gray.shape[1]
  hough_gx = gx_pos.sum(axis=1) * gx_neg.sum(axis=1)
  hough_gy = gy_pos.sum(axis=0) * gy_neg.sum(axis=0)

  # Check that gradient peak signal is strong enough by
  # comparing normalized standard deviation to threshold
  if min(hough_gx.std() / hough_gx.size,
         hough_gy.std() / hough_gy.size) < noise_threshold:
    return None
  
  # Normalize and skeletonize to just local peaks
  hough_gx = nonmax_suppress_1d(hough_gx) / hough_gx.max()
  hough_gy = nonmax_suppress_1d(hough_gy) / hough_gy.max()

  # Arbitrary threshold of 20% of max
  hough_gx[hough_gx<0.2] = 0
  hough_gy[hough_gy<0.2] = 0

  # Now we have a set of potential vertical and horizontal lines that
  # may contain some noisy readings, try different subsets of them with
  # consistent spacing until we get a set of 7, choose strongest set of 7
  pot_lines_x = np.where(hough_gx)[0]
  pot_lines_y = np.where(hough_gy)[0]
  pot_lines_x_vals = hough_gx[pot_lines_x]
  pot_lines_y_vals = hough_gy[pot_lines_y]

  # Get all possible length 7+ sequences
  seqs_x = getAllSequences(pot_lines_x)
  seqs_y = getAllSequences(pot_lines_y)
  
  if len(seqs_x) == 0 or len(seqs_y) == 0:
    return None
  
  # Score sequences by the strength of their hough peaks
  seqs_x_vals = [pot_lines_x_vals[[v in seq for v in pot_lines_x]] for seq in seqs_x]
  seqs_y_vals = [pot_lines_y_vals[[v in seq for v in pot_lines_y]] for seq in seqs_y]

  # shorten sequences to up to 9 values based on score
  # X sequences
  for i in range(len(seqs_x)):
    seq = seqs_x[i]
    seq_val = seqs_x_vals[i]

    # if the length of sequence is more than 7 + edges = 9
    # strip weakest edges 
    if len(seq) > 9:
      # while not inner 7 chess lines, strip weakest edges
      while len(seq) > 7:
        if seq_val[0] > seq_val[-1]:
          seq = seq[:-1]
          seq_val = seq_val[:-1]
        else:
          seq = seq[1:]
          seq_val = seq_val[1:]

    seqs_x[i] = seq
    seqs_x_vals[i] = seq_val

  # Y sequences
  for i in range(len(seqs_y)):
    seq = seqs_y[i]
    seq_val = seqs_y_vals[i]

    while len(seq) > 9:
      if seq_val[0] > seq_val[-1]:
        seq = seq[:-1]
        seq_val = seq_val[:-1]
      else:
        seq = seq[1:]
        seq_val = seq_val[1:]

    seqs_y[i] = seq
    seqs_y_vals[i] = seq_val

  # Now that we only have length 7-9 sequences, score and choose the best one
  scores_x = np.array([np.mean(v) for v in seqs_x_vals])
  scores_y = np.array([np.mean(v) for v in seqs_y_vals])

  # Keep first sequence with the largest step size
  # scores_x = np.array([np.median(np.diff(s)) for s in seqs_x])
  # scores_y = np.array([np.median(np.diff(s)) for s in seqs_y])

  #TODO(elucidation): Choose heuristic score between step size and hough response

  best_seq_x = seqs_x[scores_x.argmax()]
  best_seq_y = seqs_y[scores_y.argmax()]
  # print(best_seq_x, best_seq_y)

  # Now if we have sequences greater than length 7, (up to 9),
  # that means we have up to 9 possible combinations of sets of 7 sequences
  # We try all of them and see which has the best checkerboard response
  sub_seqs_x = [best_seq_x[k:k+7] for k in range(len(best_seq_x) - 7 + 1)]
  sub_seqs_y = [best_seq_y[k:k+7] for k in range(len(best_seq_y) - 7 + 1)]

  dx = np.median(np.diff(best_seq_x))
  dy = np.median(np.diff(best_seq_y))
  corners = np.zeros(4, dtype=int)
  
  # Add 1 buffer to include the outer tiles, since sequences are only using
  # inner chessboard lines
  corners[0] = int(best_seq_y[0]-dy)
  corners[1] = int(best_seq_x[0]-dx)
  corners[2] = int(best_seq_y[-1]+dy)
  corners[3] = int(best_seq_x[-1]+dx)

  # Generate crop image with on full sequence, which may be wider than a normal
  # chessboard by an extra 2 tiles, we'll iterate over all combinations
  # (up to 9) and choose the one that correlates best with a chessboard
  gray_img_crop = PIL.Image.fromarray(img_arr_gray).crop(corners)

  # Build a kernel image of an idea chessboard to correlate against
  k = 8 # Arbitrarily chose 8x8 pixel tiles for correlation image
  quad = np.ones([k,k])
  kernel = np.vstack([np.hstack([quad,-quad]), np.hstack([-quad,quad])])
  kernel = np.tile(kernel,(4,4)) # Becomes an 8x8 alternating grid (chessboard)
  kernel = kernel/np.linalg.norm(kernel) # normalize
  # 8*8 = 64x64 pixel ideal chessboard

  k = 0
  n = max(len(sub_seqs_x), len(sub_seqs_y))
  final_corners = None
  best_score = None

  # Iterate over all possible combinations of sub sequences and keep the corners
  # with the best correlation response to the ideal 64x64px chessboard
  for i in range(len(sub_seqs_x)):
    for j in range(len(sub_seqs_y)):
      k = k + 1
      
      # [y, x, y, x]
      sub_corners = np.array([
        sub_seqs_y[j][0]-corners[0]-dy, sub_seqs_x[i][0]-corners[1]-dx,
        sub_seqs_y[j][-1]-corners[0]+dy, sub_seqs_x[i][-1]-corners[1]+dx],
        dtype=np.int)

      # Generate crop candidate, nearest pixel is fine for correlation check
      sub_img = gray_img_crop.crop(sub_corners).resize((64,64)) 

      # Perform correlation score, keep running best corners as our final output
      # Use absolute since it's possible board is rotated 90 deg
      score = np.abs(np.sum(kernel * sub_img))
      if best_score is None or score > best_score:
        best_score = score
        final_corners = sub_corners + [corners[0], corners[1], corners[0], corners[1]]

  # print(final_corners)
  return True, img_arr_gray, final_corners[0],final_corners[1], final_corners[2], final_corners[3], img_arr_gray
#   final_corners

def nonmax_suppress_1d(arr, winsize=5):
    """Return 1d array with only peaks, use neighborhood window of winsize px"""
    _arr = arr.copy()

    for i in range(_arr.size):
        if i == 0:
            left_neighborhood = 0
        else:
            left_neighborhood = arr[max(0,i-winsize):i]
        if i >= _arr.size-2:
            right_neighborhood = 0
        else:
            right_neighborhood = arr[i+1:min(arr.size-1,i+winsize)]

        if arr[i] < np.max(left_neighborhood) or arr[i] <= np.max(right_neighborhood):
            _arr[i] = 0
    return _arr


def getAllSequences(seq, min_seq_len=7, err_px=5):
    """Given sequence of increasing numbers, get all sequences with common
    spacing (within err_px) that contain at least min_seq_len values"""

    # Sanity check that there are enough values to satisfy
    if len(seq) < min_seq_len:
        return []

    # For every value, take the next value and see how many times we can step
    # that falls on another value within err_px points
    seqs = []
    for i in range(len(seq) - 1):
        for j in range(i + 1, len(seq)):
            # Check that seq[i], seq[j] not already in previous sequences
            duplicate = False
            for prev_seq in seqs:
                for k in range(len(prev_seq) - 1):
                    if seq[i] == prev_seq[k] and seq[j] == prev_seq[k + 1]:
                        duplicate = True
            if duplicate:
                continue
            d = seq[j] - seq[i]

            # Ignore two points that are within error bounds of each other
            if d < err_px:
                continue

            s = [seq[i], seq[j]]
            n = s[-1] + d
            while np.abs((seq - n)).min() < err_px:
                n = seq[np.abs((seq - n)).argmin()]
                s.append(n)
                n = s[-1] + d

            if len(s) >= min_seq_len:
                s = np.array(s)
                seqs.append(s)
    return seqs
