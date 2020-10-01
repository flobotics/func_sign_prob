import pickle
import os
import tarfile


def get_pickle_file_content(full_path_pickle_file):
    pickle_file = open(full_path_pickle_file,'rb')
    pickle_list = pickle.load(pickle_file, encoding='latin1')
    pickle_file.close()
    
    return pickle_list


def main():
    tar_file_dir = "/tmp/embstoredir"
    file = "full_dataset_att_int_seq.pickle"
    
    content = get_pickle_file_content(tar_file_dir + '/' + file)
    
    
    biggest_length = 0
    len_list = list()
    c = 0
    for i in content:
        for dis,ret in i:
            len_list.append(len(dis))
            if len(dis) > biggest_length:
                if len(dis) > 50 and len(dis) < 30000:
                    print(f'New length of int_seq: {len(dis)}')
                    biggest_length = len(dis)
                
            ###debug
            if len(dis) == 8:
                print(f'len >{len(dis)} ret >{ret}<  disas >{dis}<')
                c += 1
                if c > 10:
                    break
                
    print(f'Biggest length of int_seq is: {biggest_length}')
    
    
    len_list_dict = dict()
    c = 0
    counter = 1
    for b in sorted(len_list):
        #print(f'One item in list: >{b}<')
        if b in len_list_dict:
            counter += 1
        else:
            counter = 1
        
        len_list_dict[b] = counter
        
        
        #c += 1
        #if c > 10:
         #break
        
    print(f'dict: >{len_list_dict}<')
    
    size_file = open(tar_file_dir + '/full_dataset_att_int_seq_biggest_int_seq_nr.txt','w+')
    size_file.write(str(biggest_length))
    size_file.close()


if __name__ == "__main__":
    main()
    
    



