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
    user_home_path = os.path.expanduser('~')
    #files = os.listdir(user_home_path + "/test/save_dir/")
    files = common_stuff_lib.get_all_filenames_of_type(user_home_path + "/test/save_dir/", '.pickle')
    
    for file in files:
        if os.path.isfile(user_home_path + "/tmptest/" + file.replace('.pickle', '.pickle.tar.bz2')):
            os.remove(user_home_path + "/tmptest/" + file.replace('.pickle', '.pickle.tar.bz2'))
        print(f'file >{file}<')
#         src_file = user_home_path + "/test/save_dir/" + file.replace('.tfrecord', '.pickle')
#         print(f'src_file >{src_file}<')
#         dst_file = user_home_path + "/backup/tmpstore/" + file.replace('.tfrecord', '.pickle')
#         print(f'dst_file >{dst_file}<')
#         if os.path.isfile(src_file):
#             os.rename(src_file, dst_file)
        #exit()
    



if __name__ == "__main__":
    main()