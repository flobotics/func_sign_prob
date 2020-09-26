import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import pickle
import numpy as np
import os
from datetime import datetime



def build_tf_dataset():
    label_as_int = vocab_ret_types[label]
    label_as_one_hot = tf.one_hot(label_as_int, len(vocab_ret_types))
    
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



embedding_dim=64

print(len(vocab))

#model = keras.Sequential([
#  layers.Embedding(len(vocab), embedding_dim),
#  layers.GlobalAveragePooling1D(),
#  layers.Dense(32, activation='relu'),
#  layers.Dense(len(vocab_ret_types))
#])

model = keras.Sequential([
    layers.Embedding(len(vocab)+1, embedding_dim, mask_zero=True),
    layers.GlobalAveragePooling1D(),
    layers.Dense(32, activation='relu'),
    layers.Dense(len(vocab_ret_types))
])
    
    



#model.compile(optimizer='adam',
#              loss=tf.keras.losses.BinaryCrossentropy(from_logits=True),
#              metrics=['accuracy'])
    
model.compile(optimizer='adam',
              loss=tf.keras.losses.CategoricalCrossentropy(from_logits=True),
              metrics=['accuracy'])


date_str = datetime.now().strftime("%Y%m%d-%H%M%S")

#checkpoint_filepath = 'logs/' + date_str
checkpoint_filepath = 'logs/checkpoint'
model_checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
    filepath=checkpoint_filepath,
    save_weights_only=True,
    monitor='val_accuracy',
    mode='max',
    save_best_only=True)


print(checkpoint_filepath)


logdir = "logs/scalars/" + date_str
tensorboard_callback = keras.callbacks.TensorBoard(log_dir=logdir, histogram_freq=1)
#, callbacks=[tensorboard_callback]

history = model.fit(
    train_batches,
    epochs=30,
    validation_data=test_batches, validation_steps=20, callbacks=[tensorboard_callback, model_checkpoint_callback]
)


    
    
    
    
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


model.summary()





   
    
    
    
    