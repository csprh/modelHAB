"""
Class for managing our data.
"""
import csv
import numpy as np
import random
import glob
import os.path
import sys
import operator
import threading
from processor import process_image
from keras.utils import to_categorical
import os.path

class threadsafe_iterator:
    def __init__(self, iterator):
        self.iterator = iterator
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            return next(self.iterator)

def threadsafe_generator(func):
    """Decorator"""
    def gen(*a, **kw):
        return threadsafe_iterator(func(*a, **kw))
    return gen

class DataSet():

    def __init__(self, seq_length=40, image_shape=(224, 224, 3)):
        """Constructor.
        seq_length = (int) the number of frames to consider
        """
        self.seq_length = seq_length
        self.sequence_path = os.path.join('data', 'sequences')
        self.max_frames = 300  # max number of frames a video can have for us to use it


        # Get the data.
        self.dataLowest = self.get_data()
        self.data = self.extract_data(self.dataLowest)

        # Get the classes.

        self.image_shape = image_shape



    @staticmethod
    def get_data():
        """Load our data from file."""

        mydir = '/mnt/storage/home/csprh/scratch/HAB/CNNIms/florida3/'
        #mydir = '/Users/csprh/tmp/CNNIms/florida3/'
        max_depth = 0
        bottom_most_dirs = []
        for dirpath, dirnames, filenames in os.walk(mydir):
            depth = len(dirpath.split(os.sep))
            if max_depth < depth:
                max_depth = depth
                bottom_most_dirs = [dirpath]
            elif max_depth == depth:
                bottom_most_dirs.append(dirpath)

        return bottom_most_dirs

    @staticmethod
    def extract_data(dataLowest):
        """ Get rid of last layer of dataLowest and put into data """
        output = []
        bottom_most_dirs = []
        for x in dataLowest:
                head, tail = os.path.split(x)
                bottom_most_dirs.append(head)

        for x in bottom_most_dirs:
            if x not in output:
                output.append(x)

        return output

    def get_class_one_hot(self, path_str):
        """Given a class as a string, return its number in the classes
        list. This lets us encode and one-hot it for training."""
        # Encode it first.
        parts = path_str.split(os.path.sep)

        # Now one-hot it.
        label_hot = to_categorical(int(parts[-2]), 2)

        assert len(label_hot) == 2

        return label_hot

    def split_train_test(self):
        """Split the data into train and test groups."""
        train = []
        test = []

        for item in self.data:
            parts = item.split(os.path.sep)
            if parts[-3] == 'Train':
                train.append(item)
            else:
                test.append(item)
        return train, test

    @threadsafe_generator
    def frame_generator(self, batch_size, train_test, data_type):
        """Return a generator that we can use to train on. There are
        a couple different things we can return:

        data_type: 'features', 'images'
        """
        # Get the right dataset for the generator.
        train, test = self.split_train_test()
        data = train if train_test == 'train' else test

        print("Creating %s generator with %d samples." % (train_test, len(data)))

        while 1:
            X, y = [], []

            # Generate batch_size samples.
            for _ in range(batch_size):
                # Reset to be safe.
                sequence = None

                # Get a random sample.
                sample = random.choice(data)

                # Check to see if we've already saved this sequence.
                if data_type is "images":
                    # Get and resample frames.
                    frames = self.get_frames_for_sample(sample)

                    # Build the image sequence
                    sequence = self.build_image_sequenceAllMods(frames)
                else:
                    # Get the sequence from disk.
                    sequence = self.get_extracted_sequence(data_type, sample)

                    if sequence is None:
                        raise ValueError("Can't find sequence. Did you generate them?")

                X.append(sequence)
                y.append(self.get_class_one_hot(sample))

            yield np.array(X), np.array(y)

    def build_image_sequence(self, frames):
        """Given a set of frames (filenames), build our sequence."""
        return [process_image(x, self.image_shape) for x in frames]

    def get_extracted_sequenceAllMods(self, data_type, filename):
        """Get the saved extracted features."""
        #filename = sample[2]

        thisReturn = []
        for i in range(1,10):
            thisPath = filename + '/' + str(i) + '/seqFeats.npy'
            thisFeats = np.load(thisPath)
            #if os.path.isfile(path):
            #    return np.load(path)
            #else:
            #    return None
            thisReturn = np.concatenate((thisReturn,thisFeats),axis=1)
        return thisReturn

    def get_extracted_sequence(self, data_type, filename):
        """Get the saved extracted features."""
        #filename = sample[2]

        path = filename + '/8/seqFeats.npy'
        if os.path.isfile(path):
            return np.load(path)
        else:
            return None

    def get_frames_by_filename(self, filename, data_type):
        """Given a filename for one of our samples, return the data
        the model needs to make predictions."""
        # First, find the sample row.
        sample = None
        for row in self.data:
            if row[2] == filename:
                sample = row
                break
        if sample is None:
            raise ValueError("Couldn't find sample: %s" % filename)

        if data_type == "images":
            # Get and resample frames.
            frames = self.get_frames_for_sample(sample)
            frames = self.rescale_list(frames, self.seq_length)
            # Build the image sequence
            sequence = self.build_image_sequence(frames)
        else:
            # Get the sequence from disk.
            sequence = self.get_extracted_sequence(data_type, sample)

            if sequence is None:
                raise ValueError("Can't find sequence. Did you generate them?")

        return sequence

    @staticmethod
    def get_frames_for_sample(sample):
        """Given a sample row from the data file, get all the corresponding frame
        filenames."""
        path = os.path.join('data', sample[0], sample[1])
        filename = sample[2]
        images = sorted(glob.glob(os.path.join(path, filename + '*jpg')))
        return images

    @staticmethod
    def get_filename_from_image(filename):
        parts = filename.split(os.path.sep)
        return parts[-1].replace('.jpg', '')


    def print_class_from_prediction(self, predictions, nb_to_return=5):
        """Given a prediction, print the top classes."""
        # Get the prediction for each label.
        label_predictions = {}
        for i, label in enumerate(self.classes):
            label_predictions[label] = predictions[i]

        # Now sort them.
        sorted_lps = sorted(
            label_predictions.items(),
            key=operator.itemgetter(1),
            reverse=True
        )

        # And return the top N.
        for i, class_prediction in enumerate(sorted_lps):
            if i > nb_to_return - 1 or class_prediction[1] == 0.0:
                break
            print("%s: %.2f" % (class_prediction[0], class_prediction[1]))