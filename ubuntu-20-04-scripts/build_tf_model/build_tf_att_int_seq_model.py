import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import pickle
import numpy as np
import os
from datetime import datetime

def get_pickle_file_content(full_path_pickle_file):
    pickle_file = open(full_path_pickle_file,'rb')
    pickle_list = pickle.load(pickle_file, encoding='latin1')
    pickle_file.close()
    
    return pickle_list



def get_ret_type_dict(path_to_return_type_dict_file):
    ret_type_list = get_pickle_file_content(path_to_return_type_dict_file)
               
    return ret_type_list
            


dataset_counter = 0

def main():
    global dataset_counter
    
    verbose = True
    
    ### full dataset
    ### ([3,45,66,68], 'void')
    path_to_int_seq_pickle = "../../ubuntu-20-04-datasets/full_dataset_att_int_seq.pickle"
    ### ret-type-dict
    ### { "void": 1, "char": 2,......
    path_to_return_type_dict_file = "../../ubuntu-20-04-datasets/full_dataset_att_int_seq_ret_type_dict.pickle"
    ### vocab
    ### ['mov','rbp'....
    path_to_vocab_file = "../../ubuntu-20-04-datasets/full_dataset_att_int_seq_vocabulary.pickle"
    ### number of words of the biggest int seq
    path_to_biggest_int_seq = "../../ubuntu-20-04-datasets/full_dataset_att_int_seq_biggest_int_seq_nr.txt"
    
    ### check if files exist
    if not os.path.isfile(path_to_int_seq_pickle):
        print(f'No file with full dataset, named >{path_to_int_seq_pickle}< there ?')
        exit()
    else:
        if verbose:
            print(f'The full dataset we read from file >{path_to_int_seq_pickle}<')
        pass
        
    if not os.path.isfile(path_to_return_type_dict_file):
        print(f'No file with return-type-dict, named >{path_to_return_type_dict_file}< there ?')
        exit()
    else:
        if verbose:
            print(f'Return type-dict we read from file >{path_to_return_type_dict_file}<')
        pass
        
    if not os.path.isfile(path_to_vocab_file):
        print(f'No file with vocabulary, named  >{path_to_vocab_file}< there ?')
        exit()
    else:
        if verbose:
            print(f'Vocabulary we read from >{path_to_vocab_file}<')
        pass
        
    if not os.path.isfile(path_to_biggest_int_seq):
        print(f'No file with size of biggest int-sequence, named >{path_to_biggest_int_seq}< there ?')
        exit()
    else:
        if verbose:
            print(f'The size of the biggest int-sequence we read from file >{path_to_biggest_int_seq}<')
        pass
    
    
    ### read int-seq,label from pickle file
    pickle_file_content = get_pickle_file_content(path_to_int_seq_pickle)
    
    ### get return type dict
    ret_type_dict = get_ret_type_dict(path_to_return_type_dict_file)
    print(f'\nret-type-dict: {ret_type_dict}\n')
    
    counter = 0
    len_of_all_contents = 0
    start = datetime.now()
    
    ### for content
    for content in pickle_file_content:
        ### for every item in list
        #print(f'len-content: {len(content)}')
        len_of_all_contents += len(content)
        ##for TESTING
        if len_of_all_contents > 10000:
            break
        for func_as_int_list, label in content: 
            ### build tf-one-hot
            label_as_int = ret_type_dict[label]
            label_as_one_hot = tf.one_hot(label_as_int, len(ret_type_dict))
            
            ### removing all int-seqs which are bigger then 30000 and smaller than 50
            if len(func_as_int_list) > 50 and len(func_as_int_list) < 30000:
                ### build tf dataset
                if dataset_counter == 0:
                    dataset_counter = 1
                    print(f'label: {label}')
                    print(f'label-as-int: {label_as_int}')
                    dataset = tf.data.Dataset.from_tensors( ( func_as_int_list,label_as_one_hot ))
                else:
                    #full_tf_ds = add_one_item_to_tf_dataset(func_as_int_list, label_as_one_hot, dataset)
                    ds = tf.data.Dataset.from_tensors( ( func_as_int_list,label_as_one_hot ))
                    dataset = dataset.concatenate( ds )
    
                ### print to show the user that something is happening, this loop took a while
                print(f'Adding >{counter}< int_seqs to tf-ds of >{len_of_all_contents}<', end='\r')
                counter += 1

    stop = datetime.now()
    print(f'Building dataset took: >{stop-start}< Hours:Min:Sec')
    
    num_elements_in_dataset = tf.data.experimental.cardinality(dataset).numpy()
    print(f'We got {num_elements_in_dataset} in  dataset')
    
    ### debug
    dshape = dataset.element_spec
    print(f'Shape of dataset >{dshape}<')
    
    ### print element from dataset for debug
    print_elem = False
    if print_elem:
        c =0
        for elem in dataset:
            print(f'element >{c}< >{elem}<')
            c += 1
            if c > 3:
                break
    
    
    print(f'Len of all-contents from pickle: {len_of_all_contents}')
    #ds1 = next(iter(dataset))
    #print(f'One dataset item:{ds1}')
    #exit()
    #####################
    ### Now we got our tf dataset which we can easily push into model.compile
    
    ### Next we create our model
    #####################

    embedding_dim=8
    
    ### get number of "words" in our vocabulay of int_seq (NOT ret-types)
    ### open vocab file
    vocab_file = open(path_to_vocab_file, 'rb')
    vocab = pickle.load(vocab_file, encoding='latin1')
    vocab_file.close()
    print(f'Number of items in vocabulary: >{len(vocab)}<')
    
    ### split ds in train, test  
    #train_ds, test_ds = split_tf_dataset(dataset, len_of_all_contents)
    print(f'We got >{num_elements_in_dataset}< in dataset, we split now')
    train_size = int(0.7 * num_elements_in_dataset)
    print(f'train_size: >{train_size}<  and test_size >{num_elements_in_dataset - train_size}<')

    train_data = dataset.take(train_size)
    test_data = dataset.skip(train_size)
    
    ### print element of train dataset for debug
    if print_elem:
        c =0
        for elem in train_data:
            print(f'train_data element >{c}< >{elem}<')
            c += 1
            if c > 3:
                break
    
    num_elements_in_train_data = tf.data.experimental.cardinality(train_data).numpy()
    print(f'We got {num_elements_in_train_data} in  train_data after split')
    num_elements_in_test_data = tf.data.experimental.cardinality(test_data).numpy()
    print(f'We got {num_elements_in_test_data} in  test_data after split')
    
    ### get lenght of biggest int_seq
    len_big_int_seq_file = open(path_to_biggest_int_seq, 'r')
    len_big_int_seq = len_big_int_seq_file.readline()
    len_big_int_seq_file.close()
    print(f'len biggest int-seq, we pad int-seq to: {len_big_int_seq}')
    
    ### shuffle and pad
    #train_ds_batch = train_data.shuffle(1000).padded_batch(int(len_big_int_seq))
    #test_ds_batch = test_data.shuffle(1000).padded_batch(int(len_big_int_seq))
    train_ds_batch = train_data.shuffle(1000).padded_batch(100)
    test_ds_batch = test_data.shuffle(1000).padded_batch(100)
    
    num_elements_in_train_ds_batch = tf.data.experimental.cardinality(train_ds_batch).numpy()
    print(f'We got {num_elements_in_train_ds_batch} in  train_ds_batch after padding')
    num_elements_in_test_ds_batch = tf.data.experimental.cardinality(test_ds_batch).numpy()
    print(f'We got {num_elements_in_test_ds_batch} in  test_ds_batch after padding')
    
    ### print element of train dataset for debug
    if print_elem:
        c =0
        for elem in train_ds_batch:
            print(f'train_ds_batch element >{c}< >{elem}<')
            c += 1
            if c > 3:
                break
    
    ##train_ds_batch_int_seq, train_ds_batch_label = next(iter(train_ds_batch))
    #print(f'One train_ds_batch_int_seq example: >{train_ds_batch_int_seq.numpy()}<')
    ##print(f'Shape of train_ds_batch_int_seq example: >{train_ds_batch_int_seq.shape}<')
    #print(f'Label of train_ds_batch_label example: >{train_ds_batch_label.numpy()}<')
    ##print(f'Shape of train_ds_batch_label example: >{train_ds_batch_label.shape}<')
    
    

    #print(f'stop here')
    #exit()
    
    #####################
    ### build tf model
    #####################
    
    #model = keras.Sequential([
    #  layers.Embedding(len(vocab), embedding_dim),
    #  layers.GlobalAveragePooling1D(),
    #  layers.Dense(32, activation='relu'),
    #  layers.Dense(len(vocab_ret_types))
    #])
    
        #model = tf.keras.Sequential([
    #    tf.keras.layers.Embedding(len(vocab), embedding_dim),
    #    tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(embedding_dim)),
    #    tf.keras.layers.Dense(32, activation='relu'),
    #    tf.keras.layers.Dense(len(vocab_ret_types))
    #])
    
    #batch_size --- 10
    #model = tf.keras.Sequential([
    #    tf.keras.layers.Embedding(len(vocab), embedding_dim,
    #                              batch_input_shape=[1, None]),
    #    tf.keras.layers.GRU(1024,
    #                        return_sequences=True,
    #                        stateful=True,
    #                        recurrent_initializer='glorot_uniform'),
    #    tf.keras.layers.Dense(len(vocab_ret_types))
    #])
    
    ### adding +1, because of the padded-zero, which we mask out
    print(f'len(vocab)+1: >{len(vocab)+1}<  embedding_dim: >{embedding_dim}<')
    
    #tf.profiler.experimental.stop()
    
    model = keras.Sequential([
        layers.Embedding(len(vocab)+1, embedding_dim, mask_zero=True),
        layers.GlobalAveragePooling1D(),
        layers.Dense(32, activation='relu'),
        layers.Dense(len(ret_type_dict), activation='softmax')
    ])
        
    model.summary()    
    
    #####################
    ### specify optimizer,loss,etc
    #####################
    
    #model.compile(optimizer='adam',
    #              loss=tf.keras.losses.BinaryCrossentropy(from_logits=True),
    #              metrics=['accuracy'])
        
    ## sparseCategorialCrossentropy
        
    model.compile(optimizer='adam',
                  loss=tf.keras.losses.CategoricalCrossentropy(from_logits=True),
                  metrics=['accuracy'])
    
    
    date_str = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    #####################
    ###specify callbacks to store checkpoints for tensorboard
    #####################
    
    #checkpoint_filepath = 'logs/' + date_str
    checkpoint_filepath = '/tmp/logs/checkpoint'
    model_checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
        filepath=checkpoint_filepath,
        save_weights_only=True,
        monitor='accuracy',
        mode='max',
        save_best_only=True)
    
    
    print(f'Storing tf checkpoint files to: {checkpoint_filepath}')
    
    
    logdir = "/tmp/logs/scalars/" + date_str + "/"
    tensorboard_callback = keras.callbacks.TensorBoard(log_dir=logdir, histogram_freq=1)
    #tensorboard_callback = keras.callbacks.TensorBoard(log_dir=logdir)
    print(f'Storing tensorboard files to: {logdir}')
    
    
    
    history = model.fit(
        train_ds_batch,
        epochs=10,
        validation_data=test_ds_batch, 
        validation_steps=20, 
        callbacks=[tensorboard_callback, model_checkpoint_callback]
    )
#     history = model.fit(
#         train_ds_batch,
#         epochs=30,
#         validation_data=test_ds_batch, validation_steps=20, callbacks=[model_checkpoint_callback]
#     )  

    

if __name__ == "__main__":
    main()

   
    
    
    
    
