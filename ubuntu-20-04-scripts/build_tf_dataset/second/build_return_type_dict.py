import pickle
import numpy as np
import os
from datetime import datetime


def get_pickle_file_content(full_path_pickle_file):
    pickle_file = open(full_path_pickle_file,'rb')
    pickle_list = pickle.load(pickle_file, encoding='latin1')
    pickle_file.close()
    
    return pickle_list


def get_ret_type_dict(pickle_list):
    ret_type_set = set()
    
    for content in pickle_list:
        for int_seq, ret_type in content:
            #print(f'int_seq: {int_seq}  ret_type:{ret_type}')
            ret_type_set.add(ret_type)
                
            
    ### build ret_type dict
    ret_type_dict = {k:v for v,k in enumerate(ret_type_set, start=1)}
            
    return ret_type_dict


def main():
    path_to_int_seq_pickle = "../../../ubuntu-20-04-datasets/full_dataset_att_int_seq.pickle"
    #path_to_return_type_dict_file = "../../ubuntu-20-04-datasets/full_dataset_att_int_seq_ret_type_dict.pickle"
    path_to_return_type_dict_file = "/tmp/full_dataset_att_int_seq_ret_type_dict.pickle"
    
    ###read out full ds pickle
    if not os.path.isfile(path_to_int_seq_pickle):
        print(f'No file: {path_to_int_seq_pickle} there ?')
        exit()
        
    pickle_file_content = get_pickle_file_content(path_to_int_seq_pickle)
    
    ### get return type dict
    ret_type_dict = get_ret_type_dict(pickle_file_content)
    print(f'ret-type-dict: {ret_type_dict}')
    
    ### save return type dict to file
    ret_file = open(path_to_return_type_dict_file, 'wb+')
    pickle_list = pickle.dump(ret_type_dict, ret_file)
    ret_file.close()
    
    print(f'Saved {path_to_return_type_dict_file} file.')
    
    
if __name__ == "__main__":
    main()

    
    

