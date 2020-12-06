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
#import disassembly_lib
#import tfrecord_lib

def check_config(config):
    if config['base_dir'] == '':
        print(f'Please specify a base-dir (-b or --base-dir) , where all work is done. Check -h for help.')
        print()
        exit()
        

def main():
    config = common_stuff_lib.parseArgs()
    print(f'config >{config}<')
    print()
    check_config(config)
    
    nr_of_cpus = psutil.cpu_count(logical=True)
    print(f'We got >{nr_of_cpus}< CPUs for threading')
    print()
    
    print(f"Using files in directory >{config['tfrecord_save_dir']}<")
    print()
    
    return_type_dict = pickle_lib.get_pickle_file_content(config['tfrecord_save_dir'] + 'return_type_dict.pickle')
    
    print(f'return_type_dict value >{return_type_dict}<')
    print()
    
    vocabulary_list= pickle_lib.get_pickle_file_content(config['tfrecord_save_dir'] + 'vocabulary_list.pickle')
    
    print(f'vocabulary_list >{vocabulary_list}<')
    print()
    
    print(f'vocabulary_list length >{len(vocabulary_list)}<')
    print()
    
    max_seq_length = pickle_lib.get_pickle_file_content(config['tfrecord_save_dir'] + 'max_seq_length.pickle')
    
    print(f'max_seq_length >{max_seq_length}<')
    
 


    
if __name__ == "__main__":
    main()