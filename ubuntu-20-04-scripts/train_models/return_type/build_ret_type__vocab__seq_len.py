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
        exit()
        
    print(f'config >{config}<')
    print()


def proc_build(file, config):
    
    ret_set = set()
    vocab = set()
    seq_length = 0
    
    print(f'File >{file}<')
    
    cont = pickle_lib.get_pickle_file_content(file)
    for item in cont:
        #print(f'item-1 >{item[1]}<')
        ## build ret-type-dict
        ret_set.add(item[1])
        
        ##build max-seq-length
        if len(item[0]) > seq_length:
            if len(item[0]) > 100000:
                print(f'len-bigger 100.000')
            seq_length = len(item[0])
            
        ## build vocabulary
        for word in item[0].split():
            vocab.add(word)
            
    return (ret_set, vocab, seq_length)




def main():
    config = common_stuff_lib.parseArgs()
    check_config(config)
    
    nr_of_cpus = psutil.cpu_count(logical=True)
    print(f'We got >{nr_of_cpus}< CPUs for threading\n')
    print()
    
    
    ## build return type dict-file and max-seq-length-file and vocabulary
    pickle_files = common_stuff_lib.get_all_filenames_of_type(config['save_dir'], '.pickle')
    print(f'pickle-files we use to build >{pickle_files}<')
    
    print(f'Building return-type dict, vocabulary and max-squenece-length')
    
    p = Pool(nr_of_cpus)
    
    pickle_files = [config['save_dir'] + "/" + f for f in pickle_files]
    
    star_list = zip(pickle_files, repeat(config))
    
    all_ret_types = p.starmap(proc_build, star_list)
    p.close()
    p.join()
    
    ret_set = set()
    vocab = set()
    seq_length = 0
    
    ##put all stuff together
    for ret_set1, vocab1, seq_length1 in all_ret_types:
        ret_set.update(ret_set1)
        vocab.update(vocab1)
        if seq_length1 > seq_length:
            seq_length = seq_length1
    
        
    print(f"Build return-type dict from set and save it to >{config['return_type_dict_file']}<")        
    ## build ret-type-dict and save
    ret_type_dict = dict()
    counter = 0
    for elem in ret_set:
        ret_type_dict[elem] = counter
        counter += 1
    
    print(f"ret-type-dict >{ret_type_dict}<")
    pickle_lib.save_to_pickle_file(ret_type_dict, config['return_type_dict_file'])
        
    print(f"Saving vocabulary to >{config['vocabulary_file']}<")
    ## build vocabulary list from set and save
    vocab_list = list(vocab)
    pickle_lib.save_to_pickle_file(vocab_list, config['vocabulary_file'])
    
    ## save max-seq-length
    print(f"Saving max-sequence-length to >{config['max_seq_length_file']}<")
    pickle_lib.save_to_pickle_file(seq_length, config['max_seq_length_file'])
    
    
    print("Done. Run build_balanced_dataset.py next")
    
    

if __name__ == "__main__":
    main()