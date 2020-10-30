import getopt
import tensorflow as tf
import sys
import os



def parseArgs():
    short_opts = 'hs:w:t:r:m:v:f:'
    long_opts = ['work-dir=', 'save-dir=', 'save-file-type=', 
                 'return-type-dict-file', 'max-seq-length-file=', 'vocab-file=', 'tfrecord-dir=']
    config = dict()
    
    config['work_dir'] = ''
    config['save_dir'] = ''
    config['save_file_type'] = ''
    config['return_type_dict_file'] = ''
    config['max_seq_length_file'] = ''
    config['vocabulary_file'] = ''
    config['tfrecord_dir'] = ''
 
    try:
        args, rest = getopt.getopt(sys.argv[1:], short_opts, long_opts)
    except getopt.GetoptError as msg:
        print(msg)
        print(f'Call with argument -h to see help')
        exit()
    
    for option_key, option_value in args:
        if option_key in ('-w', '--work-dir'):
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
        elif option_key in ('-f', '--tfrecord-dir'):
            config['tfrecord_dir'] = option_value[1:]
        elif option_key in ('-h'):
            print(f'<optional> -p or --pickle-dir The directory with disassemblies,etc. Default: ubuntu-20-04-pickles')
            print(f'<optional> -w or --work-dir   The directory where we e.g. untar,etc. Default: /tmp/work_dir/')
            print(f'<optional> -s or --save-dir   The directory where we save dataset.  Default: /tmp/save_dir')
            
    if config['work_dir'] == '':
        config['work_dir'] = '/tmp/work_dir/'
    if config['save_dir'] == '':
        config['save_dir'] = '/tmp/save_dir/'
    if config['save_file_type'] == '':
        config['save_file_type'] = 'pickle'
    if config['return_type_dict_file'] == '':
        config['return_type_dict_file'] = '/tmp/return_type_dict.pickle'
    if config['max_seq_length_file'] == '':
        config['max_seq_length_file'] = '/tmp/max_seq_length.pickle'
    if config['vocabulary_file'] == '':
        config['vocabulary_file'] = '/tmp/vocabulary_list.pickle'
    if config['tfrecord_dir'] == '':
        config['tfrecord_dir'] = config['save_dir'] + 'tfrecord/'
    
            
    return config


def check_config(config):
    if not os.path.isdir(config['tfrecord_dir'] + 'train/'):
        print(f"Directory with train tfrecord files >{config['tfrecord_dir'] + 'train/'}< does not exist")
        exit()
        
    if not os.path.isdir(config['tfrecord_dir'] + 'val/'):
        print(f"Directory with train tfrecord files >{config['tfrecord_dir'] + 'val/'}< does not exist")
        exit()
        
    if not os.path.isdir(config['tfrecord_dir'] + 'test/'):
        print(f"Directory with train tfrecord files >{config['tfrecord_dir'] + 'test/'}< does not exist")
        exit()


def _parse_function(example_proto):
    # Create a description of the features.
    feature_description = {
      'caller_callee_disassembly': tf.io.FixedLenFeature([], tf.string, default_value=''),
      'callee_return_type_int': tf.io.FixedLenFeature([], tf.int64, default_value=0),
    }
    
    # Parse the input `tf.train.Example` proto using the dictionary above.
    ex = tf.io.parse_single_example(example_proto, feature_description)
    
    return ex['caller_callee_disassembly'], ex['callee_return_type_int']



def main():
    
    AUTOTUNE = tf.data.experimental.AUTOTUNE
    
    config = parseArgs()
    
    check_config(config)
    
    print(f"Build tf.data.dataset with tfrecord files from directory >{config['tfrecord_dir'] + 'train/'}< \
            >{config['tfrecord_dir'] + 'val/'}< >{config['tfrecord_dir'] + 'test/'}<")

    tfrecord_train_dataset = tf.data.Dataset.list_files(config['tfrecord_dir'] + 'train/' + '*.tfrecord')
    train_dataset = tf.data.TFRecordDataset(tfrecord_train_dataset)
    
    tfrecord_val_dataset = tf.data.Dataset.list_files(config['tfrecord_dir'] + 'val/' + '*.tfrecord')
    val_dataset = tf.data.TFRecordDataset(tfrecord_val_dataset)
    
    tfrecord_test_dataset = tf.data.Dataset.list_files(config['tfrecord_dir'] + 'test/' + '*.tfrecord')
    test_dataset = tf.data.TFRecordDataset(tfrecord_test_dataset)
    
    
    train_dataset = train_dataset.map(_parse_function, num_parallel_calls=AUTOTUNE)
    val_dataset = val_dataset.map(_parse_function, num_parallel_calls=AUTOTUNE)
    test_dataset = test_dataset.map(_parse_function, num_parallel_calls=AUTOTUNE)
    
    for text, label in train_dataset.take(1):
        print(f'One example from train_dataset with int-as-label:\nText: >{text}<\n Label: >{label}<')
        
    
    

if __name__ == "__main__":
    main()