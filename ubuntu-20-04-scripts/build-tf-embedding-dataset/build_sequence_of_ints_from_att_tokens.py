import pickle
import os
from datetime import datetime
import tarfile
import shutil


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


def save_embeddings_to_pickle(embedding_build_dir, embedding_build_file, embedding_store_dir, full_path_embeddings_save_dir, embeddings_list):
    global store_counter
    
    pickle_list = list()
    pick_tar_bz2 = embedding_build_dir + "/" + embedding_build_file + ".pickle.tar.bz2"
    pick_tar_bz2_shadow = embedding_build_dir + '/' + 'shadow-' + embedding_build_file + '.pickle.tar.bz2'
    pickle_raw = embedding_build_dir + '/' + embedding_build_file + '.pickle'
    
    ###check if .pickle.tar.bz2 file is in embedding_build_dir ?
    if os.path.isfile(pick_tar_bz2):
        print(f'pickle file {pick_tar_bz2} found')
        ### copy to 'shadow' file for later usage
        shutil.copyfile(pick_tar_bz2, pick_tar_bz2_shadow)
        ###untar (does not delete the .pickle.tar.bz2 file)
        tar = tarfile.open(pick_tar_bz2, "r:bz2")  
        tar.extractall(embedding_build_dir)
        tar.close()
        ### and open file 
        pickle_file = open(pickle_raw,'rb')
        ### read out
        pickle_list = pickle.load(pickle_file, encoding='latin1')
        pickle_file.close()
        os.remove(pickle_raw)
        ### and extend embeddings_list
        pickle_list.extend(embeddings_list)
        ### and save it as pickle 
        pickle_file = open(pickle_raw,'wb+')
        ### dump to pickle
        pickle.dump(pickle_list, pickle_file)
        pickle_file.close()
        ### tar it again
        os.remove(pick_tar_bz2)
        tar = tarfile.open(pick_tar_bz2, "w:bz2")
        aname = embedding_build_file + ".pickle"
        tar.add(pickle_raw, arcname=aname)
        tar.close()
        ###delete pickle file
        os.remove(pickle_raw)
        ### check size of .pickle.tar.bz2, need < 100mb
        file_stats = os.stat(pick_tar_bz2)
        print(f'File size of .pickle.tar.bz2 actually is >{file_stats.st_size}< bytes \
                =>{file_stats.st_size/1024}< kb or =>{file_stats.st_size/1024/1024}< Mb')
        
        ### 85mb
        github_filesize_in_mb = 85000000 / 1024 / 1024
        if (file_stats.st_size/1024/1024) < github_filesize_in_mb:   ###TODO ~<100mb
            print(f'File size is smaller than >{github_filesize_in_mb}< Mb its >{file_stats.st_size/1024/1024}< Mb, so we try to add more data')
            ### OK, let it be
        else:
            print(f'File size is bigger than >{github_filesize_in_mb}<, Mb \
                    its >{file_stats.st_size/1024/1024}< Mb\
                    so we copy the shadow-file to >{embedding_store_dir}<, and create new tmp file')
            
            ### dont save last embeddings, copy shadow-*.pickle.tar.bz2 to e.g. ubuntu-20-04-att-embeddings
            shutil.copyfile(pick_tar_bz2_shadow,
                            embedding_store_dir + '/' + 'att-embedding-ints-' + str(store_counter) + '.pickle.tar.bz2')
            ###increment counter which gets added to the stored file name
            store_counter += 1
            ### delete old pickle
            #os.remove(embedding_build_dir + '/' + embedding_build_file + '.pickle')
            os.remove(pick_tar_bz2_shadow)
            ### delete old .tar.bz2
            os.remove(pick_tar_bz2)
            ### then save last embeddings to new .pickle
            pickle_file = open(pickle_raw,'wb+')
            pickle_list = pickle.dump(embeddings_list, pickle_file)
            pickle_file.close()
            ### then tar it
            tar = tarfile.open(pick_tar_bz2, "w:bz2")
            aname = embedding_build_file + ".pickle"
            tar.add(pickle_raw, arcname=aname)
            tar.close()
            ### remove old pickle
            os.remove(pickle_raw)
            
    
    ### if no file is there, we build it, that is the first round
    else:
        print(f"No file >{embedding_build_dir + '/' + embedding_build_file + '.pickle.tar.bz2'}< there, we build it")
        pickle_file = open(pickle_raw,'wb+')
        pickle_list = pickle.dump(embeddings_list, pickle_file)
        pickle_file.close()
        ### now we tar it to see its real size
        #'w:bz2'
        tar = tarfile.open(pick_tar_bz2, "w:bz2")
        aname = embedding_build_file + ".pickle"
        tar.add(pickle_raw, arcname=aname)
        tar.close()
        os.remove(pickle_raw)
        
    
    #pickle_file = open(full_path_embeddings_file,'wb+')
    #pickle_list = pickle.dump(embeddings_list, pickle_file)
    #pickle_file.close()
    
   
def save_embs_to_pickle(embeddings_part, embedding_build_dir, embedding_build_file):
    global ds_tmp_bucket
    global store_counter
    
    pick_tar_bz2 = embedding_build_dir + "/" + embedding_build_file + "-" + store_counter + ".pickle.tar.bz2"
    pickle_raw = embedding_build_dir + '/' + embedding_build_file + '.pickle'
    
    ds_tmp_bucket.extend(embeddings_part)
    
    ### check size
    size_in_bytes = sys.getsizeof(ds_tmp_bucket)
    #if size_in_bytes > 85000000:
    if size_in_bytes > 10000:
        ### save as pickle
        pickle_file = open(pickle_raw,'wb+')
        pickle_list = pickle.dump(ds_tmp_bucket, pickle_file)
        pickle_file.close()
        ### delete for next round
        ds_tmp_bucket.clear()
        ### save as tar.bz2
        tar = tarfile.open(pick_tar_bz2, "w:bz2")
        aname = embedding_build_file + "-" + store_counter + ".pickle"
        tar.add(pickle_raw, arcname=aname)
        tar.close()
        ### delete pickle file
        os.remove(pickle_raw)
        store_counter += 1
        
    
    
#### main
start=datetime.now()
store_counter = 0

bag_styled_file_dir = "/tmp/savetest"
embedding_styled_file_dir = "/tmp/embtest"
embedding_build_dir = "/tmp/embbuild"
embedding_build_filename = "seq_to_int_and_labels"
full_path_vocab_file = "/tmp/vocab.pickle"
embedding_store_dir = "/tmp/embstoredir"

ds_tmp_bucket = list()

embeddings_list = list()
disas_embeddings = list()

biggest_nr_of_words_in_disas = 0
nr_of_disas = 0

### check if dirs are there
if not os.path.isdir(bag_styled_file_dir):
    print(f'Error: No dir with tokenized files >{bag_styled_file_dir}<. You run tokenize_att_disassembly_from_pickle.py before?')
    exit()
    
if not os.path.isdir(embedding_styled_file_dir):
    print(f'Error: No dir to save embeddings files to >{embedding_styled_file_dir}< . You need to create it.')
    exit()
    
if not os.path.isdir(embedding_build_dir):
    print(f'Error: No dir to build embeddings file in >{embedding_build_dir}< . You need to create it.')
    exit()
    
if not os.path.isdir(embedding_store_dir):
    print(f'Error: No dir to store the resulting embedding-ints+labels file in >{embedding_store_dir}<. You need to create it.')
    exit()
    
### get the vocab
vocab = get_vocabulary(full_path_vocab_file)
if len(vocab) == 0:
    print(f'Error: No vocabulary found. You run build_vocabulary_from_tokenized_pickle_files.py before ?.')
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
    ##save_embeddings_to_pickle(embedding_build_dir, embedding_build_filename, embedding_store_dir, embedding_styled_file_dir, embeddings_list)
    save_embs_to_pickle(embeddings_list, embedding_build_dir, embedding_build_filename)
    embeddings_list = []
    
    
    #break

stop=datetime.now()    
print(f'Run took: {stop-start} Hour:Min:Sec')
print(f'The biggest disassembly in our dataset got >{biggest_nr_of_words_in_disas}< words in it')
print(f'We got >{nr_of_disas}< disassemblies in our dataset')
     