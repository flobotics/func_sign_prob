import os
import getopt
import sys
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.layers.experimental.preprocessing import TextVectorization
from tensorflow.keras.layers import Activation, Dense, Embedding, GlobalAveragePooling1D

sys.path.append('../../lib/')
import pickle_lib




def parseArgs():
    short_opts = 'hc:s:r:m:v:'
    long_opts = ['checkpoint-dir=', 'save-dir=', 'return-type-dict-file', 'max-seq-length-file=', 'vocab-file=']
    config = dict()
    
    config['save_dir'] = ''
    config['checkpoint_dir'] = ''
    config['return_type_dict_file'] = ''
    config['max_seq_length_file'] = ''
    config['vocabulary_file'] = ''
    
 
    try:
        args, rest = getopt.getopt(sys.argv[1:], short_opts, long_opts)
    except getopt.GetoptError as msg:
        print(msg)
        print(f'Call with argument -h to see help')
        exit()
    
    for option_key, option_value in args:
        if option_key in ('-c', '--checkpoint-dir'):
            config['checkpoint_dir'] = option_value[1:]
        elif option_key in ('-s', '--save-dir'):
            config['save_dir'] = option_value[1:]
        elif option_key in ('-r', '--return-type-dict-file'):
            config['return_type_dict_file'] = option_value[1:]
        elif option_key in ('-m', '--max-seq-length-file'):
            config['max_seq_length_file'] = option_value[1:]
        elif option_key in ('-v', '--vocab-file'):
            config['vocabulary_file'] = option_value[1:]
        elif option_key in ('-h'):
            print(f'<optional> -c or --checkpoint-dir The directory with model checkpoint Default:')
            print(f'<optional> -s or --save-dir   The directory where we save dataset.  Default: /tmp/save_dir')
           
           
    if config['save_dir'] == '':
        config['save_dir'] = '/tmp/save_dir/'
    if config['checkpoint_dir'] == '':
        config['checkpoint_dir'] = ''
    if config['return_type_dict_file'] == '':
        config['return_type_dict_file'] = config['save_dir'] + 'tfrecord/' + 'return_type_dict.pickle'
    if config['max_seq_length_file'] == '':
        config['max_seq_length_file'] = config['save_dir'] + 'tfrecord/' + 'max_seq_length.pickle'
    if config['vocabulary_file'] == '':
        config['vocabulary_file'] = config['save_dir'] + 'tfrecord/' + 'vocabulary_list.pickle'
    
            
    return config

def check_config(config):
    if not os.path.isdir(config['checkpoint_dir']):
        print(f"Directory >{config['checkpoint_dir']}< does not exist. Please specify model checkpoint dir, -h for help")
        exit()
        
#     if not os.path.isdir(config['save_dir']):
#         print(f"Directory >{config['save_dir']}< does not exist. Please specify save_dir dir, -h for help")
#         exit()
    
    

###load vocabulary list
vocabulary = pickle_lib.get_pickle_file_content('/home/ubu/Documents/gcp-caller-callee/arg_one/' + 'vocabulary_list.pickle')

###load max-sequence-length 
max_seq_length = pickle_lib.get_pickle_file_content('/home/ubu/Documents/gcp-caller-callee/arg_one/' + 'max_seq_length.pickle')
print(f'len-vocab-from-file >{len(vocabulary)}<')
vectorize_layer = TextVectorization(standardize=None,
                                    max_tokens=len(vocabulary)+2,
                                    output_mode='int',
                                    output_sequence_length=max_seq_length)

def main():
    
    print(f'Tensorflow version is >{tf.version.VERSION}<')
    
    config = parseArgs()
    
    check_config(config)
    
    model = tf.keras.models.load_model(config['checkpoint_dir'] + 'saved_model/')

    model.summary()

    export_model = tf.keras.Sequential([vectorize_layer,
                                          model,
                                          tf.keras.layers.Activation('softmax')
                                        ])

#     export_model = tf.keras.Sequential([vectorize_layer,
#                                           model
#                                         ])

    examples = ['null x null 1 mov']
    ret = export_model.predict(examples)
    print(f"Prediction: >{ret}<")
    print()  ##just a newline
    
    ret_type_dict = pickle_lib.get_pickle_file_content('/home/ubu/Documents/gcp-caller-callee/arg_one/' + 'return_type_dict.pickle')
    
    reverse_ret_type_dict = dict()
    counter = 0
    for key in ret_type_dict:
        reverse_ret_type_dict[counter] = key
        counter += 1
    
    for item in ret:
        result = 0
        biggest = 0
        biggest_count = 0
        counter = 0
        for i in item:
            if i > biggest:
                biggest = i
                biggest_count = counter
            
            print(f'ret-type >{reverse_ret_type_dict[counter] : <{30}}< got probability of >{i}<')
            counter += 1
            
            result += i
        for ret in ret_type_dict:
            if ret_type_dict[ret] == biggest_count:
                print()
                print(f'argument one is of type >{ret}<')
    
    print()
    print(f'Does last count together to 1 ? Result: >{result}<')
    
    
    
    

if __name__ == "__main__":
    main()
    
    