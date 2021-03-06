import tarfile
import os
import sys
import pickle
import tensorflow as tf
from datetime import datetime
from multiprocessing import Pool
import getopt
from itertools import repeat
sys.path.append('../../lib/')
import return_type_lib
import common_stuff_lib
import tarbz2_lib
import pickle_lib
import disassembly_lib
import tfrecord_lib

nr_of_cpus = 16



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
    
        
   
def dis_split(dis):
    dis_list = list()
        
    for line in dis.split('\t'):
        #print(f'One line-----------')
        #print(f'line: >{line}<')
        
        line = line.replace('(', ' ( ')
        line = line.replace(')', ' ) ')
        line = line.replace('%', ' % ')
        line = line.replace(',', ' , ')
        line = line.replace('$', ' $ ')
        line = line.replace('*', ' * ')
        line = line.replace('<', ' < ')
        line = line.replace('>', ' > ')
        line = line.replace('+', ' + ')
        line = line.replace('@', ' @ ')
        line = line.replace(':', ' : ')
        #print(f'line after giving space: >{line}<')
        
        new_line = ''
        for item in line.split():
            #print(f'One item of one line >{item}<')
            ## check if we got a hex nr with chars
            new_item = ''
            if (len(item) >= 2) and item[0] == '0' and item[1] == 'x':
                #print(f'Found Hex >{item}<, split it into single numbers and chars')
                for c in item:
                    ### replace '0' with 'null'  ,for textVectorize where '0' is masked-value
                    if c == '0':
                        c = 'null'
                    new_item = new_item + c + ' '
                    
                #print(f'Split hex to >{new_item}<')
            else:
                #print(f'No hex found, check for nr')
                length = len(item)
                #print(f'length >{length}<')
                if length > 1:
                    for c in item:
                        if str.isnumeric(c):
                            ### replace '0' with 'null'  ,for textVectorize where '0' is masked-value
                            if c == '0':
                                c = 'null'
                            new_item = new_item + c + ' '
                        else:
                            new_item = new_item + c
                    
#                         for i in range(length):
#                             if isnumeric(item[i]):
#                                 c = item[i]
#                                 new_item = new_item + c + ' '
#                                 #print(f'Found number >{item[i]}< new_item >{new_item}<')
#                             else:
#                                 new_item = new_item + c
#                                 #print(f'No number >{item[i]}<  new_item >{new_item}<')
                else:
                    new_item = item
        
            ### add ' ' ,so that in next line it got a space between the strings for new_line
            if not new_item.endswith(' '):
                new_item = new_item + ' '
            #print(f'old item >{item}< new_item: >{new_item}<')        
            
            
            new_line = new_line + new_item
         
        #print(f'new_line >{new_line}<')   
               

        #exit()         
        dis_list.append(new_line)
    
    
    #print(f'Full disas: >{dis_list}<')
    dis_str = ' '.join(dis_list)   
    
    return dis_str


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
                                    
                                    return_type_func_sign = return_type_lib.get_return_type_from_function_signature(elem2[0])
                                    return_type = return_type_lib.get_return_type_from_gdb_ptype(elem2[1])
                                    
                                    ###for debugging, what string is still unknown ?? should show nothing
                                    if return_type == 'unknown':
                                        print(f'string_before_func_name: {string_before_func_name}')
                                     
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
                                            
                                        dis1_str = ' '.join(att_dis)
                                        dis2_str = ' '.join(elem2[4])
                                        
                                        dis1_str = disassembly_lib.split_disassembly(dis1_str)
                                        dis2_str = disassembly_lib.split_disassembly(dis2_str)
                                        #dis1_str = dis_split(dis1_str)
                                        #dis2_str = dis_split(dis2_str)
                                        
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
    
    
                  
    return counter
    
    
def check_if_dir_exists(dir):
    if not os.path.isdir(dir):
        print(f'Directory >{dir}< does not exist. Create it.')
        exit()
  
def main():
    config = parseArgs()
    
    print(f'config >{config}<')
    
    check_if_dir_exists(config['pickle_dir'])
    check_if_dir_exists(config['work_dir'])
    check_if_dir_exists(config['save_dir'])
    check_if_dir_exists(config['tfrecord_save_dir'])
    
     
    ### get all pickle files
    #pickle_files = get_all_tar_filenames(config['pickle_dir'])
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
    
    
    
    ## build return type dict-file and max-seq-length-file and vocabulary
    pickle_files = common_stuff_lib.get_all_filenames_of_type(config['save_dir'], '.pickle')
    print(f'pickle-files >{pickle_files}<')
    
    print(f'Building return-type dict, vocabulary and max-squenece-length')
    ret_set = set()
    vocab = set()
    seq_length = 0
    counter = 1
    pickle_count = len(pickle_files)
    
    for file in pickle_files:
        print(f'File >{file}< >{counter}/{pickle_count}<', end='\r')
        counter += 1
        cont = pickle_lib.get_pickle_file_content(config['save_dir'] + file)
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
        
    print(f"Build return-type dict and save it to >{config['return_type_dict_file']}<")        
    ## build ret-type-dict and save
    ret_type_dict = dict()
    counter = 0
    for elem in ret_set:
        ret_type_dict[elem] = counter
        counter += 1
    
    pickle_lib.save_to_pickle_file(ret_type_dict, config['return_type_dict_file'])
        
    print(f"Build vocabulary and save it to >{config['vocabulary_file']}<")
    ## build vocabulary list from set and save
    vocab_list = list(vocab)
    pickle_lib.save_to_pickle_file(vocab_list, config['vocabulary_file'])
    
    ## save max-seq-length
    print(f"Saving max-sequence-length to >{config['max_seq_length_file']}<")
    pickle_lib.save_to_pickle_file(seq_length, config['max_seq_length_file'])
    
    ### transform dataset ret-types to ints
    print(f"Transform return-type to int and save to >{config['tfrecord_save_dir']}<")
    trans_ds = list()
    counter = 1
    for file in pickle_files:
        print(f'Transform File >{file}< >{counter}/{pickle_count}<', end='\r')
        counter += 1
        cont = pickle_lib.get_pickle_file_content(config['save_dir'] + file)
        for item in cont:
            trans_ds.append( (item[0], ret_type_dict[item[1]]) )
            
        tfrecord_lib.save_caller_callee_to_tfrecord(trans_ds, config['tfrecord_save_dir'] + file.replace('.pickle', '.tfrecord'))
    
    
    
    print("Splitting dataset to train,val,test")
    tfrecord_lib.split_to_train_val_test(config['tfrecord_save_dir'])
    
    
    print("Done. Run build_caller_callee_model.py now")
#     for counter in all_ret_types:
#         if counter > 0:
#             print(f'disassemblies saved >{counter}<')
#             break
    
    
if __name__ == "__main__":
    main()

    