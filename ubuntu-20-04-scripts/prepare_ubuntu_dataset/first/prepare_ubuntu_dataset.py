import getopt
import sys
import os
import tensorflow as tf
sys.path.append('../../lib/')
import tfrecord_lib


def parseArgs():
    short_opts = 'hw:t:v:'
    long_opts = ['work-dir=', 'tfrecord-save-dir=', 'verbose=']
    
    config = dict()
    
    config['work_dir'] = ''
    config['tfrecord_save_dir'] = ''
    config['config_dir'] = ''
    config['verbose'] = ''
    ###check little down for more configs
    
    try:
        args, rest = getopt.getopt(sys.argv[1:], short_opts, long_opts)
    except getopt.GetoptError as msg:
        print(msg)
        print(f'Call with argument -h to see help')
        exit()
    
    for option_key, option_value in args:
        if option_key in ('-w', '--work-dir'):
            config['work_dir'] = option_value[1:]
        elif option_key in ('-t', '--tfrecord-save-dir'):
            config['tfrecord_save_dir'] = option_value[1:]
        elif option_key in ('-v', '--verbose'):
            if option_value[1:] == 'False':
                config['verbose'] = False
            else:
                config['verbose'] = True
        elif option_key in ('-h'):
            print(f'<optional> -w or --work-dir The directory where all work is done. Default: /tmp/work')
            print(f'<optional> -b or --ubuntu-pwd The ubuntu user password to install packages with apt')
     
     
    if config['work_dir'] == '':
        config['work_dir'] = '/tmp/work/'
    if config['tfrecord_save_dir'] == '':
        config['tfrecord_save_dir'] = config['work_dir'] + 'tfrecord_files/'
    if config['verbose'] == '':
        config['verbose'] = True
    

           
    return config   


def check_config(config):
    if not os.path.isdir(config['tfrecord_save_dir']):
        print(f"Directory with tfrecord files does not exist >{config['tfrecord_save_dir']}<, check -h for help")
        exit()


# def get_all_tfrecord_filenames(tfrecord_file_dir):
#     files = os.listdir(tfrecord_file_dir)
#     tfrecord_files = list()
#     for f in files:
#         if f.endswith(".tfrecord"):
#             tfrecord_files.append(f)
#     
#     return tfrecord_files



def print_raw_record(raw_record):
    feature_description = {
      'func-signature': tf.io.FixedLenFeature([], tf.string, default_value=''),
      'func-return-type': tf.io.FixedLenFeature([], tf.string, default_value=''),
      'func-name': tf.io.FixedLenFeature([], tf.string, default_value=''),
      'func-file-name': tf.io.FixedLenFeature([], tf.string, default_value=''),
      'func-att-disas': tf.io.FixedLenFeature([], tf.string, default_value=''),
      'func-intel-disas': tf.io.FixedLenFeature([], tf.string, default_value=''),
      'ubuntu-package-name': tf.io.FixedLenFeature([], tf.string, default_value=''),
      'ubuntu-package-binary': tf.io.FixedLenFeature([], tf.string, default_value=''),
    }
    
    ex = tf.io.parse_single_example(raw_record, feature_description)
    
    print(f"func-signature\t---------->\n{ex['func-signature']}<")
    print(f"func-return-type\t---------->\n{ex['func-return-type']}<")
    print(f"func-name\t---------->\n{ex['func-name']}<")
    print(f"func-file-name\t---------->\n{ex['func-file-name']}<")
    print(f"func-att-disas\t---------->\n{ex['func-att-disas']}<")
    print(f"func-intel-disas\t---------->\n{ex['func-intel-disas']}<")
    print(f"ubuntu-package-name\t---------->\n{ex['ubuntu-package-name']}<")
    print(f"ubuntu-package-binary\t---------->\n{ex['ubuntu-package-binary']}<")
    

def _parse_function(example_proto):
    # Create a description of the features.
    feature_description = {
      'func-signature': tf.io.FixedLenFeature([], tf.string, default_value=''),
      'func-return-type': tf.io.FixedLenFeature([], tf.string, default_value=''),
      'func-name': tf.io.FixedLenFeature([], tf.string, default_value=''),
      'func-file-name': tf.io.FixedLenFeature([], tf.string, default_value=''),
      'func-att-disas': tf.io.FixedLenFeature([], tf.string, default_value=''),
      'func-intel-disas': tf.io.FixedLenFeature([], tf.string, default_value=''),
      'ubuntu-package-name': tf.io.FixedLenFeature([], tf.string, default_value=''),
      'ubuntu-package-binary': tf.io.FixedLenFeature([], tf.string, default_value=''),
    }
    
    # Parse the input `tf.train.Example` proto using the dictionary above.
    ex = tf.io.parse_single_example(example_proto, feature_description)
    
    return ex['func-signature'], ex['func-return-type'], ex['func-name'], ex['func-file-name'], ex['func-att-disas'], ex['func-intel-disas'], ex['ubuntu-package-name'], ex['ubuntu-package-binary']   
    

def main():
    AUTOTUNE = tf.data.experimental.AUTOTUNE
    
    config = parseArgs()
    
    check_config(config)
    
#     tfrecord_dataset_files = tf.data.Dataset.list_files(config['tfrecord_save_dir'] + '*.tfrecord')
#     tfrecord_dataset = tf.data.TFRecordDataset(tfrecord_dataset_files)
#     
#     print(f'tf.data.Dataset element_spec of train_dataset >{train_dataset.element_spec}<')
#     
#     tfrecord_dataset = tfrecord_dataset.map(_parse_function, num_parallel_calls=AUTOTUNE)
#     
#     
    
    
    
    
    #label_ds = tfrecord_dataset.map(lambda a,b,c,d,e,f,g,h: y, num_parallel_calls=AUTOTUNE)
    
     
    tfrecord_files = tfrecord_lib.get_all_tfrecord_filenames(config['tfrecord_save_dir'])
     
    for file in tfrecord_files:
        print(f"Printing 5 examples from >{config['tfrecord_save_dir'] + file}<")
        dataset = tf.data.TFRecordDataset(config['tfrecord_save_dir'] + file)
        for raw_record in dataset.take(3):
            print_raw_record(raw_record)
            
    
    
if __name__ == "__main__":
    main()