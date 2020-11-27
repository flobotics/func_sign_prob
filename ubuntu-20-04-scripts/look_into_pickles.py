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


sys.path.append('lib/')
#import return_type_lib
import common_stuff_lib
import tarbz2_lib
import pickle_lib
#import disassembly_lib
#import tfrecord_lib



def main():
#     tarbz2_files = common_stuff_lib.get_all_filenames_of_type("/tmp/test/", '.tar.bz2')
#     
#     work_dir = "/tmp/work_dir"
#     for tarbz2_file in tarbz2_files:
#         tarbz2_lib.untar_file_to_path('/tmp/test/' + tarbz2_file, work_dir)
    
    pickle_files = common_stuff_lib.get_all_filenames_of_type("/tmp/work_dir", '.pickle')
    
    for file in pickle_files:
        cont = pickle_lib.get_pickle_file_content("/tmp/work_dir/" + file)
        
        for elem in cont:
            #print(f'elem >{elem}<')
            if len(elem[4]) > 10000:
#                 print(f'filename >{elem[3]}<')
#                 print(f'funcname >{elem[2]}<')
#                 print(f'binary >{elem[7]}<')
#                 print(f'package >{elem[6]}<')
#                 print(f'att >{elem[4]}<')
                #print(f'intel >{elem[5]}<')
                
                for item in elem[4]:
                    print(f'{item}')


if __name__ == "__main__":
    main()