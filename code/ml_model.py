
from tensorflow.keras.models import Sequential, load_model
def init():
    model_path = '/Users/sebastiankoch/Downloads/chessbot_python-master 2/model_binary/binarymodel.h5'
    model_weights_path = '/Users/sebastiankoch/Downloads/chessbot_python-master 2/model_binary/binaryweights.hdf5'
    global model
    model = load_model(model_path)
    model.load_weights(model_weights_path)
    # from tensorflow.keras.utils import plot_model
    # plot_model(model, to_file='model.png')