import tarfile
import os
import sys
import pickle
import tensorflow as tf
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
import tfrecord_lib



def parseArgs():
    short_opts = 'hp:s:t:r:m:v:f:b:'
    long_opts = ['pickle-dir=', 'save-dir=', 'save-file-type=', 'balanced-dataset-dir=',
                 'return-type-dict-file', 'max-seq-length-file=', 'vocab-file=', 'tfrecord-save-dir=']
    config = dict()
    
    config['pickle_dir'] = ''
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
        if option_key in ('-s', '--save-dir'):
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
            print(f'<optional> -s or --save-dir   The directory where we get the dataset from.  Default: /tmp/save_dir')
            print(f'<optional> -b or --balanced-dataset-dir  The directory where we save the balanced dataset. Default: /tmp/save_dir/balanced/')
            
    
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



def check_config(config):
    if not os.path.isdir(config['save_dir']):
        print(f"Directory >{config['save_dir']}< does not exist")
        exit()
        
    if not os.path.isdir(config['tfrecord_save_dir']):
        print(f"Directory >{config['tfrecord_save_dir']}< does not exist. Create it.")
        exit()
        
 
def proc_build(file, ret_type_dict, config):
    trans_ds = list()
    
    print(f'Transform File >{file}<')
    
    cont = pickle_lib.get_pickle_file_content(file)
    for item in cont:
        print(f"item >{item[0]}<  item-1 >{item[1]}< >{ret_type_dict[item[1]]}<")
        trans_ds.append( (item[0], ret_type_dict[item[1]]) )
        
    tfrecord_lib.save_caller_callee_to_tfrecord(trans_ds, config['tfrecord_save_dir'] + os.path.basename(file).replace('.pickle', '.tfrecord'))


def check_config(config):
    if not os.path.isfile(config['return_type_dict_file']):
        print(f"No ret-type-dict file >{config['return_type_dict_file']}<")
        exit()
         


def main():
    config = parseArgs()
    
    check_config(config)
    
    print(f'config >{config}<')
    
    nr_of_cpus = psutil.cpu_count(logical=True)
    print(f'We got nr_of_cpus >{nr_of_cpus}<')

    ##load ret-type dict
    ret_type_dict = pickle_lib.get_pickle_file_content(config['return_type_dict_file'])
    print(f"ret-type-dict >{ret_type_dict}<")
    
    pickle_files = common_stuff_lib.get_all_filenames_of_type(config['balanced_dataset_dir'], '.pickle')
    
    ### transform dataset ret-types to ints
    print(f"Transform return-type to int and save to >{config['tfrecord_save_dir']}<")
    p = Pool(nr_of_cpus)
    
    pickle_files = [config['balanced_dataset_dir'] + "/" + f for f in pickle_files]
    
    star_list = zip(pickle_files, repeat(ret_type_dict), repeat(config))
    
    all_ret_types = p.starmap(proc_build, star_list)
    p.close()
    p.join()
    
       

    print("Done. Run train_arg_one_model_lstm.py next")

if __name__ == "__main__":
    main()