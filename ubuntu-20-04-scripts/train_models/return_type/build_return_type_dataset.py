# from multiprocessing import set_start_method
# set_start_method("spawn")
import tarfile
import os
import sys
import pickle
#import tensorflow as tf
from datetime import datetime
from multiprocessing import Pool
from multiprocessing import Process
import multiprocessing as mp
import getopt
from itertools import repeat
import psutil
from shutil import copyfile


sys.path.append('../../lib/')
import return_type_lib
import common_stuff_lib
import tarbz2_lib
import pickle_lib
import disassembly_lib
#import tfrecord_lib




def print_one_pickle_list_item(pickle_file_content):
    item = next(iter(pickle_file_content))
    if item:
        print(f'function-signature: {item[0]}')
        print(f'gdb-ptype: {item[1]}')
        print(f'function-name: {item[2]}')
        print(f'function-file-name: {item[3]}')
        print(f'disassembly-att: {item[4]}')
        print(f'disassembly-intel: {item[5]}')
        print(f'package-name: {item[6]}')
        print(f'binary-name: {item[7]}')
    else:
        print('Error item[0]')



def serialize_example(feature0, feature1):
    """
    Creates a tf.train.Example message ready to be written to a file.
    """
    # Create a dictionary mapping the feature name to the tf.train.Example-compatible
    # data type.
    feature0 = feature0.numpy()
    feature1 = feature1.numpy()
    feature = {
              'caller_callee': tf.train.Feature(bytes_list=tf.train.BytesList(value=[feature0])),
              'label': tf.train.Feature(bytes_list=tf.train.BytesList(value=[feature1])),
    }
    
    # Create a Features message using tf.train.Example.
    
    example_proto = tf.train.Example(features=tf.train.Features(feature=feature))
    return example_proto.SerializeToString()  

    
    
def tf_serialize_example(f0,f1):
    tf_string = tf.py_function(
      serialize_example,
      (f0,f1),  # pass these args to the above function.
      tf.string)      # the return type is `tf.string`.
    return tf.reshape(tf_string, ()) # The result is a scalar  


 
def proc_build(tarbz2_file, work_dir, save_dir, config):
#     with get_context("spawn").Pool() as pool:
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
    ## 6. save caller, callee, func_signature
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
                                    
                                    if (len(elem2[4]) > (int(config['tokenized_disassembly_length'])/2)) or (len(att_dis) > (int(config['tokenized_disassembly_length'])/2)) or (len(elem2[4]) < 1) or (len(att_dis) < 1):
                                        continue
                                    
                                    return_type_func_sign = return_type_lib.get_return_type_from_function_signature(elem2[0])
                                    return_type = return_type_lib.get_return_type_from_gdb_ptype(elem2[1])
                                    
                                    ###for debugging, what string is still unknown ?? should show nothing
                                    if return_type == 'unknown':
                                        print(f'string_before_func_name: {return_type_func_sign}')
                                     
                                    if return_type == 'unknown':
                                        #print('unknown found')
                                        #breaker = True
                                        #break
                                        pass
                                    elif return_type == 'delete':
                                        #print('delete found')
                                        ### no return type found, so delete this item
                                        pass
                                    elif return_type == 'process_further':
                                        print(f'ERRROOOORRRR---------------')
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
                                        if (len(dis1_str) > (int(config['tokenized_disassembly_length'])/2)) or (len(dis2_str) > (int(config['tokenized_disassembly_length'])/2)) or (len(dis1_str) < 1) or (len(dis2_str) < 1):
                                            #print(f'tokenized_disassembly_length caller >{len(dis1_str)}<')
                                            #print(f'tokenized_disassembly_length callee >{len(dis2_str)}<')
                                            #print(f"package >{elem[2]}< bin >{elem[3]}< file >{elem[6]}< func >{elem[7]}<")
                                            #print(f"package >{elem2[2]}< bin >{elem2[3]}< file >{elem2[6]}< func >{elem2[7]}<")
                                            pass
                                        else:
                                            dis_str = dis1_str + dis2_str
                                                
                                            #print(f'dis_str >{dis_str}<')
                                        
                                            dataset_list.append((dis_str, return_type))
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
    
    
                  
    #return counter
    
    
def check_config(config):
    if config['base_dir'] == '':
        print(f'Please specify a base-dir (-b or --base-dir) , where all work is done. Check -h for help.')
        exit()
        
    if not os.path.isdir(config['git_repo_path']):
        print(f"There is no git repo at >{config['git_repo_path']}<")
        exit()
        
    if not os.path.isdir(config['base_dir']):
        print(f"Creating >{config['base_dir']}<")
        os.mkdir(config['base_dir'])
        
    if not os.path.isdir(config['pickle_dir']):
        print(f"Creating >{config['pickle_dir']}<")
        os.mkdir(config['pickle_dir']) 
        
    if not os.path.isdir(config['work_dir']):
        print(f"Creating >{config['work_dir']}<")
        os.mkdir(config['work_dir'])
    
    if not os.path.isdir(config['save_dir']):
        print(f"Creating >{config['save_dir']}<")
        os.mkdir(config['save_dir'])
        
    if not os.path.isdir(config['tfrecord_save_dir']):
        print(f"Creating >{config['tfrecord_save_dir']}<")
        os.mkdir(config['tfrecord_save_dir'])
        
    print(f'config >{config}<')
    print() 
  
  
def copy_files_to_build_dataset(config):
    pickle_files = common_stuff_lib.get_all_filenames_of_type(config['pickle_dir'], '.tar.bz2')
    if len(pickle_files) > 0:
        decision = 'z'
        while( (decision != 'y') and (decision != 'n' ) ):
            decision = input(f"There are still files in >{config['pickle_dir']}< . Do you want to use them: Type in (y/n):")
    
        if decision == 'y':
            print(f'Using files still there')
            return
            
    pickle_path = config['git_repo_path'] + '/ubuntu-20-04-pickles/'
    
    pickle_files = common_stuff_lib.get_all_filenames_of_type(pickle_path, '.tar.bz2')
    counter = 0
    for file in pickle_files:
        counter += 1
      
    nr_files = 'z'
    while( not nr_files.isdecimal()):
        nr_files = input(f'In directory >{pickle_path}< are >{counter}< files.\nHow many files to use for dataset? Type in:')
    
    counter = 0
    for file in pickle_files:
        print(f'Copy file >{file}<                 ', end='\r')
        copyfile(pickle_path + file, config['pickle_dir'] + file)
        counter += 1
        if counter >= int(nr_files):
            break
        
    print(f'Copied >{nr_files}< files')
    print()


      
# def main():
    
    
    

    
if __name__ == "__main__":
    mp.set_start_method("forkserver")
    
    config = common_stuff_lib.parseArgs()
    check_config(config)
    
    nr_of_cpus = psutil.cpu_count(logical=True)
    print(f'We got >{nr_of_cpus}< CPUs for threading\n')
    print()
    
    copy_files_to_build_dataset(config)
    
    ### get all pickle files
    #pickle_files = get_all_tar_filenames(config['pickle_dir'])
    pickle_files = common_stuff_lib.get_all_filenames_of_type(config['pickle_dir'], '.tar.bz2')
    ### print 5 files, check and debug
    pickle_lib.print_X_pickle_filenames(pickle_files, 5)
    
    
    ### build
    #p = Pool(nr_of_cpus)
    #p = Pool(len(pickle_files))
     
     
    pickle_files = [config["pickle_dir"] + "/" + f for f in pickle_files]
    star_list = zip(pickle_files, repeat(config['work_dir']), repeat(config['save_dir']), repeat(config))
    #p = list(len(pickle_files))
    #i = 0
    process_list = list()
    for file in pickle_files:
        p = Process(target=proc_build, args=(file, config['work_dir'], config['save_dir'], config) )
        process_list.append(p)
        p.start()
        #p.join()
    
    
#     
#     all_ret_types = p.starmap(proc_build, star_list)
#     p.close()
#     p.join()
      
    
    print("Done. Run build_ret_type__vocab__seq_len.py next")
#     main()

    