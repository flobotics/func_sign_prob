import os
import sys
import getopt

def get_all_filenames_of_type(file_dir, type):
    filtered_files = list()
    
    if not type.startswith("."):
       type = '.' + type
  
    ### check if dir exists
    if not os.path.isdir(file_dir):
        print(f'Directory >{file_dir}< does not exist')
        return filtered_files
    
    files = os.listdir(file_dir)
    
    for f in files:
        if f.endswith(type):
            filtered_files.append(f)
    
    return filtered_files


def is_type_known(arg_one):
    return_type_list = ['bool', 'bool *', 'const bool',
                        'void', 'void *', 'void **', 'void (*)(void *)', 'void * const',
                        'char', 'char *', 'unsigned char *', 'char **', 'const char *', 'signed char',
                        'const char **', 'unsigned char', 'const char', 'const unsigned char *',
                        'unsigned char **', 'const char * const *', 'char32_t',
                        'signed char *', 'wchar_t *', 'const char16_t *', 'char ***',
                        'wchar_t', 'const char * const', 'const wchar_t *', 'char16_t *',
                        'const unsigned char **', 'char * const *', 'const signed char *',
                        'const char ***', 'volatile char *', 'signed char * const *',
                        'unsigned short', 'short', 'unsigned short *', 'short *',
                        'const unsigned short *', 'unsigned short **', 'short **',
                        'const unsigned short', 'const short',
                        'int', 'int *', 'unsigned int', 'const int *', 'const unsigned int *',
                        'int **', 'unsigned int **', 'volatile int *',
                        'unsigned int *', 'const unsigned int', 'const int', 'int ***',
                        '__int128', 'long int', '__int128 unsigned',
                        'long','unsigned long', 'unsigned long long', 'unsigned long *', 'long long',
                        'const unsigned long', 'unsigned long **', 'const long', 'const long *',
                        'long *', 'const unsigned long long *', 'const unsigned long *',
                        'long long *', 'unsigned long ***', 'unsigned long long *',
                        'double', 'const double *', 'double *', 'const double', 'long double',
                        'double **', 'double ***', 'const long double',
                        'float', 'const float *', 'float *', 'const float',
                        'float **', 'float ***', 'float ****',
                        'complex *', 'complex double', 'complex float']
    
    for a in return_type_list:
        if a == arg_one:
            #print(f'Found arg_one in return_type_list')
            return True
        
    return False
     
     
def check_trailing_slash_in_path(path):
    if not path.endswith('/'):
        path = path + '/'
        
    return path



def parseArgs():
    short_opts = 'hp:s:w:t:r:m:v:f:d:n:b:'
    long_opts = ['pickle-dir=', 'work-dir=', 'save-dir=', 'save-file-type=', 'base-dir=',
                 'return-type-dict-file', 'max-seq-length-file=', 'vocab-file=', 'tfrecord-save-dir=',
                 'balanced-dataset-dir=', 'minimum-nr-of-return-types=']
    config = dict()
    
    config['base_dir'] = ''
    config['pickle_dir'] = ''
    config['work_dir'] = ''
    config['save_dir'] = ''
    config['save_file_type'] = ''
    config['return_type_dict_file'] = ''
    config['max_seq_length_file'] = ''
    config['vocabulary_file'] = ''
    config['tfrecord_save_dir'] = ''
    config['balanced_dataset_dir'] = ''
    config['minimum_nr_of_return_types'] = '0'
 
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
        elif option_key in ('-d', '--balanced-dataset-dir'):
            config['balanced_dataset_dir'] = option_value[1:]
        elif option_key in ('-n', '--minimum-nr-of-return-types'):
            config['minimum_nr_of_return_types'] = option_value[1:]
        elif option_key in ('-b', '--base-dir'):
            config['base_dir'] = option_value[1:]
        elif option_key in ('-h'):
            print(f'<optional> -b or --base-dir The directory where all work is done')
            print(f'<optional> -p or --pickle-dir The directory with disassemblies,etc. Default: ubuntu-20-04-pickles')
            print(f'<optional> -w or --work-dir   The directory where we e.g. untar,etc. Default: /tmp/work_dir/')
            print(f'<optional> -s or --save-dir   The directory where we save dataset.  Default: /tmp/save_dir/')
            print(f'<optional> -d or --balanced-dataset-dir  The directory where we save the balanced dataset. Default: /tmp/save_dir/balanced/')
            print(f'<optional> -n or --minimum-nr-of-return-types  The minimum nr of return types. ')
            
    
    if not config['base_dir'] == '':
        config['base_dir'] = check_trailing_slash_in_path(config['base_dir'])
                
        if config['pickle_dir'] == '':
            config['pickle_dir'] = config['base_dir'] + 'pickles_for_dataset/'
            
        if config['work_dir'] == '':
            config['work_dir'] = config['base_dir'] + 'work_dir/'
            
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
                
        if config['balanced_dataset_dir'] == '':
            config['balanced_dataset_dir'] = config['base_dir'] + 'balanced_dataset/'
    
            
    return config
    
    