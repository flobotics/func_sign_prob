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
        #print(f"item >{item[0]}<  item-1 >{item[1]}< >{ret_type_dict[item[1]]}<")
        trans_ds.append( (item[0], ret_type_dict[item[1]]) )
        
    tfrecord_lib.save_caller_callee_to_tfrecord(trans_ds, config['tfrecord_save_dir'] + os.path.basename(file).replace('.pickle', '.tfrecord'))


def check_config(config):
    if config['base_dir'] == '':
        print(f'Please specify a base-dir (-b or --base-dir) , where all work is done. Check -h for help.')
        print()
        exit()
        
    if not os.path.isdir(config['tfrecord_save_dir']):
        print(f"Directory >{config['tfrecord_save_dir']}< does not exist.")
        exit()
        
    if not os.path.isdir(config['balanced_dataset_dir']):
        print(f"Directory >{config['balanced_dataset_dir']}< does not exist.")
        exit()
         


def main():
    config = common_stuff_lib.parseArgs()
    print(f'config >{config}<')
    print()
    check_config(config)
    
    nr_of_cpus = psutil.cpu_count(logical=True)
    print(f'We got >{nr_of_cpus}< CPUs for threading')
    print()

    ##load ret-type dict
    ret_type_dict = pickle_lib.get_pickle_file_content(config['return_type_dict_file'])
    print(f"ret-type-dict >{ret_type_dict}<")
    print()
    
    pickle_files = common_stuff_lib.get_all_filenames_of_type(config['balanced_dataset_dir'], '.pickle')
    
    ### transform dataset ret-types to ints
    print(f"Transform return-type to int and save to >{config['tfrecord_save_dir']}<")
    print()
    p = Pool(nr_of_cpus)
    
    pickle_files = [config['balanced_dataset_dir'] + "/" + f for f in pickle_files]
    
    star_list = zip(pickle_files, repeat(ret_type_dict), repeat(config))
    
    all_ret_types = p.starmap(proc_build, star_list)
    p.close()
    p.join()
    
       

    print("Done. Run train_nr_of_args_model_lstm.py next")

if __name__ == "__main__":
    main()