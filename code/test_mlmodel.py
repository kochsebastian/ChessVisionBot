
import cv2
import os
import numpy as np
from tensorflow.keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array
import ml_model

if __name__ == '__main__':

    ml_model.init_binary()
    squares=os.listdir('pieces')
    for name in squares:
        square= cv2.imread(os.path.join('pieces',name),0)
        # square = cv2.resize(square,(32,32))
        square = cv2.resize(square,(32,32))

        x = cv2.cvtColor(square, cv2.COLOR_GRAY2RGB)

        x = img_to_array(x)
        x = np.expand_dims(x, axis=0)
        array = ml_model.binary_model.predict(x)
        result = array[0]
        answer = np.argmax(result)
        print(f"{name}:  {answer}")