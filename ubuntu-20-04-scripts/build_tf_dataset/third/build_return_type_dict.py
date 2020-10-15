import pickle
import numpy as np
import os
from datetime import datetime
import getopt
import sys


def get_all_pickle_filenames(pickle_file_dir):
    files = os.listdir(pickle_file_dir)
    tar_files = list()
    for f in files:
        if f.endswith(".pickle"):
            tar_files.append(f)
    
    return tar_files


def get_pickle_file_content(full_path_pickle_file):
    pickle_file = open(full_path_pickle_file,'rb')
    pickle_list = pickle.load(pickle_file, encoding='latin1')
    pickle_file.close()
    
    return pickle_list


def get_ret_type_dict(pickle_list):
    ret_type_set = set()
    
    for int_seq, ret_type in pickle_list:
        #print(f'int_seq: {int_seq}  ret_type:{ret_type}')
        ret_type_set.add(ret_type)
                
    return ret_type_set


def parseArgs():
    short_opts = 'hp:s:'
    long_opts = ['pickle-dir=', 'save-ret-type-dict-file=']
    config = dict()
    
    config['pickle_dir'] = '/tmp/save_dir'
    config['save_ret_type_dict_file'] = '/tmp/ret_type_dict.pickle'
    
    try:
        args, rest = getopt.getopt(sys.argv[1:], short_opts, long_opts)
    except getopt.GetoptError as msg:
        print(msg)
        print(f'Call with argument -h to see help')
        exit()
    
    for option_key, option_value in args:
        if option_key in ('-p', '--pickle-dir'):
            config['pickle_dir'] = option_value[1:]
        elif option_key in ('-s', '--save-ret-type-dict-file'):
            config['save_ret_type'] = option_value[1:]
        elif option_key in ('-h'):
            print(f'<optional> -p or --pickle-dir The directory with disassemblies,etc. Default: /tmp/save_dir')
            print(f'<optional> -s or --save-ret-type-dict-file  The file to save the return type dictionary to')
            
    return config  


def main():
    
    config = parseArgs()
    
    #path_to_int_seq_pickle = "../../../ubuntu-20-04-datasets/full_dataset_att_int_seq.pickle"
    path_to_int_seq_pickle = config['pickle_dir']
    #path_to_return_type_dict_file = "../../ubuntu-20-04-datasets/full_dataset_att_int_seq_ret_type_dict.pickle"
    #path_to_return_type_dict_file = "/tmp/full_dataset_att_int_seq_ret_type_dict.pickle"
    path_to_return_type_dict_file = config['save_ret_type_dict_file']
    
    ###read out full ds pickle
    if not os.path.isdir(path_to_int_seq_pickle):
        print(f'No dir: {path_to_int_seq_pickle} there ?')
        exit()
        
    all_sets = set()
    
    files = get_all_pickle_filenames(path_to_int_seq_pickle)
    for file in files:
        pickle_file_content = get_pickle_file_content(path_to_int_seq_pickle + '/' + file)
    
        ### get return type dict
        ret_type_set = get_ret_type_dict(pickle_file_content)
        all_sets.update(ret_type_set)
        
        
    
        
        
    ret_type_dict = {k:v for v,k in enumerate(all_sets, start=1)}
    print(f'ret-type-dict: {ret_type_dict}')
    
    ### save return type dict to file
    ret_file = open(path_to_return_type_dict_file, 'wb+')
    pickle_list = pickle.dump(ret_type_dict, ret_file)
    ret_file.close()
    
    print(f'Saved {path_to_return_type_dict_file} file.')
    
    
if __name__ == "__main__":
    main()

    
    

