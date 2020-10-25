import pickle
import os
from datetime import datetime
import getopt


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


def save_vocab(full_path_vocabfile, unique_vocab):
    pickle_file = open(full_path_vocabfile,'wb+')
    pickle.dump(unique_vocab, pickle_file)
    pickle_file.close()
    
 
def parseArgs():
    short_opts = 'hp:'
    long_opts = ['pickle-dir=']
    config = dict()
    
    config['pickle_dir'] = '/tmp/save_dir'
 
    try:
        args, rest = getopt.getopt(sys.argv[1:], short_opts, long_opts)
    except getopt.GetoptError as msg:
        print(msg)
        print(f'Call with argument -h to see help')
        exit()
    
    for option_key, option_value in args:
        if option_key in ('-p', '--pickle-dir'):
            print(f'found p')
            config['pickle_dir'] = option_value[1:]
        elif option_key in ('-h'):
            print(f'<optional> -p or --pickle-dir The directory with disassemblies,etc. Default: /tmp/save_dir')
            
            
    return config
    

def main():
    start=datetime.now()
    
    config = parseArgs()
    
    bag_styled_file_dir = config['pickle_dir']
    full_path_vocab_file = "/tmp/vocab_size.txt"
    full_path_seq_file = "/tmp/sequence_length.txt"
    full_path_vocabfile = "/tmp/vocab.pickle"
    
    unique_vocab = set()
    
    
    print(f'Read out all tokenized pickle files in >{bag_styled_file_dir}<')
    all_files = get_all_pickle_filenames(bag_styled_file_dir)
    if len(all_files) == 0:
        print(f'Error: No tokenized files in dir >{bag_styled_file_dir}<')
        exit()
    
    counter = 0
    biggest = 0
    longest_disas = 30000
    shortest_disas = 50
    len_all_files = len(all_files)
    len_all_files_counter = 1
    
    for file in all_files:
        content = get_pickle_file_content(bag_styled_file_dir + '/' + file)
        print(f'Building vocab from file >{file}<  nr >{len_all_files_counter}/{len_all_files}<', end='\r')
        len_all_files_counter += 1
        for disas,ret_type in content:
            #print(f'len disas >{len(disas)}<')
            ### we filter out some
            if (len(disas) <= longest_disas) and ( len(disas) >= shortest_disas):
                for disas_item in disas.split():
                    unique_vocab.add(disas_item)
                
                if len(disas) > biggest:
                    biggest = len(disas)
        #break
        
    stop = datetime.now()
    
    #vocab_dict = build_vocab_dict_from_set(unique_vocab)
    
    print(f'Run took:{stop-start} Hour:Min:Sec')
    print(f'We save Vocabulary in file >{full_path_vocab_file}<')
    print(f'Vocab size is >{len(unique_vocab)}<')
    print(f'Biggest sequence length is >{biggest}<')
    
    save_vocab(full_path_vocabfile, unique_vocab)
    
    save_vocab_size(full_path_vocab_file, len(unique_vocab))
    save_sequence_length(full_path_seq_file, biggest)
    
    #print(unique_vocab)
    


if __name__ == "__main__":
    main()

