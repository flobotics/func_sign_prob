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