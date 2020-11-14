import os
import getopt
import sys
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.layers.experimental.preprocessing import TextVectorization
from tensorflow.keras.layers import Activation, Dense, Embedding, GlobalAveragePooling1D

sys.path.append('../../lib/')
import pickle_lib

print(tf.version.VERSION)


def parseArgs():
    short_opts = 'hc:'
    long_opts = ['checkpoint-dir=']
    config = dict()
    
    config['checkpoint_dir'] = ''
 
    try:
        args, rest = getopt.getopt(sys.argv[1:], short_opts, long_opts)
    except getopt.GetoptError as msg:
        print(msg)
        print(f'Call with argument -h to see help')
        exit()
    
    for option_key, option_value in args:
        if option_key in ('-c', '--checkpoint-dir'):
            config['checkpoint_dir'] = option_value[1:]
        elif option_key in ('-h'):
            print(f'<optional> -c or --checkpoint-dir The directory with model checkpoint Default:')
           
           
    if config['checkpoint_dir'] == '':
        config['checkpoint_dir'] = ''
    
            
    return config

def check_config(config):
    if not os.path.isdir(config['checkpoint_dir']):
        print(f"Please specify model checkpoint dir, -h for help")
        exit()


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
    
    ret_type_dict = pickle_lib.get_pickle_file_content('/home/ubu/Documents/gcp-caller-callee/arg_one/' + 'return_type_dict.pickle')
    
    for item in ret:
        result = 0
        biggest = 0
        biggest_count = 0
        counter = 0
        for i in item:
            if i > biggest:
                biggest = i
                biggest_count = counter
            counter += 1
            #print(f'item >{i}<')
            result += i
        for ret in ret_type_dict:
            if ret_type_dict[ret] == biggest_count:
                print(f'argument one is of type >{ret}<')
    
    print(f'Does last count together to 1 ? Result: >{result}<')
    
    
    
    

if __name__ == "__main__":
    main()
    
    