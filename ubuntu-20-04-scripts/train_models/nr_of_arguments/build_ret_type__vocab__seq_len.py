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


def check_trailing_slash_in_path(path):
    if not path.endswith('/'):
        path = path + '/'
        
    return path


def parseArgs():
    short_opts = 'hs:t:r:m:v:f:b:'
    long_opts = ['save-dir=', 'save-file-type=', 'base-dir=',
                 'return-type-dict-file', 'max-seq-length-file=', 'vocab-file=', 'tfrecord-save-dir=']
    config = dict()

    config['base_dir'] = ''
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
        elif option_key in ('-b', '--base-dir'):
            config['base_dir'] = option_value[1:]
        elif option_key in ('-h'):
            print(f'<optional> -s or --save-dir   The directory where we get the dataset from.  Default: /tmp/save_dir')
            

    ##if base-dir is specified, check for trailing slash
    if not config['base_dir'] == '':
        config['base_dir'] = check_trailing_slash_in_path(config['base_dir'])
        
        if config['save_dir'] == '':
            config['save_dir'] = config['base_dir'] + 'save_dir/'
            
        if config['save_file_type'] == '':
            config['save_file_type'] = 'pickle'
            
        if config['tfrecord_save_dir'] == '':
            config['tfrecord_save_dir'] = config['base_dir'] + 'tfrecord/'
            
        if config['return_type_dict_file'] == '':
            config['return_type_dict_file'] = config['tfrecord_save_dir'] + 'return_type_dict.pickle'
            
        if config['max_seq_length_file'] == '':
            config['max_seq_length_file'] = config['tfrecord_save_dir'] + 'max_seq_length.pickle'
            
        if config['vocabulary_file'] == '':
            config['vocabulary_file'] = config['tfrecord_save_dir'] + 'vocabulary_list.pickle'
        
       
    return config






def proc_build(file, config):
    
    ret_set = set()
    vocab = set()
    seq_length = 0
    
    print(f'Parsing file >{file}<\t\t\t\t', end='\r')
    
    cont = pickle_lib.get_pickle_file_content(file)
    for item in cont:
        #print(f'item-1 >{item[1]}<')
        ## build ret-type-dict
        ret_set.add(item[1])
        
        ##build max-seq-length
        if len(item[0]) > seq_length:
            seq_length = len(item[0])
            
        ## build vocabulary
        for word in item[0].split():
            vocab.add(word)
            
    return (ret_set, vocab, seq_length)



def check_config(config):
    if config['base_dir'] == '':
        print(f'Please specify a base-dir (-b or --base-dir) , where all work is done. Check -h for help.')
        print()
        exit()
        
    if not os.path.isdir(config['tfrecord_save_dir']):
        print(f"Directory >{config['tfrecord_save_dir']}< does not exist. Create it.")
        print()
        exit()
        
        

def main():
    config = parseArgs()
    print(f'config >{config}<')
    print()
    check_config(config)
    
    nr_of_cpus = psutil.cpu_count(logical=True)
    print(f'We got >{nr_of_cpus}< CPUs for threading')
    print()
    
    ## build return type dict-file and max-seq-length-file and vocabulary
    pickle_files = common_stuff_lib.get_all_filenames_of_type(config['save_dir'], '.pickle')
    #print(f'pickle-files we use to build >{pickle_files}<')
    pickle_lib.print_X_pickle_filenames(pickle_files, 5)
    
    print(f'Building return-type dict, vocabulary and max-squenece-length')
    print()
    
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
    print()       
    ## build ret-type-dict and save
    ret_type_dict = dict()
    counter = 0
    ret_set_list = sorted(ret_set)
    for elem in ret_set_list:
        ret_type_dict[elem] = counter
        counter += 1
    
    print(f"ret-type-dict :")
    for key in ret_type_dict:
        print(f"nr-of-args >{key}<  label >{ret_type_dict[key]}<")
    print()
        
    pickle_lib.save_to_pickle_file(ret_type_dict, config['return_type_dict_file'])
        
    print(f"Saving vocabulary to >{config['vocabulary_file']}<")
    print()
    ## build vocabulary list from set and save
    vocab_list = list(vocab)
    pickle_lib.save_to_pickle_file(vocab_list, config['vocabulary_file'])
    
    ## save max-seq-length
    print(f"Saving max-sequence-length to >{config['max_seq_length_file']}<")
    print()
    pickle_lib.save_to_pickle_file(seq_length, config['max_seq_length_file'])
    
    
    print("Done. Run build_balanced_dataset.py next")
    
    

if __name__ == "__main__":
    main()