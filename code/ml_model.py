
from tensorflow.keras.models import Sequential, load_model
def init_binary():
    model_path = '/Users/sebastiankoch/Downloads/chessbot_python-master 2/model_binary/binarymodel.h5'
    model_weights_path = '/Users/sebastiankoch/Downloads/chessbot_python-master 2/model_binary/binaryweights.hdf5'
    global model
    model = load_model(model_path)
    model.load_weights(model_weights_path)
    # from tensorflow.keras.utils import plot_model
    # plot_model(model, to_file='model.png')

def init_class():
    model_path = '/Users/sebastiankoch/Downloads/chessbot_python-master 2/model_class/model.h5'
    model_weights_path = '/Users/sebastiankoch/Downloads/chessbot_python-master 2/model_class/epoch-018_acc-0.9999.hdf5'
    global model
    model = load_model(model_path)
    model.load_weights(model_weights_path)
    # from tensorflow.keras.utils import plot_model
    # plot_model(model, to_file='model.png')