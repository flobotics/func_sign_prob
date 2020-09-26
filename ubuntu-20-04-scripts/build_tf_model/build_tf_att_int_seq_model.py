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


def get_ret_type_dict(pickle_list):
    ret_type_set = set()
    
    for content in pickle_list:
        for int_seq, ret_type in content:
            ret_type_set.add(ret_type)
            
            
    ### build ret_type dict
    ret_type_dict = {v:k for v,k in enumerate(ret_type_set, start=1)}
            
    return ret_type_dict
            

    
    

def add_one_item_to_tf_dataset(func_as_int_list, label_as_one_hot):
    
    if dataset_counter == 0:
        #dataset = tf.data.Dataset.from_tensors( ( func_as_int_list,label_as_int ))
        dataset = tf.data.Dataset.from_tensors( ( func_as_int_list,label_as_one_hot ))
        dataset_counter = 1
    else:
        #ds = tf.data.Dataset.from_tensors( ( func_as_int_list,label_as_int ))
        ds = tf.data.Dataset.from_tensors( ( func_as_int_list,label_as_one_hot ))
        #for elem,e in ds:
            #print(elem.shape)
        dataset = dataset.concatenate( ds )
        
        
    component = next(iter(dataset))
    print(component)
    
    return dataset
    
    
def split_tf_dataset():
    train_size = int(0.7 * num_elements_in_dataset)

    train_data = dataset.take(train_size)
    test_data = dataset.skip(train_size)
    
    #for e in train_data:
    #    print(e)
        
    #for e in test_data:
    #    print(e)
        
    num_elements_in_train_data = tf.data.experimental.cardinality(train_data).numpy()
    print(f'We got {num_elements_in_train_data} in train_data dataset')
    
    num_elements_in_test_data = tf.data.experimental.cardinality(test_data).numpy()
    print(f'We got {num_elements_in_test_data} in test_data dataset')
    
 
def shuffle_and_pad():
    train_batches = train_data.shuffle(10).padded_batch(5)
    test_batches = test_data.shuffle(10).padded_batch(5)
    
    
    train_batch, train_labels = next(iter(train_batches))
    print(train_batch.numpy())
    print(train_batch.shape)
    
    num_elements_in_train_batches = tf.data.experimental.cardinality(train_batches).numpy()
    print(num_elements_in_train_batches)
    
    num_elements_in_test_batches = tf.data.experimental.cardinality(test_batches).numpy()
    print(num_elements_in_test_batches)





def main():
    path_to_int_seq_pickle = "../../ubuntu-20-04-datasets/full_dataset_att_int_seq.pickle"
    
    ###read out full ds pickle
    pickle_file_content = get_pickle_file_content(path_to_int_seq_pickle)
    
    ### get return type dict
    ret_type_dict = get_ret_type_dict(path_to_int_seq_pickle)
    
    ### for content
    for content in pickle_file_content:
        ### for every item in list
        for func_as_int_list, label in content: 
            ### build tf-one-hot
            label_as_int = ret_type_dict[label]
            label_as_one_hot = tf.one_hot(label_as_int, len(ret_type_dict))
            
            ### build tf dataset
            full_tf_ds = add_one_item_to_tf_dataset(func_as_int_list, label_as_one_hot)

    #####################
    ### Now we got our tf dataset which we can easily push into model.compile
    
    ### Next we create our model
    #####################

    embedding_dim=64
    
    ### get number of "words" in our vocabulay of int_seq (NOT ret-types)
    ### open vocab file
    vocab_file = open("../../ubuntu-20-04-datasets/full_dataset_att_int_seq_vocabulary.pickle")
    vocab = pickle.load(vocab_file, encoding='latin1')
    vocab_file.close()
    print(f'Number of items in vocabulary: {len(vocab)}')
    
    
    
    split_tf_dataset
    
    
    shuffle_and_pad
    
    
    
    
    
    
    
    
    
    
    
    
    
    
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
    
    
    model = keras.Sequential([
        layers.Embedding(len(vocab)+1, embedding_dim, mask_zero=True),
        layers.GlobalAveragePooling1D(),
        layers.Dense(32, activation='relu'),
        layers.Dense(len(vocab_ret_types))
    ])
        
    model.summary()    
    
    #####################
    ### specify optimizer,loss,etc
    #####################
    
    #model.compile(optimizer='adam',
    #              loss=tf.keras.losses.BinaryCrossentropy(from_logits=True),
    #              metrics=['accuracy'])
        
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
        monitor='val_accuracy',
        mode='max',
        save_best_only=True)
    
    
    print(f'Storing tf checkpoint files to: {checkpoint_filepath}')
    
    
    logdir = "/tmp/logs/scalars/" + date_str
    tensorboard_callback = keras.callbacks.TensorBoard(log_dir=logdir, histogram_freq=1)
    #, callbacks=[tensorboard_callback]
    print(f'Storing tensorboard files to: {logdir}')
    
    
    
    history = model.fit(
        train_batches,
        epochs=30,
        validation_data=test_batches, validation_steps=20, callbacks=[tensorboard_callback, model_checkpoint_callback]
    )
        

    

if __name__ == "__main__":
    main()

   
    
    
    
    