import tarfile
import os
import sys
import pickle
#import tensorflow as tf
from datetime import datetime
from multiprocessing import Pool
import getopt
from itertools import repeat
import psutil

sys.path.append('../../lib/')
import return_type_lib
import common_stuff_lib
import tarbz2_lib
import pickle_lib
import disassembly_lib
#import tfrecord_lib

a = 100000
pickle_lib.save_to_pickle_file(a,"/home/infloflo/test/save_dir2/tfrecord/max_sequence_length.pickle")