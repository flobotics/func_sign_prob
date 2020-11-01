import tarfile
import os
import sys
import pickle
#import tensorflow as tf
from datetime import datetime
from multiprocessing import Pool
import getopt
from itertools import repeat

sys.path.append('../../lib/')
import common_stuff_lib

def main():
    #files = os.listdir("/home/infloflo/test/save_dir/")
    files = common_stuff_lib.get_all_filenames_of_type("/home/infloflo/test/save_dir/", '.pickle')
    
    for file in files:
        os.remove("/home/infloflo/tmptest/" + file.replace('.pickle', '.pickle.tar.bz2'))
        print(f'file >{file}<')
#         src_file = "/home/infloflo/test/save_dir/" + file.replace('.tfrecord', '.pickle')
#         print(f'src_file >{src_file}<')
#         dst_file = "/home/infloflo/backup/tmpstore/" + file.replace('.tfrecord', '.pickle')
#         print(f'dst_file >{dst_file}<')
#         if os.path.isfile(src_file):
#             os.rename(src_file, dst_file)
        #exit()
    



if __name__ == "__main__":
    main()