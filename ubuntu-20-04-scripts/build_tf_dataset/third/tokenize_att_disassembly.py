import tarfile
import os
import sys
import pickle
#import tensorflow as tf
from datetime import datetime
from multiprocessing import Pool
import getopt
from itertools import repeat

nr_of_cpus = 2

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
                                    ##save caller-disassembly, callee-disassembly, callee-func-sign, callee-gdb-ptype
                                    dataset_list.append((att_dis ,elem2[4], elem2[0], elem2[1]))
                                    counter += 1
                                    break
                  
           
    if dataset_list:       
        ret_file = open(save_dir + '/' + os.path.basename(pickle_file).replace('.tar.bz2', ''), 'wb+')
        pickle_list = pickle.dump(dataset_list, ret_file)
        ret_file.close()
                  
    return counter
    
  
def main():
    config = parseArgs()
    
    print(f'config >{config}<')
    
     
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

    