import getopt
import sys
import os
import tensorflow as tf


def parseArgs():
    short_opts = 'hw:u:p:t:c:b:v:'
    long_opts = ['work-dir=', 'git-user=', 'git-pwd=', 'tfrecord-save-dir=', 'config-dir=', 'ubuntu-pwd=', 'verbose=']
    
    config = dict()
    
    config['work_dir'] = ''
    config['tfrecord_save_dir'] = ''
    config['config_dir'] = ''
    config['git_user'] = ''
    config['git_pwd'] = ''
    config['ubuntu_pwd'] = ''
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
        elif option_key in ('-u', '--git-user'):
            config['git_user'] = option_value[1:]
        elif option_key in ('-p', '--git-pwd'):
            config['git_pwd'] = option_value[1:]
        elif option_key in ('-t', '--tfrecord-save-dir'):
            config['tfrecord_save_dir'] = option_value[1:]
        elif option_key in ('-c', '--config-dir'):
            config['config_dir'] = option_value[1:]
        elif option_key in ('-b', '--ubuntu-pwd'):
            config['ubuntu_pwd'] = option_value[1:]
        elif option_key in ('-v', '--verbose'):
            if option_value[1:] == 'False':
                config['verbose'] = False
            else:
                config['verbose'] = True
        elif option_key in ('-h'):
            print(f'<optional> -w or --work-dir The directory where all work is done. Default: /tmp/work')
            print(f'<optional> -u or --git-user  The username for github repo')
            print(f'<optional> -p or --git-pwd  The password for github repo')
            print(f'<optional> -c or --config-dir  The directory to save config files to run this script twice or more, without \
                    doing the same packages again')
            print(f'<optional> -b or --ubuntu-pwd The ubuntu user password to install packages with apt')
     
     
    if config['work_dir'] == '':
        config['work_dir'] = '/tmp/work/'
    if config['tfrecord_save_dir'] == '':
        config['tfrecord_save_dir'] = config['work_dir'] + 'tfrecord_files/'
    if config['config_dir'] == '':
        config['config_dir'] = config['work_dir'] + 'config-files/'
    if config['git_user'] == '':
        config['git_user'] = ''
    if config['git_pwd'] == '':
        config['git_pwd'] = ''
    if config['ubuntu_pwd'] == '':
        config['ubuntu_pwd'] = ''
    if config['verbose'] == '':
        config['verbose'] = True
    
    ###configs without argument, but perhaps depend on configs-with-arguments
    config['filtered_out_config_file'] = config['config_dir'] + 'package-filtered-out.txt'
    config['package_all_config_file'] = config['config_dir'] + 'package-all.txt'
    config['package_work_config_file'] = config['config_dir'] + 'package-work.txt'
    config['package_dont_work_config_file'] = config['config_dir'] + 'package-dont-work.txt'
    config['package_binaries_config_file'] = config['config_dir'] + 'package-binaries.txt'
    
           
    return config   


def get_all_tfrecord_filenames(tfrecord_file_dir):
    files = os.listdir(tfrecord_file_dir)
    tfrecord_files = list()
    for f in files:
        if f.endswith(".tfrecord"):
            tfrecord_files.append(f)
    
    return tfrecord_files


def check_config(config):
    if not os.path.isdir(config['tfrecord_save_dir']):
        print(f"Directory with tfrecord files does not exist >{config['tfrecord_save_dir']}<, check -h for help")
        exit()

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
    
    
    #return ex['caller_callee'], ex['label']

def main():
    config = parseArgs()
    
    check_config(config)
    
    tfrecord_files = get_all_tfrecord_filenames(config['tfrecord_save_dir'])
    
    for file in tfrecord_files:
        print(f"Printing 5 examples from >{config['tfrecord_save_dir'] + file}<")
        dataset = tf.data.TFRecordDataset(config['tfrecord_save_dir'] + file)
        for raw_record in dataset.take(3):
            example = tf.train.Example()
            example.ParseFromString(raw_record.numpy())
            print(f'Example >{example}<')
            
            print_raw_record(raw_record)
        exit()
            
    
    
    

if __name__ == "__main__":
    main() 
    
    
    