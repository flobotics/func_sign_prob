import tarfile
import os
import sys
import pickle

def get_pickle_file_content(full_path_pickle_file):
    pickle_file = open(full_path_pickle_file,'rb')
    pickle_list = pickle.load(pickle_file, encoding='latin1')
    pickle_file.close()
    
    return pickle_list


def print_pickle_list_items(pickle_file_content):
    for key in pickle_file_content:
        print(key)
        
        
def main():
    file = '/tmp/vocab.pickle'
    
    cont = get_pickle_file_content(file)
    print_pickle_list_items(cont)
    
        
        
if __name__ == "__main__":
    main()
