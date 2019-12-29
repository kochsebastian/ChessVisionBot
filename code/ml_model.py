
from tensorflow.keras.models import Sequential, load_model
def init_binary():
    model_path = '/Users/sebastiankoch/OnlineChessBot/model_binary/binarymodel.h5'
    model_weights_path = '/Users/sebastiankoch/OnlineChessBot/model_binary/binaryweights.hdf5'
    global binary_model
    binary_model = load_model(model_path)
    binary_model.load_weights(model_weights_path)
    # from tensorflow.keras.utils import plot_model
    # plot_model(model, to_file='model.png')

def init_class():
    model_path = '/Users/sebastiankoch/OnlineChessBot/model_class/model128.h5'
    model_weights_path = '/Users/sebastiankoch/OnlineChessBot/model_class/weights128.hdf5'
    global class_model
    class_model = load_model(model_path)
    class_model.load_weights(model_weights_path)
    # from tensorflow.keras.utils import plot_model
    # plot_model(model, to_file='model.png')