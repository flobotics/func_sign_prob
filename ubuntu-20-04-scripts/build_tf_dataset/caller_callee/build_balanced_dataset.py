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
                 'return-type-dict-file', 'max-seq-length-file=', 'vocab-file=', 'tfrecord-save-dir=']
    config = dict()
    
    config['pickle_dir'] = ''
    config['work_dir'] = ''
    config['save_dir'] = ''
    config['save_file_type'] = ''
    config['return_type_dict_file'] = ''
    config['max_seq_length_file'] = ''
    config['vocabulary_file'] = ''
    config['tfrecord_save_dir'] = ''
 
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
        elif option_key in ('-h'):
            print(f'<optional> -p or --pickle-dir The directory with disassemblies,etc. Default: ubuntu-20-04-pickles')
            print(f'<optional> -w or --work-dir   The directory where we e.g. untar,etc. Default: /tmp/work_dir/')
            print(f'<optional> -s or --save-dir   The directory where we save dataset.  Default: /tmp/save_dir')
            
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
    
            
    return config
    

def proc_count(file, ret_type_dict, config):
    #ret_type_dict => 'char' = 0   'int' = 1
    
    ## build count dict
    ret_type_count = dict()
    nr = 0
    for key in ret_type_dict:
        ret_type_count[key] = 0
        
    ##count
    cont = pickle_lib.get_pickle_file_content(file)
    for item in cont:
        ret_type_count[item[1]] = ret_type_count[item[1]] + 1
            
    #print(f"Counter >{ret_type_count}<")
    
    return ret_type_count
      

def main():
    config = parseArgs()
    
    nr_of_cpus = psutil.cpu_count(logical=True)
    print(f'We got nr_of_cpus >{nr_of_cpus}<')
    
    ret_type_dict = pickle_lib.get_pickle_file_content(config['return_type_dict_file'])
    
    ## get number of different return types
    pickle_files = common_stuff_lib.get_all_filenames_of_type(config['save_dir'], '.pickle')
    
    p = Pool(nr_of_cpus)
    
    
    pickle_files_save_dir = [config['save_dir'] + "/" + f for f in pickle_files]
    star_list = zip(pickle_files_save_dir, repeat(ret_type_dict), repeat(config))
    all_ret_types = p.starmap(proc_count, star_list)
    p.close()
    p.join()
    
    ## build count dict
    ret_type_counter = dict()
    nr = 0
    for key in ret_type_dict:
        ret_type_counter[key] = 0
        
    for counts_dict in all_ret_types:
        #print(f"counts_dict >{counts_dict}<")
        for counts_dict_key in counts_dict:
            #print(f"counts_dict[counts_dict_key] >{counts_dict[counts_dict_key]}<")
            ret_type_counter[counts_dict_key]  += counts_dict[counts_dict_key]
        
    print(f"The counts of every return type >{ret_type_counter}<")
    
    ### filter all that >= 10
    minimum_ret_type_count = 10
    ret_type_counter_filtered = dict()
    for key in ret_type_dict:
        if ret_type_counter[key] >= minimum_ret_type_count:
            ret_type_counter_filtered[key] = ret_type_counter[key]
            
    print(f"The filtered counts of every return type >{ret_type_counter_filtered}<")
    
    ### now select minimum_ret_type_count disassemblies,labels from 
    ### every return type that is possible (got so many minimum_ret_type_count)
    for file in pickle_files:
        cont = pickle_lib.get_pickle_file_content(file)
    
    
    
if __name__ == "__main__":
    main()
