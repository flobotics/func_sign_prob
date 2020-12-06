import tarfile
import os
import sys
import pickle
#import tensorflow as tf
from datetime import datetime
from multiprocessing import Pool
# import getopt
from itertools import repeat
import psutil
from threading import Thread


sys.path.append('../../lib/')
import return_type_lib
import common_stuff_lib
import tarbz2_lib
import pickle_lib
import disassembly_lib
#import tfrecord_lib



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
      
      
def proc_build_balanced(pickle_files, key, minimum_ret_type_count, config):
    #print(f'build balanced')
    ### filter and store to dict the usable text,label pairs
    
    ## a dict that counts how many text,labels from one key-type we got
    ret_type_count_watcher = 1
#     nr = 0
#     for key in ret_type_counter_filtered:
#         ret_type_count_watcher[key] = 0
        
    ret_type_0 = list()    
    for file in pickle_files:
        cont = pickle_lib.get_pickle_file_content(file)
        for item in cont:
            ## is the ret-type we found in our filtered list?
            #for key in ret_type_counter_filtered:
            if key == item[1]:
                #print(f'got filtered ret-type')
                if ret_type_count_watcher <= minimum_ret_type_count:
                    ret_type_0.append( (item[0], item[1]) )
                    ret_type_count_watcher += 1
                    if ret_type_count_watcher > minimum_ret_type_count:
                        break
        
        if ret_type_count_watcher > minimum_ret_type_count:
            break
    
    ### save them
    #print(f'Save balanced dataset')
    pickle_lib.save_to_pickle_file(ret_type_0, config['balanced_dataset_dir'] + str(key) + '.pickle')
    
    
      
def check_config(config):
    if config['base_dir'] == '':
        print(f'Please specify a base-dir (-b or --base-dir) , where all work is done. Check -h for help.')
        print()
        exit()
        
        
    if not os.path.isdir(config['balanced_dataset_dir']):
        os.mkdir(config['balanced_dataset_dir'])
        

def check_if_balanced_dir_is_empty(config):
    pickle_files = common_stuff_lib.get_all_filenames_of_type(config['balanced_dataset_dir'], '.pickle')
    
    if len(pickle_files) > 0:
        decision = 'z'
        while( (decision != 'y') and (decision != 'n' ) ):
            decision = input(f"There are still files in >{config['balanced_dataset_dir']}< . Do you want to use them: Type in (y/n):")
    
        print()
        if decision == 'y':
            print(f'Using files still there')
            print()
            return
        
        print(f"Deleting files in >{config['balanced_dataset_dir']}<")
        print()
        for file in pickle_files:
            os.remove(config['balanced_dataset_dir'] + file)
        
        
    
def main():
    config = common_stuff_lib.parseArgs()
    
    check_config(config)
    
    nr_of_cpus = psutil.cpu_count(logical=True)
    print(f'We got >{nr_of_cpus}< CPUs for threading')
    print()
    
    check_if_balanced_dir_is_empty(config)
    
    ret_type_dict = pickle_lib.get_pickle_file_content(config['return_type_dict_file'])
    
    ## get number of different return types
    pickle_files = common_stuff_lib.get_all_filenames_of_type(config['save_dir'], '.pickle')
    
    print(f'Building balanced dataset now')
    print()
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
        
    print(f"The counts of every nr_of_arguments :")
    for key in ret_type_counter:
        print(f"Functions with >{key}< argument(s) exists\t\t\t>{ret_type_counter[key]}< \ttimes")
    
    config['minimum_nr_of_return_types'] = input('Put in minimum nr of nr_of_args to build balanced dataset:')
    
    ### filter all that >= int(config['minimum_nr_of_return_types'])
    ret_type_counter_filtered = dict()
    for key in ret_type_dict:
        if ret_type_counter[key] >= int(config['minimum_nr_of_return_types']):
            ret_type_counter_filtered[key] = ret_type_counter[key]
            
    print(f"The filtered counts (>={int(config['minimum_nr_of_return_types'])}) of every return type >{ret_type_counter_filtered}<")
    
    ### now select int(config['minimum_nr_of_return_types']) disassemblies,labels from 
    ### filter and store to dict the usable text,label pairs
    
    for key in ret_type_counter_filtered:
        print(f'build balanced with key >{key}<')
        t = Thread(target=proc_build_balanced, args=(pickle_files_save_dir, key, int(config['minimum_nr_of_return_types']), config, ))
        t.start()
        
    print(f'Run build_balanced_ret_type__vocab__seq_len.py next')

    
if __name__ == "__main__":
    main()
