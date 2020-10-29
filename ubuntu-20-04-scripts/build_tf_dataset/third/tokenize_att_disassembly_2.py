import tarfile
import os
import sys
import pickle
#import tensorflow as tf
from datetime import datetime
from multiprocessing import Pool
import getopt
from itertools import repeat
sys.path.append('../../lib/')
import return_type_lib

nr_of_cpus = 16

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
    
    if "type =" in gdb_ptype:
        ### pattern based
        new_gdb_ptype = gdb_ptype.replace('type =', '')
        raw_gdb_ptype = new_gdb_ptype.strip()
        
        #################
        ret = return_type_lib.delete_strange_return_types(raw_gdb_ptype)
        if ret == 'delete':
            return ret

        ret = return_type_lib.pattern_based_find_return_type(raw_gdb_ptype)
        if not (ret == 'process_further'):
            return ret
        ##################
            
        ### check if { is there
        idx = 0
        if '{' in raw_gdb_ptype:
            ret = return_type_lib.find_class_return_type(raw_gdb_ptype)
            if not (ret == 'process_further'):
                return ret
            
            ret = return_type_lib.find_struct_return_type(raw_gdb_ptype)
            if not (ret == 'process_further'):
                return ret  
             
            ret = return_type_lib.find_enum_return_type(raw_gdb_ptype)
            if not (ret == 'process_further'):
                return ret
            
            ret = return_type_lib.find_union_return_type(raw_gdb_ptype)
            if not (ret == 'process_further'):
                return ret   
            
            print(f'---No return type found with braket-sign in it')
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
 
 
def dis_split(dis):
    dis_list = list()
        
    for line in dis.split('\t'):
        #print(f'One line-----------')
        #print(f'line: >{line}<')
        
        line = line.replace('(', ' ( ')
        line = line.replace(')', ' ) ')
        line = line.replace('%', ' % ')
        line = line.replace(',', ' , ')
        line = line.replace('$', ' $ ')
        line = line.replace('*', ' * ')
        line = line.replace('<', ' < ')
        line = line.replace('>', ' > ')
        line = line.replace('+', ' + ')
        line = line.replace('@', ' @ ')
        line = line.replace(':', ' : ')
        #print(f'line after giving space: >{line}<')
        
        new_line = ''
        for item in line.split():
            #print(f'One item of one line >{item}<')
            ## check if we got a hex nr with chars
            new_item = ''
            if (len(item) >= 2) and item[0] == '0' and item[1] == 'x':
                #print(f'Found Hex >{item}<, split it into single numbers and chars')
                for c in item:
                    ### replace '0' with 'null'  ,for textVectorize where '0' is masked-value
                    if c == '0':
                        c = 'null'
                    new_item = new_item + c + ' '
                    
                #print(f'Split hex to >{new_item}<')
            else:
                #print(f'No hex found, check for nr')
                length = len(item)
                #print(f'length >{length}<')
                if length > 1:
                    for c in item:
                        if str.isnumeric(c):
                            ### replace '0' with 'null'  ,for textVectorize where '0' is masked-value
                            if c == '0':
                                c = 'null'
                            new_item = new_item + c + ' '
                        else:
                            new_item = new_item + c
                    
#                         for i in range(length):
#                             if isnumeric(item[i]):
#                                 c = item[i]
#                                 new_item = new_item + c + ' '
#                                 #print(f'Found number >{item[i]}< new_item >{new_item}<')
#                             else:
#                                 new_item = new_item + c
#                                 #print(f'No number >{item[i]}<  new_item >{new_item}<')
                else:
                    new_item = item
        
            ### add ' ' ,so that in next line it got a space between the strings for new_line
            if not new_item.endswith(' '):
                new_item = new_item + ' '
            #print(f'old item >{item}< new_item: >{new_item}<')        
            
            
            new_line = new_line + new_item
         
        #print(f'new_line >{new_line}<')   
               

        #exit()         
        dis_list.append(new_line)
    
    
    #print(f'Full disas: >{dis_list}<')
    dis_str = ' '.join(dis_list)   
    
    return dis_str
    
 
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
                                        
                                        dis1_str = dis_split(dis1_str)
                                        dis2_str = dis_split(dis2_str)
                                        
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

    