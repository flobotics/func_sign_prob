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


def save_vocab_size(full_path_vocab_file, vocab_size):
    file = open(full_path_vocab_file,'w+')
    file.write(str(vocab_size))
    file.close()
    
def save_sequence_length(full_path_seq_file, biggest):
    file = open(full_path_seq_file,'w+')
    file.write(str(biggest))
    file.close()
    
    
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
full_path_vocab_file = "/tmp/vocab_size.txt"
full_path_seq_file = "/tmp/sequence_length.txt"

unique_vocab = set()


print(f'Read out all tokenized pickle files in >{bag_styled_file_dir}<')
all_files = get_all_pickle_filenames(bag_styled_file_dir)
if len(all_files) == 0:
    print(f'Error: No tokenized files in dir >{bag_styled_file_dir}<')
    exit()

counter = 0
biggest = 0

for file in all_files:
    content = get_pickle_file_content(bag_styled_file_dir + '/' + file)
    for disas,ret_type in content:
        counter = 0
        for disas_item in disas.split():
            counter += 1
            #print(f'disas_item:{disas_item}')
            unique_vocab.add(disas_item)
        
        if counter > biggest:
            biggest = counter
    #break
    
stop = datetime.now()

#vocab_dict = build_vocab_dict_from_set(unique_vocab)

print(f'Run took:{stop-start} Hour:Min:Sec')
print(f'We save Vocabulary in file >{full_path_vocab_file}<')
print(f'Vocab size is >{len(unique_vocab)}<')
print(f'Biggest sequence length is >{biggest}<')

save_vocab_size(full_path_vocab_file, len(unique_vocab))
save_sequence_length(full_path_seq_file, biggest)

print(unique_vocab)
