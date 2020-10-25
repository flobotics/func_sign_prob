import getopt
import sys
import os
import pickle
from multiprocessing import Pool
from itertools import repeat
import tensorflow as tf

nr_of_cpus = 16

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


def proc_build_list_with_label_ints(file, save_dir, ret_type_dict):
    #global ret_type_dict
    
    ds_counter = 0
    
    ret_list = list()
            
    cont = get_pickle_file_content(file)
    for dis,ret in cont:
        
        ret_type_int = ret_type_dict[ret] -1
        
        #ret_list.append( (dis, ret_type_int) )
        ret_list.append( (dis.encode('utf-8'), ret_type_int) )
        


    ret_file = open(save_dir + os.path.basename(file), 'wb+')
    pickle_list = pickle.dump(ret_list, ret_file)
    ret_file.close()
    
    #return ret_list

def parseArgs():
    short_opts = 'hp:c:t:d:v:s:l:i:r:t:'
    long_opts = ['pickle-dir=', 'checkpoint-dir=', 'tensorboard-log-dir=', 'tf-dataset-save-dir=', 'vocab-file=',
                 'vocab-size-file=', 'seq-length-file=', 'label-ints-dir=', 'tf-record-dir=', 'ret-type-dict-file=']
    config = dict()
    
    config['pickle_dir'] = '/tmp/save_dir'
    config['checkpoint_dir'] = '/tmp/logs/checkpoint'
    config['tensorboard_log_dir'] = '/tmp/logs'
    config['tf_dataset_save_dir'] = '/tmp/logs/tf_dataset_dir'
    config['vocab_file'] = ''
    config['vocab_size_file'] = ''
    config['seq_length_file'] = ''
    config['label_ints_dir'] = '/tmp/label-ints-dir/'
    config['tf_record_dir'] = '/tmp/tf_record_dir/'
    config['ret_type_dict_file'] = "/tmp/ret_type_dict.pickle"
    
    try:
        args, rest = getopt.getopt(sys.argv[1:], short_opts, long_opts)
    except getopt.GetoptError as msg:
        print(msg)
        print(f'Call with argument -h to see help')
        exit()
    
    for option_key, option_value in args:
        if option_key in ('-p', '--pickle-dir'):
            config['pickle_dir'] = option_value[1:]
        elif option_key in ('-c', '--checkpoint-dir'):
            config['checkpoint_dir'] = option_value[1:]
        elif option_key in ('-t', '--tensorboard-log-dir'):
            config['tensorboard_log_dir'] = option_value[1:]
        elif option_key in ('-d', '--tf-dataset-save-dir'):
            config['tf_dataset_save_dir'] = option_value[1:]
        elif option_key in ('-v', '--vocab-file'):
            config['vocab_file'] = option_value[1:]
        elif option_key in ('-s', '--vocab-size-file'):
            config['vocab_size_file'] = option_value[1:]
        elif option_key in ('-l', '--seq-length-file'):
            config['seq_length_file'] = option_value[1:]
        elif option_key in ('-i', '--label-ints-dir'):
            config['label_ints_dir'] = option_value[1:]
        elif option_key in ('-r', '--tf-record-dir'):
            config['tf_record_dir'] = option_value[1:]
        elif option_key in ('-t', '--ret-type-dict-file'):
            config['ret_type_dict_file'] = option_value[1:]
        elif option_key in ('-h'):
            print(f'<optional> -p or --pickle-dir The directory with disassemblies,etc. Default: /tmp/save_dir')
            print(f'<optional> -w or --checkpoint-dir   The directory where we store tensorflow checkpoints Default: /tmp/logs/checkpoint')
            print(f'<optional> -v or --vocab-file   The file with the vocabulary. Default: None')
            print(f'<optional> -s or --vocab-size-file  The file with the size of the vocabulary. Default: None')
            print(f'<optional> -l or --seq-length-file   The file with the sequence lenght. Default: None')
            print(f'<optional> -i or --label-ints-dir   The directory we store pickles with string,int tuples')
            print(f'<optional> -r or --tf-record-dir   The directory we store tfrecord files')
            print(f'<optional> -t or --ret-type-dict-file  The file with the return types dictionary.  Default: /tmp/ret_type_dict.pickle')
            
    return config   


def does_file_exist(file):
    if os.path.isfile(file):
        print(f'File >{file}< exists')
    else:
        print(f'File >{file}< does not exist')
        exit()
        
        

def check_if_dir_exists(dir):
    if not os.path.isdir(dir):
        print(f'Directory >{dir}< does not exist. Create it.')
        exit()
    
def check_dir_and_files_exists(config):
    ### check, else exit and inform user
    check_if_dir_exists(config['pickle_dir'])
    #check_if_dir_exists(config['label_ints_dir'])
    check_if_dir_exists(config['tf_record_dir'])
    
    if config['vocab_file']:
        does_file_exist(config['vocab_file'])
    if config['vocab_size_file']:
        does_file_exist(config['vocab_size_file'])
    if config['seq_length_file']:
        does_file_exist(config['seq_length_file'])
    #if config['ret_type_dict_file']:
    #    does_file_exist(config['ret_type_dict_file'])
        

def print_info(config):
    if config['vocab_size_file']:
        print(f'Vocabulary size read from file >{config["vocab_size_file"]}< is >{vocab_size}<')
    if config['seq_length_file']:
        print(f'Sequence length read from file >{config["seq_length_file"]}< is >{sequence_length}<')
    print(f'TF Record directory is >{config["tf_record_dir"]}<')
       
       
def get_vocab(config):
    vocab_word_list = list()
    
    ### get vocabulary, to feed into textvectorization.set_vocabulary() , much faster than .adapt()
    if config['vocab_file']:
        print(f'We got a vocabulary file, so we use it')
        vocab_ret1 = get_pickle_file_content(config['vocab_file'])
        
        c = 0
        vocab_ret = list(vocab_ret1)
        print(f'Print 3 words from our vocabulary')
        for key in vocab_ret:
            if c <= 2:
                print(f'vocab key >{key}<')
                c += 1
            vocab_word_list.append(str(key))
            
    return vocab_word_list
                 
            
def proc_build_tfrecord(file, tf_record_dir):
    dis_list = list()
    ret_list = list()

    
    #cont = get_pickle_file_content(config['pickle_dir'] + '/' + file)
    cont = get_pickle_file_content(file)
    

    print(f'From file >{file}<', end='\r')

    
    for dis,ret in cont:
        dis_list.append(dis)
        ret_list.append(ret)
         
    raw_dataset = tf.data.Dataset.from_tensor_slices( (dis_list, ret_list ))

    ## ValueError: Can't convert Python sequence with mixed types to Tensor.
    ##raw_dataset = tf.data.Dataset.from_tensor_slices(cont)
      
    ds_counter += 1
    
    serialized_features_dataset = raw_dataset.map(tf_serialize_example)
#             serialized_features_dataset = tf.data.Dataset.from_generator(
#                                                 generator, output_types=tf.string, output_shapes=())
    

    filename = tf_record_dir + file.replace('.pickle','') + '.tfrecord'
    writer = tf.data.experimental.TFRecordWriter(filename)
    writer.write(serialized_features_dataset)
            
            
            
def main():
    config = parseArgs()

    ### check if the dirs and files needed are there, else exit
    check_dir_and_files_exists(config)
    
    ##print what files/dirs are used
    print_info(config)
    
    ## 
    ### build ds from tokenized files, then get texts
    print(f'Building tf.data.Dataset from tokenized files from dir >{config["pickle_dir"]}<')
    ds_counter = 0
#     pickle_files = get_all_pickle_filenames(config["pickle_dir"])
#     nr_of_pickle_files = len(pickle_files)
    pickle_file_counter = 0
    dis_counter = 1
    
    #### convert string return type to int
#     p = Pool(nr_of_cpus)
#     
#     ret_type_dict = get_pickle_file_content(config['ret_type_dict_file'])
#     
#     pickle_files = [config["pickle_dir"] + "/" + f for f in pickle_files]
#     star_list = zip(pickle_files, repeat(config['label_ints_dir']), repeat(ret_type_dict))
#     all_ret_types = p.starmap(proc_build_list_with_label_ints, star_list)
#     #p.map(proc_build_list_with_label_ints, pickle_files )
#     p.close()
#     p.join()    
        
    
    ds_counter = 0
    
    print(f'Build tf dataset now')
    
    
    pickle_files_int = get_all_pickle_filenames(config["pickle_dir"])
    nr_of_pickle_files = len(pickle_files_int)
    
    p = Pool(nr_of_cpus)
    
    
    pickle_files = [config["pickle_dir"] + "/" + f for f in pickle_files_int]
    star_list = zip(pickle_files, repeat(config['tf_record_dir']))
    all_ret_types = p.starmap(proc_build_tfrecord, star_list)
    p.close()
    p.join()
    
    
    #for counter in all_ret_types:
        
        
    
#    for file in pickle_files_int:
#         dis_list.clear()
#         ret_list.clear()
#         
#         cont = get_pickle_file_content(config['pickle_dir'] + '/' + file)
#         
#         if (ds_counter+1) >= nr_of_pickle_files:
#             print(f'From file >{config["pickle_dir"] + file}< nr >{ds_counter+1}/{nr_of_pickle_files}<', end='\n')
#         else:
#             print(f'From file >{config["pickle_dir"] + file}< nr >{ds_counter+1}/{nr_of_pickle_files}<', end='\r')
#     
#         
#         for dis,ret in cont:
#             dis_list.append(dis)
#             ret_list.append(ret)
#              
#         raw_dataset = tf.data.Dataset.from_tensor_slices( (dis_list, ret_list ))
# 
#         ## ValueError: Can't convert Python sequence with mixed types to Tensor.
#         ##raw_dataset = tf.data.Dataset.from_tensor_slices(cont)
#           
#         ds_counter += 1
#         
#         serialized_features_dataset = raw_dataset.map(tf_serialize_example)
# #             serialized_features_dataset = tf.data.Dataset.from_generator(
# #                                                 generator, output_types=tf.string, output_shapes=())
#         
# 
#         filename = config['tf_record_dir'] + file.replace('.pickle','') + '.tfrecord'
#         writer = tf.data.experimental.TFRecordWriter(filename)
#         writer.write(serialized_features_dataset)


    ## now get number of tfrecord files, and split numbers
    files = os.listdir(config['tf_record_dir'])
    nr_of_files = len(files)
    
    print(f'We got >{nr_of_files}< tfrecord files')
    train_size = int(0.7 * nr_of_files)
    val_size = int(0.15 * nr_of_files)
    test_size = int(0.15 * nr_of_files)
    print(f'We split to train >{train_size}< val >{val_size}< test >{test_size}<')
    
    ## create train,val,test dir
    os.mkdir(config['tf_record_dir'] + 'train')
    os.mkdir(config['tf_record_dir'] + 'val')
    os.mkdir(config['tf_record_dir'] + 'test')
    
    ## move files to extra dirs
    counter = 1
    for file in files:
        if counter <= train_size:
            os.rename(config['tf_record_dir'] + file, config['tf_record_dir'] + 'train/' + file)
            counter += 1
        elif counter <= (train_size + val_size):
            os.rename(config['tf_record_dir'] + file, config['tf_record_dir'] + 'val/' + file)
            counter += 1
        else:
            os.rename(config['tf_record_dir'] + file, config['tf_record_dir'] + 'test/' + file)
            
    

if __name__ == "__main__":
    main()