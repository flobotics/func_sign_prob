import pickle
import os

def get_pickle_file_content(full_path_pickle_file):
    pickle_list = list()
    
    if not os.path.isfile(full_path_pickle_file):
        print(f'Pickle file >{full_path_pickle_file}< does not exist')
        return pickle_list
    
    pickle_file = open(full_path_pickle_file,'rb')
    pickle_list = pickle.load(pickle_file, encoding='latin1')
    pickle_file.close()
    
    return pickle_list



def save_to_pickle_file(data, file):
    ret_file = open(file, 'wb+')
    pickle.dump(data, ret_file)
    ret_file.close()
    
    
def print_X_pickle_filenames(pickle_files, number):
    if len(pickle_files) == 0:
        print(f'Pickle dir is empty')
        return
        
    print(f'Print >{number}< pickle files')
    c = 0
    for file in pickle_files:
        print(f'file >{file}<')
        c += 1
        if c > (number-1):
            break
        
        
        
        