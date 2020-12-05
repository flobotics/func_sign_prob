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



def parseArgs():
    short_opts = 'hp:s:w:t:r:m:v:f:'
    long_opts = ['pickle-dir=', 'work-dir=', 'save-dir=', 'save-file-type=', 
                 'return-type-dict-file', 'max-seq-length-file=', 'vocab-file=', 'tfrecord-save-dir=',
                 'balanced-dataset-dir=']
    config = dict()
    
    config['pickle_dir'] = ''
    config['work_dir'] = ''
    config['save_dir'] = ''
    config['save_file_type'] = ''
    config['return_type_dict_file'] = ''
    config['max_seq_length_file'] = ''
    config['vocabulary_file'] = ''
    config['tfrecord_save_dir'] = ''
    config['balanced_dataset_dir'] = ''
 
    try:
        args, rest = getopt.getopt(sys.argv[1:], short_opts, long_opts)
    except getopt.GetoptError as msg:
        print(msg)
        print(f'Call with argument -h to see help')
        exit()
    
    for option_key, option_value in args:
        if option_key in ('-p', '--pickle-dir'):
            print(f'found p')
            config['pickle_dir'] = option_value[1:]
        elif option_key in ('-w', '--work-dir'):
            config['work_dir'] = option_value[1:]
        elif option_key in ('-s', '--save-dir'):
            config['save_dir'] = option_value[1:]
        elif option_key in ('-t', '--save-file-type'):
            config['save_file_type'] = option_value[1:]
        elif option_key in ('-r', '--return-type-dict-file'):
            config['return_type_dict_file'] = option_value[1:]
        elif option_key in ('-m', '--max-seq-length-file'):
            config['max_seq_length_file'] = option_value[1:]
        elif option_key in ('-v', '--vocab-file'):
            config['vocabulary_file'] = option_value[1:]
        elif option_key in ('-f', '--tfrecord-save-dir'):
            config['tfrecord_save_dir'] = option_value[1:]
        elif option_key in ('-b', '--balanced-dataset-dir'):
            config['balanced_dataset_dir'] = option_value[1:]
        elif option_key in ('-h'):
            print(f'<optional> -p or --pickle-dir The directory with disassemblies,etc. Default: ubuntu-20-04-pickles')
            print(f'<optional> -w or --work-dir   The directory where we e.g. untar,etc. Default: /tmp/work_dir/')
            print(f'<optional> -s or --save-dir   The directory where we save dataset.  Default: /tmp/save_dir')
            print(f'<optional> -b or --balanced-dataset-dir  The directory where we save the balanced dataset. Default: /tmp/save_dir/balanced/')
            
    if config['pickle_dir'] == '':
        config['pickle_dir'] = '../../../ubuntu-20-04-pickles'
    if config['work_dir'] == '':
        config['work_dir'] = '/tmp/work_dir/'
    if config['save_dir'] == '':
        config['save_dir'] = '/tmp/save_dir/'
    if config['save_file_type'] == '':
        config['save_file_type'] = 'pickle'
    if config['return_type_dict_file'] == '':
        config['return_type_dict_file'] = config['save_dir'] + 'tfrecord/' + 'return_type_dict.pickle'
    if config['max_seq_length_file'] == '':
        config['max_seq_length_file'] = config['save_dir'] + 'tfrecord/' + 'max_seq_length.pickle'
    if config['vocabulary_file'] == '':
        config['vocabulary_file'] = config['save_dir'] + 'tfrecord/' + 'vocabulary_list.pickle'
    if config['tfrecord_save_dir'] == '':
        config['tfrecord_save_dir'] = config['save_dir'] + 'tfrecord/'
    if config['balanced_dataset_dir'] == '':
        config['balanced_dataset_dir'] = config['save_dir'] + 'balanced/'
    
            
    return config





def main():
    config = parseArgs()
    
    nr_of_cpus = psutil.cpu_count(logical=True)
    print(f'We got nr_of_cpus >{nr_of_cpus}<')
    print()
    
    print(f"Using files in directory >{config['save_dir']}<")
    print()
    
    pickle_files = common_stuff_lib.get_all_filenames_of_type(config['save_dir'], '.pickle')
    
    all_ret_types_list = set()
    counter = 0
    max_seq_len = 0
    
    for file in pickle_files:
        cont = pickle_lib.get_pickle_file_content(config['save_dir'] + file)
        counter = 0
        max_seq_len = 0
        
        for item in cont:
            all_ret_types_list.add(item[1])
            if counter < 1:
                print(f"nr-of-arguments >{item[1]}< from file >{config['save_dir'] + file}<")
                print()
                print(f'text >{item[0]}<\nlabel >{item[1]}<')
            
            if len(item[0]) > max_seq_len:
                max_seq_len = len(item[0])
                
            counter += 1
            
        print(f'Counted >{counter}< text,label elements')
        print(f'longest disassembly got >{max_seq_len}< words')
        print('----------------------------------------')
        print()
        
        
    print(f'all_ret_types_list >{all_ret_types_list}<')



    
if __name__ == "__main__":
    main()