import pickle
import os
from datetime import datetime


def get_pickle_file_content(full_path_pickle_file):
    pickle_file = open(full_path_pickle_file,'rb')
    pickle_list = pickle.load(pickle_file, encoding='latin1')
    pickle_file.close()
    
    return pickle_list



def get_all_pickle_filenames(pickle_file_dir):
    files = os.listdir(pickle_file_dir)
    tar_files = list()
    for f in files:
        if f.endswith(".pickle"):
            tar_files.append(f)
    
    return tar_files


def save_vocab_as_pickle(full_path_vocab_file, vocab):
    pickle_file = open(full_path_vocab_file,'wb+')
    pickle_list = pickle.dump(vocab, pickle_file)
    pickle_file.close()
    
    
def build_vocab_dict_from_set(vocab_set):
    vocab_dict = dict()
    c = 1
    for w in vocab_set:
        vocab_dict[w] = c
        c += 1
        
    return vocab_dict



#### main
start=datetime.now()

bag_styled_file_dir = "/tmp/savetest"
full_path_vocab_file = "/tmp/vocab.pickle"

unique_vocab = set()


print(f'Read out all tokenized pickle files in >{bag_styled_file_dir}<')
all_files = get_all_pickle_filenames(bag_styled_file_dir)
if len(all_files) == 0:
    print(f'Error: No tokenized files in dir >{bag_styled_file_dir}<')
    exit()


for file in all_files:
    content = get_pickle_file_content(bag_styled_file_dir + '/' + file)
    for disas,ret_type in content:
        for disas_item in disas:
            #print(f'disas_item:{disas_item}')
            unique_vocab.add(disas_item)
            
    #break
    
stop = datetime.now()

vocab_dict = build_vocab_dict_from_set(unique_vocab)

print(f'Run took:{stop-start} Hour:Min:Sec')
print(f'We save Vocabulary in file >{full_path_vocab_file}<')

save_vocab_as_pickle(full_path_vocab_file, vocab_dict)

print(unique_vocab)
