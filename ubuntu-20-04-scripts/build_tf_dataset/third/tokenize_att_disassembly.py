import tarfile
import os
import sys
import pickle
#import tensorflow as tf
from datetime import datetime
from multiprocessing import Pool
import getopt

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
    short_opts = 'hp:'
    long_opts = ['pickle-dir=']
    config = dict()
    
    config['pickle_dir'] = '../../../ubuntu-20-04-pickles'
    config['work_dir'] = '/tmp/work_dir'
 
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
        elif option_key in ('-h'):
            print(f'<optional> -p or --pickle-dir The directory with disassemblies,etc. Default: ubuntu-20-04-pickles')
            print(f'<optional> -w or --work-dir   The directory where we e.g. untar,etc. Default: /tmp/work_dir')
            
            
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
        
 
def proc_build(full_path_tar_file, work_dir):
    untar_one_pickle_file(full_path_tar_file, work_dir)
        
    pickle_list = get_pickle_file_content(full_path_pickle_file)
  
def main():
    config = parseArgs()
    
    print(f'config >{config}<')
     
    ### get all pickle files
    pickle_files = get_all_tar_filenames(config['pickle_dir'])
    
    ### print 5 files, check and debug
    print_5_pickle_files(pickle_files, config)
    
    
    ### build
    p = Pool(nr_of_cpus)
            
    all_ret_types = p.starmap(proc_build, (pickle_files , config['work_dir']))
    p.close()
    p.join()
    
    for ret in all_ret_types:
        print(f'ret >{ret}<')
    
    
if __name__ == "__main__":
    main()

    