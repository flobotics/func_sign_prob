import tarfile
import os
import sys
import pickle
#import tensorflow as tf
from datetime import datetime
from multiprocessing import Pool
import getopt
from itertools import repeat


def main():
    files = os.listdir("/tmp/tf_record_dir/")
    
    for file in files:
        print(f'file >{file}<')
        src_file = "/home/infloflo/backup/save_dir/" + file.replace('.tfrecord', '.pickle')
        print(f'src_file >{src_file}<')
        dst_file = "/home/infloflo/backup/tmpstore/" + file.replace('.tfrecord', '.pickle')
        print(f'dst_file >{dst_file}<')
        if os.path.isfile(src_file):
            os.rename(src_file, dst_file)
        #exit()
    



if __name__ == "__main__":
    main()