import os

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
    