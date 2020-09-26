import pickle
import os
import tarfile

def get_all_pickle_filenames(tar_file_dir):
    files = os.listdir(tar_file_dir)
    tar_files = list()
    for f in files:
        if f.endswith(".pickle"):
            tar_files.append(f)
    
    return tar_files


def get_pickle_file_content(full_path_pickle_file):
    pickle_file = open(full_path_pickle_file,'rb')
    pickle_list = pickle.load(pickle_file, encoding='latin1')
    pickle_file.close()
    
    return pickle_list


def save_new_pickle(full_path_pickle_file, pickle_content):
    pickle_file = open(full_path_pickle_file,'wb+')
    pickle.dump(pickle_content, pickle_file)
    pickle_file.close()
    
    
tar_file_dir = "/tmp/embbuild"
all_files = get_all_pickle_filenames(tar_file_dir)

all_ds = list()

for file in all_files:
    content = get_pickle_file_content(tar_file_dir + '/' + file)
    all_ds.append(content)
    
save_new_pickle("/tmp/embstoredir/full_dataset_att_int_seq.pickle", all_ds)


