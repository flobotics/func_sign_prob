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
    
    print(f"Using files in directory >{config['save_dir']}<")
    
    pickle_files = common_stuff_lib.get_all_filenames_of_type(config['save_dir'], '.pickle')
    
    for file in pickle_files:
        cont = pickle_lib.get_pickle_file_content(config['save_dir'] + file)
        counter = 0
        
        for item in cont:
            #print(f'item[0] >{item[0]}<  item[1] >{item[1]}<')
            if counter < 1:
                print(f"return type >{item[1]}< from file >{config['save_dir'] + file}<")
                print(f'{item[0]}')
            counter += 1
            
        print(f'Counted >{counter}< text,label elements')
        print()




    
if __name__ == "__main__":
    main()