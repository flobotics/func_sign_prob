import tarfile
import os
import sys
import pickle
#import tensorflow as tf
from datetime import datetime

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
            print(f'Found func-pointer as return-type, delete till now')
            return 'delete'
        elif 'substitution' in raw_gdb_ptype:
            print(f'Found substituion-string, dont know, delete it')
            return 'delete'
        else:
            print(f'------no gdb ptype-match for: >{raw_gdb_ptype}<')
            return 'unknown'
    else:
        print(f'No gdb ptype found')
        return 'unknown'
    
    
    
def get_function_return_type(string_before_func_name, gdb_ptype):
    ### get raw return type, e.g. "void" or "struct" instead of "struct timeval" from gdb-ptype
    raw_gdb_return_type = get_raw_return_type_from_gdb_ptype(gdb_ptype)
    
    if raw_gdb_return_type == 'unknown':
        print(f'string_before_func_name: {string_before_func_name}')
    
    return raw_gdb_return_type



def store_as_tfrecord():
    tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))
    
    
    
def clean_att_disassembly(att_disassembly):
    cleaned = list()
    
    for dis_line in att_disassembly:
        #if 'ako' in dis_line:
        #    print(f'dis_line:{dis_line}')
        dis_line_parts = dis_line.split('\t')
        if len(dis_line_parts) != 2:
            print(f'len:{len(dis_line_parts)}')
        #if 'ako' in dis_line:
        #   print(f'dis_line_parts:{dis_line_parts}')
            
        dis_line_front = dis_line_parts[1]
            
        
        if '#' in dis_line_front:
            ### get index of #
            idx = dis_line_front.index('#')
            if '<' in dis_line_front:
                idx2 = dis_line_front.index('<')
                if idx2 < idx:
                    idx = idx2
            
            ### copy part infront of #
            clean_dis = dis_line_front[:idx-1]
            ### strip whitelines from copying
            clean_dis = clean_dis.strip()
            
            if 'ako' in clean_dis:
                print(f"Error here---1---------{clean_dis}")
            cleaned.append(clean_dis)
        elif '<' in dis_line_front:
            #print(f'dis_line:{dis_line_front}')
            ### get index of <
            idx = dis_line_front.index('<')
            if '#' in dis_line_front:
                idx2 = dis_line_front.index('#')
                if idx2 < idx:
                    idx = idx2
            #print(f'idx:{idx}')
            ### copy part infront of <
            clean_dis = dis_line_front[:idx-1]
            #print(f'clean_dis: {clean_dis}')
            ### strip whitelines from copying
            clean_dis = clean_dis.strip()
            
            if 'ako' in clean_dis:
                print("Error here---2---------")
            cleaned.append(clean_dis)
        else:
            if 'ako' in dis_line_front:
                print("Error herer---3------")
            cleaned.append(dis_line_front)
            
        
    for i in cleaned:
        if 'ako' in i:
            print(f'Error')
        
    return cleaned



def build_bag_of_words_style_assembly(cleaned_att_disassembly):
    bag_style_att_disassembly = list()
    
    for line in cleaned_att_disassembly:
        line = line.replace('(', ' ( ')
        line = line.replace(')', ' ) ')
        line = line.replace('%', ' % ')
        line = line.replace(',', ' , ')
        line = line.replace('$', ' $ ')
        line = line.replace('*', ' * ')
        for item in line.split():
            ### replace every addr e.g. 0x764 with 0x, to have a better vocab
            if '0x' in item:
                bag_style_att_disassembly.append('0x')
            else:
                bag_style_att_disassembly.append(item)
        
    return bag_style_att_disassembly

    
    
    
def get_all_bag_styled_pickle_files(save_dir):
    files = os.listdir(save_dir)
    bag_files = list()
    for f in files:
        if f.endswith(".pickle"):
            bag_files.append(f)
    
    return bag_files


def create_dirs_for_working(full_path_untar_dir, full_path_save_dir):
    if not os.path.isdir(full_path_untar_dir):
        print(f'Dir >{full_path_untar_dir} does not exist, so we create it')
        os.mkdir(full_path_untar_dir)
        if not os.path.isdir(full_path_untar_dir):
            print(f'Error: could not create directory to untar >{full_path_untar_dir}<')
            return
        else:
            print(f'Dir to untar >{full_path_untar_dir} created')
            
    if not os.path.isdir(full_path_save_dir):
        print(f'Dir >{full_path_save_dir} does not exist, so we create it')
        os.mkdir(full_path_save_dir)
        if not os.path.isdir(full_path_save_dir):
            print(f'Error: could not create directory to save >{full_path_save_dir}<')
            return
        else:
            print(f'Dir to save >{full_path_save_dir} created')
    


def save_new_pickle(full_path_pickle_file, pickle_content):
    pickle_file = open(full_path_pickle_file,'wb+')
    pickle.dump(pickle_content, pickle_file)
    pickle_file.close()





#### main

start=datetime.now()

#tar_file_dir = "/home/ubu/jupyter-notebooks/build-tf-ds-from-pickle"
tar_file_dir = "/tmp/testtars"   ##dir where .pickle.tar.bz2 files are
#tar_file_dir = os.getcwd() + '/../ubuntu-20-04-pickles'
print(f'Directory with pickle.tar.bz2 files is >{tar_file_dir}<')

work_dir = "/tmp/test"           ##dir where untar files to
save_dir = "/tmp/savetest"       ##dir where we save bag-style pickle files to

unique_return_types = set()
disassembly_att_and_ret_types_list = list()

###check/create dirs to untar/save
create_dirs_for_working(work_dir, save_dir)

###get a list with all pickle.tar.bz2 files
all_tar_files = get_all_tar_filenames(tar_file_dir)
if len(all_tar_files) == 0:
    print(f'Error: No pickle.tar.bz2 files in >{tar_file_dir}<')
    exit()

### if we run it again, check what files we already have done yet
all_bag_styled_files = get_all_bag_styled_pickle_files(save_dir)
if len(all_bag_styled_files) == 0:
    print(f'Info: No tokenized pickle files found, now we tokenize.')

breaker = False

##test
##all_tar_files = ['kakoune.pickle.tar.bz2']
##all_bag_styled_files = []

### loop through all pickle.tar.bz2 files and untar them
for one_tar_file in all_tar_files:
    cont = False
    
    ### check if we have already done this package in a previous run
    for bag_file in all_bag_styled_files:
        #print(f'bag-file:{bag_file}')
        if bag_file.replace('att-tokenized-', '') == one_tar_file.replace(".tar.bz2", ""):
            #print('Already tokenized this file')
            cont = True
            break
    
    if(cont):
        continue
    
    untar_one_pickle_file(tar_file_dir + "/" + one_tar_file, work_dir)

    ### read out pickle file
    pickle_file_content = get_pickle_file_content(work_dir + "/" + one_tar_file.replace(".tar.bz2", ""))

    ##for debug
    #print_one_pickle_list_item(pickle_file_content)

    disassembly_att_and_ret_types_list.clear()
    
    ### loop through all pickle items and 
    for item in pickle_file_content:
        if item:
            ### if the item[0] exists
            ### item[4] => att
            ### item[5] => intel
            if item[0].strip() and item[1].strip() and (len(item[4]) > 1) and (len(item[5]) > 1):
                
                string_before_func_name = get_string_before_function_name(item[0])
                #print(f'string_before_func_name: >{string_before_func_name}<')
                return_type = get_function_return_type(string_before_func_name, item[1])
                
                #print(f'return_type: >{return_type}<')
                if return_type == 'unknown':
                    print('unknown found')
                    breaker = True
                    break
                elif return_type == 'delete':
                    print('delete found')
                    ### no return type found, so delete this item
                    #pass
                else:
                    unique_return_types.add(return_type)
                    ### remove addr and stuff
                    cleaned_att_disassembly = clean_att_disassembly(item[4])
                    bag_of_words_style_assembly = build_bag_of_words_style_assembly(cleaned_att_disassembly)
                    
                    ### append it to the last list, which gets stored to tfrecord
                    disassembly_att_and_ret_types_list.append((bag_of_words_style_assembly, return_type))
        else:
            print("-----No item in pickle file")
       
    if breaker:
        break
        
    ### save to new pickle file, to save_dir
    print(f'Save file: att-tokenized-{one_tar_file.replace(".tar.bz2", "")}')
    save_new_pickle(save_dir + '/' + 'att-tokenized-' + one_tar_file.replace(".tar.bz2", ""), 
                    disassembly_att_and_ret_types_list)
     
    
    
    

stop=datetime.now()
print(f'Run took:{stop-start} Hours:Min:Sec')

### debug: print 3 list items
#c=0
#for d, r in disassembly_att_and_ret_types_list:
#    print(f'bag-style-disas:{d} \n return-type:{r}')
#    print('-----------')
#    c += 1
#    if c > 3:
#        break
    ### can a function end with callq ???????
    ### remove numbers 0x and $0x, etc.
        
        


print(f'unique_return_types: {unique_return_types}')
print(f'len disassembly_att_and_ret_types_list: {len(disassembly_att_and_ret_types_list)}')
sz = sys.getsizeof(disassembly_att_and_ret_types_list)
print(f'size of: {sz}')




### if less than 100Mb, store it in tfrecord file (github doesnt allow > 100Mb files)
#store_as_tfrecord(disassembly_att_and_ret_types_list)