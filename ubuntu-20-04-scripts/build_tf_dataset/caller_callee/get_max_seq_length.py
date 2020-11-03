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


ret = pickle_lib.get_pickle_file_content("/home/infloflo/backup/save_dir/tfrecord/max_seq_length.pickle")

print(f'max-seq-length >{ret}<')