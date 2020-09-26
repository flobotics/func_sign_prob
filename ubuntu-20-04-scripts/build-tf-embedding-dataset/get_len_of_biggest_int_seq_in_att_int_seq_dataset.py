import pickle
import os
import tarfile


def get_pickle_file_content(full_path_pickle_file):
    pickle_file = open(full_path_pickle_file,'rb')
    pickle_list = pickle.load(pickle_file, encoding='latin1')
    pickle_file.close()
    
    return pickle_list


tar_file_dir = "/tmp/embbuild"
file = "full_dataset_att_int_seq.pickle"

content = get_pickle_file_content(tar_file_dir + '/' + file)


biggest_length = 0

for i in content:
    for dis,ret in i:
        if len(dis) > biggest_length:
            print(f'New length of int_seq: {len(dis)}')
            biggest_length = len(dis)
            
print(f'Biggest length of int_seq is: {biggest_length}')

size_file = open(tar_file_dir + '/full_dataset_att_int_seq_biggest_int_seq_nr.txt','w+')
size_file.write(biggest_length)
size_file.close()





