"""
@author: Vincent Bonnet
@description : Class to load the MNIST database into numpy array without high-level libraries
"""

import os
import gzip
from urllib import request
import numpy as np


class MNIST_Loader:
    '''
    Loader to download the MNIST database
    '''
    def __init__(self):
        self.filenames = [
            ["training_images", "train-images-idx3-ubyte.gz"],
            ["test_images", "t10k-images-idx3-ubyte.gz"],
            ["training_labels", "train-labels-idx1-ubyte.gz"],
            ["test_labels", "t10k-labels-idx1-ubyte.gz"]
            ]
        self.url = "http://yann.lecun.com/exdb/mnist/"
        self.download_folder = "mnist_data/"
        self.size = (28, 28) # resolution of a single training image

    def download(self, force=False):
        '''
        Download filenames into specified folder
        '''
        # create the download folder
        os.makedirs(os.path.dirname(self.download_folder), exist_ok=True)

        # download the files
        num_filenames = len(self.filenames)
        for index, filename in enumerate(self.filenames):
            full_url = self.url + filename[1]
            full_path = self.download_folder + filename[1]

            print("=> Process file [{0}/{1}]".format(index + 1, num_filenames))
            if os.path.exists(full_path) and force is False:
                print(full_url + " already downloaded")
            else:
                print("downloading " + full_url + "...")
                request.urlretrieve(full_url, full_path)
                print("download complete.")

    def load_into_float_array(self, normalize = False):
        '''
        Return a dictionnary containing the following data
        {
         'training_images' :[[image_data],...,[image_data]],
         'test_images' : [[image_data],...,[image_data]],
         'training_labels' : [5 0 4 ... 5 6 8],
         'test_labels' : [7 2 1 ... 4 5 6],
         }
        '''
        mnist = {}
        # load the images (training and test)
        for name in self.filenames[:2]:
            full_path = self.download_folder + name[1]
            with gzip.open(full_path, 'rb') as f:
                tmp = np.frombuffer(f.read(), np.uint8, offset=16).reshape(-1,self.size[0]*self.size[1])
                mnist[name[0]] = tmp.astype(float)

                if normalize:
                    min_data = np.min(mnist[name[0]])
                    max_data = np.max(mnist[name[0]])
                    mnist[name[0]] -= min_data
                    mnist[name[0]] /= (max_data - min_data)

        # load the labels (training and test)
        for name in self.filenames[2:]:
            full_path = self.download_folder + name[1]
            with gzip.open(full_path, 'rb') as f:
                tmp = np.frombuffer(f.read(), np.uint8, offset=8)
                mnist[name[0]] = tmp.astype(float)

        return mnist
