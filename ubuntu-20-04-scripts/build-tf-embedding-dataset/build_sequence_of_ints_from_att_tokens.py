import pickle
import os
from datetime import datetime
import tarfile


def get_all_pickle_filenames(pickle_file_dir):
    files = os.listdir(pickle_file_dir)
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


def get_vocabulary(full_path_vocab_file):
    pickle_list = list()
    
    if not os.path.isfile(full_path_vocab_file):
        print(f'Error: No vocabulary file here >{full_path_vocab_file}<')
        return pickle_list
    
    pickle_file = open(full_path_vocab_file,'rb')
    pickle_list = pickle.load(pickle_file, encoding='latin1')
    pickle_file.close()
    
    return pickle_list


def save_embeddings_to_pickle(embedding_build_dir, embedding_build_file, full_path_embeddings_save_dir, embeddings_list):
    ###check if file is in embedding_build_dir ?
    if os.path.isfile(embedding_build_dir + '/' + embedding_build_file + '.pickle.tar.bz2'):
        print(f'file found')
        ###untar 
        tar = tarfile.open(embedding_build_dir + '/' + embedding_build_file + '.pickle.tar.bz2', "r:bz2")  
        tar.extractall(embedding_build_dir)
        tar.close()
        ### and open file 
        pickle_file = open(embedding_build_dir + '/' + embedding_build_file + '.pickle','rb')
        ### read out
        pickle_list = pickle.load(pickle_file, encoding='latin1')
        pickle_file.close()
        os.remove(embedding_build_dir + '/' + embedding_build_file + '.pickle')
        ### and extend embeddings_list
        pickle_list.extend(embeddings_list)
        ### and save it as pickle 
        pickle_file = open(embedding_build_dir + '/' + embedding_build_file + '.pickle','wb+')
        ### dump to pickle
        pickle.dump(pickle_list, pickle_file)
        pickle_file.close()
        ### tar it again
        tar = tarfile.open(embedding_build_dir + '/' + embedding_build_file + '.pickle.tar.bz2', "w:bz2")
        aname = embedding_build_file + ".pickle"
        tar.add(embedding_build_dir + '/' + embedding_build_file + '.pickle', arcname=aname)
        tar.close()
        ###delete pickle file
        os.remove(embedding_build_dir + '/' + embedding_build_file + '.pickle')
        print(f'type: {type(pickle_list)}')
    
    ### if no file is there, we build it
    else:
        print(f"no file >{embedding_build_dir + '/' + embedding_build_file + '.pickle.tar.bz2'}< there, we build it")
        pickle_file = open(embedding_build_dir + '/' + embedding_build_file + '.pickle','wb+')
        pickle_list = pickle.dump(embeddings_list, pickle_file)
        pickle_file.close()
        ### now we tar it to see its real size
        #'w:bz2'
        tar = tarfile.open(embedding_build_dir + '/' + embedding_build_file + '.pickle.tar.bz2', "w:bz2")
        aname = embedding_build_file + ".pickle"
        tar.add(embedding_build_dir + '/' + embedding_build_file + '.pickle', arcname=aname)
        tar.close()
        os.remove(embedding_build_dir + '/' + embedding_build_file + '.pickle')
        
    
    #pickle_file = open(full_path_embeddings_file,'wb+')
    #pickle_list = pickle.dump(embeddings_list, pickle_file)
    #pickle_file.close()
    
    
    
#### main
start=datetime.now()

bag_styled_file_dir = "/tmp/savetest"
embedding_styled_file_dir = "/tmp/embtest"
embedding_build_dir = "/tmp/embbuild"
embedding_build_filename = "embbuildfile"
full_path_vocab_file = "/tmp/vocab.pickle"


embeddings_list = list()
disas_embeddings = list()

biggest_nr_of_words_in_disas = 0
nr_of_disas = 0

### check if dirs are there
if not os.path.isdir(bag_styled_file_dir):
    print(f'Error: No dir with tokenized files >{bag_styled_file_dir}<')
    exit()
    
if not os.path.isdir(embedding_styled_file_dir):
    print(f'Error: No dir to save embeddings files to >{embedding_styled_file_dir}< . You need to create it.')
    exit()
    
if not os.path.isdir(embedding_build_dir):
    print(f'Error: No dir to build embeddings file in >{embedding_build_dir}< . You need to create it.')
    exit()
    
### get the vocab
vocab = get_vocabulary(full_path_vocab_file)
if len(vocab) == 0:
    print(f'Error: No vocabulary found. Create it first.')
    exit()

### get list with all files, we want to replace word with embedding-int
all_files = get_all_pickle_filenames(bag_styled_file_dir)
if len(all_files) == 0:
    print(f'Error: No tokenized files found in >{bag_styled_file_dir}<')
    exit()

for file in all_files:
    content = get_pickle_file_content(bag_styled_file_dir + '/' + file)
    
    ### clean for next loop
    embeddings_list = []
    disas_embeddings = []
    
    ### loop through all items, and build new list with embedding-ints
    for disas,ret_type in content:
        nr_of_disas += 1
        for disas_item in disas:
            vi = vocab[disas_item]
            disas_embeddings.append(vi)
            #print(f'disas_item:{disas_item} embedding-int:{vi}')
              
        if biggest_nr_of_words_in_disas < len(disas_embeddings):
            biggest_nr_of_words_in_disas = len(disas_embeddings)
        embeddings_list.append((disas_embeddings, ret_type))
        #break 
        
        disas_embeddings = []     
    
    ### save every embedding to its own pickle file
    save_embeddings_to_pickle(embedding_build_dir, embedding_build_filename, embedding_styled_file_dir, embeddings_list)
    embeddings_list = []
    
    
    #break

stop=datetime.now()    
print(f'Run took: {stop-start} Hour:Min:Sec')
print(f'The biggest disassembly in our dataset got >{biggest_nr_of_words_in_disas}< words in it')
print(f'We got >{nr_of_disas}< disassemblies in our dataset')
     