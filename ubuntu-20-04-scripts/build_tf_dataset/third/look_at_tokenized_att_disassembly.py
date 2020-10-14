import tarfile
import os
import sys
import pickle

def get_all_tar_filenames(tar_file_dir):
    tar_files = list()
    
    ### check if dir exists
    if not os.path.isdir(tar_file_dir):
        return tar_files
    
    files = os.listdir(tar_file_dir)
    
    for f in files:
        if f.endswith(".pickle"):
            tar_files.append(f)
    
    return tar_files


def get_pickle_file_content(full_path_pickle_file):
    pickle_file = open(full_path_pickle_file,'rb')
    pickle_list = pickle.load(pickle_file, encoding='latin1')
    pickle_file.close()
    
    return pickle_list


def print_one_pickle_list_item(pickle_file_content):
    item = next(iter(pickle_file_content))
    if item:
        print(f'caller-and-callee-disassembly: {item[0]}')
        print(f'return-type: {item[1]}')
    else:
        print('Error item[0]')
        
        
def main():
    files = get_all_tar_filenames('/tmp/save_dir')
    
    for file in files:
        cont = get_pickle_file_content('/tmp/save_dir/' + file)
        print_one_pickle_list_item(cont)
        break
        
        
if __name__ == "__main__":
    main()
