import tarfile
import os
import sys
import pickle
#import tensorflow as tf
from datetime import datetime
from multiprocessing import Pool
import getopt
from itertools import repeat

nr_of_cpus = 4

def get_all_tar_filenames(tar_file_dir):
    tar_files = list()
    
    ### check if dir exists
    if not os.path.isdir(tar_file_dir):
        return tar_files
    
    files = os.listdir(tar_file_dir)
    
    for f in files:
        if f.endswith(".tar.bz2"):
            tar_files.append(f)
    
    return tar_files

def untar_one_pickle_file(full_path_tar_file, work_dir):
    tar = tarfile.open(full_path_tar_file, "r:bz2")  
    tar.extractall(work_dir)
    tar.close()
    
    
def get_pickle_file_content(full_path_pickle_file):
    pickle_file = open(full_path_pickle_file,'rb')
    pickle_list = pickle.load(pickle_file, encoding='latin1')
    pickle_file.close()
    
    return pickle_list


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
    short_opts = 'hp:s:w:'
    long_opts = ['pickle-dir=', 'work-dir=', 'save-dir=']
    config = dict()
    
    config['pickle_dir'] = '../../../ubuntu-20-04-pickles'
    config['work_dir'] = '/tmp/work_dir/'
    config['save_dir'] = '/tmp/save_dir'
 
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
        elif option_key in ('-h'):
            print(f'<optional> -p or --pickle-dir The directory with disassemblies,etc. Default: ubuntu-20-04-pickles')
            print(f'<optional> -w or --work-dir   The directory where we e.g. untar,etc. Default: /tmp/work_dir/')
            print(f'<optional> -s or --save-dir   The directory where we save dataset.  Default: /tmp/save_dir')
            
            
    return config
    

def print_5_pickle_files(pickle_files, config):
    if len(pickle_files) == 0:
        print(f'Pickle dir is empty')
        exit()
        
    print(f'Five files from dir >{config["pickle_dir"]}<')
    c = 0
    for file in pickle_files:
        print(f'file >{file}<')
        c += 1
        if c > 5:
            break
        
        
def get_string_before_function_name(function_signature):
    return_type = ''
    
    ### find ( which marks the function-names end
    fn_end_idx = function_signature.index('(')
    
    ### now step one char left, till * , &, or ' ' is found
    c = -1
    for char in function_signature[fn_end_idx::-1]:
        if char == '*' or char == ' ' or char == '&':
            #print(f'return-type: {function_signature[:fn_end_idx-c]}')
            return_type = function_signature[:fn_end_idx-c].strip()
            break
        c += 1
                  
    return return_type
 
 
def get_function_return_type(string_before_func_name, gdb_ptype):
    ### get raw return type, e.g. "void" or "struct" instead of "struct timeval" from gdb-ptype
    raw_gdb_return_type = get_raw_return_type_from_gdb_ptype(gdb_ptype)
    
    if raw_gdb_return_type == 'unknown':
        print(f'string_before_func_name: {string_before_func_name}')
    
    return raw_gdb_return_type


def get_raw_return_type_from_gdb_ptype(gdb_ptype):
    
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
    
    
    if "type =" in gdb_ptype:
        ### pattern based
        new_gdb_ptype = gdb_ptype.replace('type =', '')
        raw_gdb_ptype = new_gdb_ptype.strip()
        
        ### delete some strange return-types
        if raw_gdb_ptype == 'unsigned char (*)[16]':
            return 'delete'
        elif raw_gdb_ptype == 'unsigned char (*)[12]':
            return 'delete'
        elif raw_gdb_ptype == 'int (*)(int (*)(void *, int, int), void *, int)':
            return 'delete'
        elif raw_gdb_ptype == 'PTR TO -> ( character )':
            return 'delete'
        elif raw_gdb_ptype == 'logical*4':
            return 'delete'
        elif raw_gdb_ptype == 'PTR TO -> ( Type _object )':
            return 'delete'
        elif raw_gdb_ptype == 'integer(kind=8)':
            return 'delete'
        elif 'GLcontext' in raw_gdb_ptype:
            return 'delete'
        elif raw_gdb_ptype == 'long long __attribute__ ((vector_size(2)))':
            return 'delete'
        elif 'Yosys' in raw_gdb_ptype:
            return 'delete'
        
        ### check if we directly find a valid return type
        for return_type in return_type_list:
            if raw_gdb_ptype == return_type:
                return return_type
            elif raw_gdb_ptype == '_Bool':
                return 'bool'
            elif raw_gdb_ptype == '_Bool *':
                return 'bool *'
            elif raw_gdb_ptype == 'ulong':
                return 'unsigned long'
            elif raw_gdb_ptype == 'uint':
                return 'unsigned int'
            elif raw_gdb_ptype == 'ubyte':
                return 'unsigned char'
            elif raw_gdb_ptype == 'ubyte *':
                return 'unsigned char *'
            elif raw_gdb_ptype == 'integer':
                return 'delete'   ### dont know if its signed,or unsigned or ????
            elif raw_gdb_ptype == 'ushort':
                return "unsigned short"

            
        ### check if { is there
        idx = 0
        if '{' in raw_gdb_ptype:
            idx = raw_gdb_ptype.index('{')
            
        if idx > 0:
            #print(f'Found braket-sign')
            front_str = raw_gdb_ptype[:idx]
            front_str = front_str.strip()
            #print(f'front_str: {front_str}')
            if 'class' in front_str:
                ### check if ptype got {} signs for class
                if '}' in front_str:
                    ### check if * or ** is after } available
                    idx = front_str.rfind('}')
                    last_front_str = front_str[idx:]
                
                    star_count = last_front_str.count('*')
                    if star_count == 0:
                        return 'class'
                    elif star_count == 1:
                        return 'class *'
                    elif star_count == 2:
                        return 'class **'
                    elif 'std::' in front_str:
                        return 'delete'
                    else:
                        print(f'Error star_count class >{star_count}< front_str >{front_str}<')
                        return 'unknown'
                    
            elif 'struct' in front_str:
                star_count = front_str.count('*')
                if star_count == 0:
                    return 'struct'
                elif 'std::' in front_str:
                    return 'delete'
                elif 'QPair' in front_str:
                    return 'delete'
                elif 'ts::Rv' in front_str: ##strange stuff from a package,dont know,delete
                    return 'delete'
                elif 'fMPI' in front_str: #strange
                    return 'delete'
                else:
                    print(f'Error star_count struct >{star_count}< front_str >{front_str}<')
                    return 'unknown'
            elif 'enum' in front_str:
                star_count = front_str.count('*')
                if star_count == 0:
                    return 'enum'
                else:
                    print(f'Error star_count enum >{star_count}< front_str >{front_str}<')
                    return 'unknown'
            elif 'union' in front_str:
                #print(f'front_str-union: {front_str}')
                star_count = front_str.count('*')
                if star_count == 0:
                    return 'union'
                else:
                    print(f'Error star_count union >{star_count}< front_str >{front_str}<')
                    return 'unknown'
                
            else:
                print(f'---Nothing found')
                print(f'front_str: {front_str}')
                return 'unknown'
            
        elif (raw_gdb_ptype.count('(') == 2) and (raw_gdb_ptype.count(')') == 2):
            #print(f'Found func-pointer as return-type, delete till now')
            return 'delete'
        elif 'substitution' in raw_gdb_ptype:
            #print(f'Found substituion-string, dont know, delete it')
            return 'delete'
        else:
            #print(f'------no gdb ptype-match for: >{raw_gdb_ptype}<')
            return 'unknown'
    else:
        print(f'No gdb ptype found')
        return 'unknown'
    
    
 
def proc_build(pickle_file, work_dir, save_dir):
    untar_one_pickle_file(pickle_file, work_dir)
        
    pickle_file_content = get_pickle_file_content(work_dir + os.path.basename(pickle_file).replace('.tar.bz2', ''))
    
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
            for elem in pickle_file_content:
                if elem[7] == bin and elem[2] == func:
                    att_dis = elem[4]
                    for item in att_dis:
                        if 'call' in item and not '@plt' in item and not 'std::' in item:
                            #print(f'caller >{item}<')
                            ## get callee name
                            callee_name = ''
                            item_split = item.split()
                            callee_name = item_split[len(item_split)-1]
                            callee_name = callee_name.replace('<', '')
                            callee_name = callee_name.replace('>', '')
                                
                                    
                                    
                            #print(f'callee_name >{callee_name}<')
                            
                            for elem2 in pickle_file_content:
                                if elem2[7] == bin and elem2[2] == callee_name:
                                    #print(f'caller >{item}<')
                                    #print(f'callee_name >{callee_name}<')
                                    #print(f'dis-of-callee >{elem2[4]}<')
                                    
                                    string_before_func_name = get_string_before_function_name(elem2[0])
                                    #print(f'string_before_func_name: >{string_before_func_name}<')
                                    return_type = get_function_return_type(string_before_func_name, elem2[1])
                                     
                                    #print(f'return_type: >{return_type}<')
                                    if return_type == 'unknown':
                                        #print('unknown found')
                                        #breaker = True
                                        #break
                                        pass
                                    elif return_type == 'delete':
                                        #print('delete found')
                                        ### no return type found, so delete this item
                                        pass
                                    else:
                                        #unique_return_types.add(return_type)
                                        ### remove addr and stuff
                                        #cleaned_att_disassembly = clean_att_disassembly(item[4])
                                        #bag_of_words_style_assembly = build_bag_of_words_style_assembly(cleaned_att_disassembly)
                                        #dis_str = ' '.join(bag_of_words_style_assembly)
                                    
                                        ##save caller-disassembly, callee-disassembly, callee-func-sign, callee-gdb-ptype
                                        
#                                         print(f'att_dis >{att_dis}<')
#                                         print(f'elem2[4] >{elem2[4]}<')
#                                         print(f'return_type >{return_type}<')
                                        #dis_combined = list()
                                        #dis_combined.clear()
                                        #dis_combined = att_dis
                                        #for elem3 in elem2[4]:
                                        #    dis_combined.append(elem3)
                                            
                                        dis1_str = ' '.join(att_dis)
                                        dis2_str = ' '.join(elem2[4])
                                        dis_str = dis1_str + dis2_str
                                            
                                        #print(f'dis_str >{dis_str}<')
                                    
                                        dataset_list.append((dis_str, return_type))
                                        counter += 1
                                        break
                  
           
    if dataset_list:       
        ret_file = open(save_dir + '/' + os.path.basename(pickle_file).replace('.tar.bz2', ''), 'wb+')
        pickle_list = pickle.dump(dataset_list, ret_file)
        ret_file.close()
                  
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
    
     
    ### get all pickle files
    pickle_files = get_all_tar_filenames(config['pickle_dir'])
    
    ### print 5 files, check and debug
    print_5_pickle_files(pickle_files, config)
    
    
    ### build
    p = Pool(nr_of_cpus)
    
    
    pickle_files = [config["pickle_dir"] + "/" + f for f in pickle_files]
    star_list = zip(pickle_files, repeat(config['work_dir']), repeat(config['save_dir']))
    all_ret_types = p.starmap(proc_build, star_list)
    p.close()
    p.join()
    
    
    for counter in all_ret_types:
        if counter > 0:
            print(f'disassemblies saved >{counter}<')
            break
    
    
if __name__ == "__main__":
    main()

    