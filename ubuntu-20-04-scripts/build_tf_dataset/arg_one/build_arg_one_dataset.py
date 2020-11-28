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
    
    
def check_config(config):
    pass

def proc_build(tarbz2_file, work_dir, save_dir, config):
    
    tarbz2_lib.untar_file_to_path(tarbz2_file, work_dir)
    #untar_one_pickle_file(tarbz2_file, work_dir)
     
    pickle_file = work_dir + os.path.basename(tarbz2_file).replace('.tar.bz2', '')
    pickle_file_content = pickle_lib.get_pickle_file_content(pickle_file)   
    #pickle_file_content = get_pickle_file_content(work_dir + os.path.basename(pickle_file).replace('.tar.bz2', ''))
    
    binaries = set()
    functions = set()
    for elem in pickle_file_content:
        binaries.add(elem[7])
        functions.add(elem[2])
    
    print(f'binaries >{binaries}<')
    
    counter = 0
    dataset_list = list()
    
    ## 1. get one binary
    ## 2. get one function of this binary
    ## 3. get disassembly of this function
    ## 4. check if this disassembly calls another function
    ## 4.1 filter @plt
    ## 5. if yes: get disassembly of caller function
    ## 6. save caller, callee, nr_of_args
    ## 7. check again, if it calls another function
    ## 8. if yes: get disassembly of caller function
    ## 9. save caller, calle, func_signature
    ##10. get disassembly of next function of this binary
    ##11. check if ....
    for bin in binaries:
        for func in functions:
            ## search for bin and func
            for elem in pickle_file_content:
                ### if we found bin and func
                if elem[7] == bin and elem[2] == func:
                    ## get att disassembly
                    att_dis = elem[4]
                    #print(f'att-dis >{att_dis}<')
                    ## check every line if there is a call
                    for item in att_dis:
                        ## find call in disas
                        if disassembly_lib.find_call_in_disassembly_line(item):
                            ## if found, get callee name
                            callee_name = disassembly_lib.get_callee_name_from_disassembly_line(item)
                                                                   
                            #print(f'callee_name >{callee_name}<')
                            
                            ## search for same bin, but callee func
                            for elem2 in pickle_file_content:
                                ### if we found it, get return type and disassembly
                                if elem2[7] == bin and elem2[2] == callee_name:
                                    
                                    #return_type_func_sign = return_type_lib.get_return_type_from_function_signature(elem2[0])
                                    #return_type = return_type_lib.get_return_type_from_gdb_ptype(elem2[1])
                                    nr_of_args = return_type_lib.get_nr_of_args_from_function_signature(elem2[0])
                                    arg_nr_we_want = 1
                                    if nr_of_args < arg_nr_we_want:
                                        print(f'func got to less args for us')
                                        break
                                        
                                    arg_one = return_type_lib.get_arg_one_name_from_function_signature(elem2[0])
                                    
                                    result = common_stuff_lib.is_type_known(arg_one)
                                    
  
                                    if result == False:
                                        #print(f'Error arg_one')
                                        pass
                                    else:
                                        tmp_att_dis = att_dis
                                        #print(f'len att-dis 1 >{len(tmp_att_dis)}<')
                                        tmp_att_dis = disassembly_lib.clean_att_disassembly_from_comment(tmp_att_dis)
                                        callee_dis = disassembly_lib.clean_att_disassembly_from_comment(elem2[4])
                                        #print(f'len att-dis 1 >{len(tmp_att_dis)}<')
                                        #print(f'att-dis >{tmp_att_dis}<')
                                        
                                        dis1_str = ' '.join(tmp_att_dis)
                                        #dis2_str = ' '.join(elem2[4])
                                        dis2_str = ' '.join(callee_dis)
                                        
                                        dis1_str = disassembly_lib.split_disassembly(dis1_str)
                                        dis2_str = disassembly_lib.split_disassembly(dis2_str)
                                        #dis1_str = dis_split(dis1_str)
                                        #dis2_str = dis_split(dis2_str)
                                        
                                        ##the max-seq-length blows memory (>160GB ram) with model.fit() if e.g. over 6million
                                        if (len(dis1_str) > 100000) or (len(dis2_str) > 100000) or (len(dis1_str) < 1) or (len(dis2_str) < 1):
                                            print(f'dis1_str >{len(dis1_str)}<')
                                            print(f'dis2_str >{len(dis2_str)}<')
                                            #print(f"package >{elem[2]}< bin >{elem[3]}< file >{elem[6]}< func >{elem[7]}<")
                                            #print(f"package >{elem2[2]}< bin >{elem2[3]}< file >{elem2[6]}< func >{elem2[7]}<")
                                            
                                        else:
                                            dis_str = dis1_str + dis2_str
                                                
                                            #print(f'dis_str >{dis_str}<')
                                        
                                            dataset_list.append((dis_str, arg_one))
                                            counter += 1
                                            
                                        break
                  
           
    if dataset_list:
        if config['save_file_type'] == 'pickle':     
            ret_file = open(config['save_dir'] + os.path.basename(pickle_file).replace('.tar.bz2', ''), 'wb+')
            pickle_list = pickle.dump(dataset_list, ret_file)
            ret_file.close()
        else:
            ## save as tfrecord
            dis_list = list()
            ret_list = list()
            
            for item in dataset_list:
                dis_list.append(item[0])
                ret_list.append(item[1])
                
            raw_dataset = tf.data.Dataset.from_tensor_slices( (dis_list, ret_list ))
        
            serialized_features_dataset = raw_dataset.map(tf_serialize_example)
            
            filename = config['save_dir']  + os.path.basename(tarbz2_file).replace('.pickle.tar.bz2','') + '.tfrecord'
            writer = tf.data.experimental.TFRecordWriter(filename)
            writer.write(serialized_features_dataset)
    
    
                  
    return counter
    

def main():
    config = parseArgs()
    
    check_config(config)

    nr_of_cpus = psutil.cpu_count(logical=True)
    print(f'We got nr_of_cpus >{nr_of_cpus}<')
    
    pickle_files = common_stuff_lib.get_all_filenames_of_type(config['pickle_dir'], '.tar.bz2')
    ### print 5 files, check and debug
    pickle_lib.print_X_pickle_filenames(pickle_files, 5)
    
     ### build
    p = Pool(nr_of_cpus)
    
    
    pickle_files = [config["pickle_dir"] + "/" + f for f in pickle_files]
    star_list = zip(pickle_files, repeat(config['work_dir']), repeat(config['save_dir']), repeat(config))
    all_ret_types = p.starmap(proc_build, star_list)
    p.close()
    p.join()
    
    print(f'Run build_ret_type__vocab__seq_len.py next')

if __name__ == "__main__":
    main()
    
    
