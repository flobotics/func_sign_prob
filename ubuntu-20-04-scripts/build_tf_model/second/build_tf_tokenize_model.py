import tensorflow as tf
from tensorflow.keras import Model, Sequential
from tensorflow.keras.layers import Activation, Dense, Embedding, GlobalAveragePooling1D
from tensorflow.keras.layers.experimental.preprocessing import TextVectorization
import pickle
import os  
from tensorflow.python.ops.ragged.ragged_string_ops import ngrams
from datetime import datetime
from multiprocessing import Pool
import numpy as np

nr_of_cpus = 2



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

def get_vocab_size(full_path_vocab_file):
    file = open(full_path_vocab_file,'r')
    ret = file.read()
    file.close()
    return ret


def get_sequence_length(full_path_seq_file):
    file = open(full_path_seq_file,'r')
    ret = file.read()
    file.close()
    return ret

full_path_vocab_file = "/tmp/vocab_size.txt"
full_path_seq_file = "/tmp/sequence_length.txt"
# Vocabulary size and number of words in a sequence.
vocab_size = get_vocab_size(full_path_vocab_file)
sequence_length = get_sequence_length(full_path_seq_file)


def custom_standardization(input_data):
    return tf.strings.lower(input_data)


### add 2   UNK and empty
vectorize_layer = TextVectorization(standardize=None,
                                        max_tokens=int(vocab_size)+2,
                                        output_mode='int',
                                        output_sequence_length=int(sequence_length))

def vectorize_text(text, label):
    text = tf.expand_dims(text, -1)
    return vectorize_layer(text), label
  
  
def save_trained_word_embeddings(date_str, model):
    trained_dir = "/tmp/logs/" + date_str + "/trained_word_embeddings"
    vecs_filename = "/tmp/logs/" + date_str + "/trained_word_embeddings/vecs.tsv"
    meta_filename = "/tmp/logs/" + date_str + "/trained_word_embeddings/meta.tsv"
    
    vocab = vectorize_layer.get_vocabulary()
    print(f'10 vocab words >{vocab[:10]}<')
    
    # Get weights matrix of layer named 'embedding'
    weights = model.get_layer('embedding').get_weights()[0]
    print(f'Shape of the weigths >{weights.shape}<') 
    
    os.mkdir(trained_dir)
    out_v = open(vecs_filename, 'w+')
    out_m = open(meta_filename, 'w+')
    
    for num, word in enumerate(vocab):
      if num == 0: continue # skip padding token from vocab
      vec = weights[num]
      out_m.write(word + "\n")
      out_v.write('\t'.join([str(x) for x in vec]) + "\n")
    out_v.close()
    out_m.close()


def proc_build_list_with_label_ints(file):
    global ret_type_dict

    pickle_file_dir = "/tmp/savetest"
    
    ds_counter = 0
    
    ret_list = list()
            
    cont = get_pickle_file_content(pickle_file_dir + '/' + file)
    for dis,ret in cont:
        #print(f'Tokenized file {pickle_file_counter}/{nr_of_pickle_files} and >{dis_counter}< assemblies', end='\r')
        #dis_counter += 1
        
        ret_type_int = ret_type_dict[ret] - 1
        
        ret_list.append( (dis, ret_type_int) )

    return ret_list





path_to_return_type_dict_file = "/tmp/full_dataset_att_int_seq_ret_type_dict.pickle"
ret_type_dict = get_pickle_file_content(path_to_return_type_dict_file)


def main():
    global vectorize_layer
    global vocab_size
    global sequence_length
    global full_path_vocab_file
    global full_path_seq_file
    global nr_of_cpus
    global ret_type_dict
    
    date_str = datetime.now().strftime("%Y%m%d-%H%M%S")

    checkpoint_filepath = '/tmp/logs/' + date_str + '/checkpoint'
    tensorboard_logdir = "/tmp/logs/" + date_str
    
    pickle_file_dir = "/tmp/savetest"
    
    
    raw_dataset_path = "/tmp/logs/" + date_str + "/tf_dataset_dir"
    
    
    print(f'tensorflow version >{tf.__version__}<, build with 2.3.1')
    print(f'Vocabulary size read from file >{full_path_vocab_file}< is >{vocab_size}<')
    print(f'Sequence length read from file >{full_path_seq_file}< is >{sequence_length}<')
    
    

    ### get return type dict
    ret_type_dict = get_pickle_file_content(path_to_return_type_dict_file)
    
    got_dataset = False
    ### check if we already got a dataset from tokenized files
    print(f'Check if we already got a dataset from tokenized files')
    if os.path.isdir(raw_dataset_path):
        print(f'Found raw_dataset file, will use it')
        raw_dataset = tf.data.experimental.load(raw_dataset_path, (tf.TensorSpec(shape=(), dtype=tf.string, name=None), tf.TensorSpec(shape=(), dtype=tf.int32, name=None)) )
        got_dataset = True
    else:
        print('No dataset from tokenized files found')
    
    
    if not got_dataset:
        ### build ds from tokenized files, then get texts
        print(f'Building tf dataset from tokenized files')
        ds_counter = 0
        pickle_files = get_all_pickle_filenames(pickle_file_dir)
        nr_of_pickle_files = len(pickle_files)
        pickle_file_counter = 0
        dis_counter = 1
        
        ####
        p = Pool(nr_of_cpus)
#         for a, ret_type, funcName, baseFileName in funcs_and_ret_types:
#             proc_ret_type_list.append((ret_type, binary_name))
            
        all_ret_types = p.map(proc_build_list_with_label_ints, pickle_files )
        p.close()
        p.join()    
            
        
        ds_counter = 0
        
        print(f'Build tf dataset now')
        dis_list = list()
        ret_list = list()
        
        if all_ret_types:
            for ds in all_ret_types:
                #print(f'type-ds >{type(ds)}<')
                #print(f'numpy-shape >{np.shape(ds)}<')
                if (ds_counter+1) >= nr_of_pickle_files:
                    print(f'From file >{ds_counter+1}/{nr_of_pickle_files}<', end='\n')
                else:
                    print(f'From file >{ds_counter+1}/{nr_of_pickle_files}<', end='\r')
                
                dis_list.clear()
                ret_list.clear()
                
                for dis,ret in ds:
                    dis_list.append(dis)
                    ret_list.append(ret)
                    
                if ds_counter == 0:
                    dis_ds = tf.data.Dataset.from_tensor_slices(dis_list)
                    ret_ds = tf.data.Dataset.from_tensor_slices(ret_list)
                    
                    raw_dataset = tf.data.Dataset.zip( (dis_ds, ret_ds ))
                    #ds_item = next(iter(raw_dataset))
                    #print(f'ds_item >{ds_item}<')
                    #ds_counter = 1
                else:
                    dis_ds = tf.data.Dataset.from_tensor_slices(dis_list)
                    ret_ds = tf.data.Dataset.from_tensor_slices(ret_list)
                    
                    ds_tmp = tf.data.Dataset.zip( (dis_ds, ret_ds ))
                    raw_dataset = raw_dataset.concatenate( ds_tmp )
                    
                ds_counter += 1
      
        ####
        
#         for file in pickle_files:
#             pickle_file_counter += 1
#             
#             cont = get_pickle_file_content(pickle_file_dir + '/' + file)
#             for dis,ret in cont:
#                 print(f'Tokenized file {pickle_file_counter}/{nr_of_pickle_files} and >{dis_counter}< assemblies', end='\r')
#                 dis_counter += 1
#                 
#                 ret_type_int = ret_type_dict[ret] - 1
#                 if ds_counter == 0:
#                     #print(f'dis >{dis}<')
#                     
#                     #raw_dataset = tf.data.Dataset.from_tensor_slices(dis_ret )
#                     raw_dataset = tf.data.Dataset.from_tensors( (dis, ret_type_int)  )
#                     ds_counter = 1
#                 else:
#                     #ds = tf.data.Dataset.from_tensor_slices(dis_ret )
#                     ds = tf.data.Dataset.from_tensors( (dis, ret_type_int) )
#                     raw_dataset = raw_dataset.concatenate( ds )
#     
    
        ### save dataset 
        print(f'Saving raw_dataset to file >{raw_dataset_path}<')
        tf.data.experimental.save(raw_dataset, raw_dataset_path)
      
    
    ##debug
#     for text_batch, label_batch in raw_dataset.take(1):
#         print(text_batch.numpy()[i])
#         print(label_batch.numpy()[i])
#         print()
    

    for x, y in raw_dataset:
        print(f'x: >{x.numpy()}<  y: >{y.numpy()}<')
        break
    print(f'raw_dataset element_spec >{raw_dataset.element_spec}<')
    
    text_ds = raw_dataset.map(lambda x, y: x)
    print(f'text_ds element_spec >{text_ds.element_spec}<')
    vectorize_layer.adapt(text_ds)
    
    #a = next(iter(text_ds))
    x = next(iter(raw_dataset))
    print(f'x-next-iter >{x[0].numpy()}<')
    print(vectorize_text(x[0], x[1]) )
    #x = vectorize_layer(x)
    #print(f'x vec-layer type: >{type(x)}<')
    #print(f'x vec-layer numpy: >{x.numpy()}<')
    #print(f'x vec-layer: >{x}<')
    
    
    v = vectorize_layer.get_vocabulary()
    c =0
    for v1 in v:
        print(f'vec-vocab: >{v1}<')
        c += 1
        if c > 6:
            break
    print(f'len vec-vocab: >{len(v)}')
    #exit()
    
    ### split dataset
    DATASET_SIZE = tf.data.experimental.cardinality(raw_dataset).numpy()
    train_size = int(0.7 * DATASET_SIZE)
    val_size = int(0.15 * DATASET_SIZE)
    test_size = int(0.15 * DATASET_SIZE)
    
    print(f'We split dataset >{DATASET_SIZE}< into train >{train_size}< val >{val_size}< test >{test_size}<')
    
    train_dataset = raw_dataset.take(train_size)
    remaining = raw_dataset.skip(train_size)
    test_dataset = remaining.take(test_size)
    val_dataset = remaining.skip(test_size)
    
    train_dataset = train_dataset.batch(1000, drop_remainder=False)
    val_dataset = val_dataset.batch(1000, drop_remainder=False)
    test_dataset = test_dataset.batch(1000, drop_remainder=False)
    
    print(f'train_ds element_spec-2 >{train_dataset.element_spec}<')
    
    print(f'train_dataset element_spec >{train_dataset.element_spec}<')
    
    print(f'train_dataset size >{tf.data.experimental.cardinality(train_dataset).numpy()}<')
    print(f'test_dataset size >{tf.data.experimental.cardinality(test_dataset).numpy()}<')
    print(f'val_dataset size >{tf.data.experimental.cardinality(val_dataset).numpy()}<')
    

    text_batch, label_batch = next(iter(train_dataset))
    first_review, first_label = text_batch, label_batch
    print("Review", first_review)
    print("Label", first_label)
    print("Vectorized review", vectorize_text(first_review, first_label))
    
    
    ### vec text
    train_ds = train_dataset.map(vectorize_text)
    val_ds = val_dataset.map(vectorize_text)
    test_ds = test_dataset.map(vectorize_text)
    
    print(f'train_ds element_spec >{train_ds.element_spec}<')
    

    
#     train_ds = train_dataset
#     val_ds = val_dataset
#     test_ds = test_dataset

    ### config for performance
    AUTOTUNE = tf.data.experimental.AUTOTUNE

    train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)
    test_ds = test_ds.cache().prefetch(buffer_size=AUTOTUNE)
    
    ## build model
    embedding_dim = 8
    
    model = tf.keras.Sequential([tf.keras.layers.Embedding(int(vocab_size)+2, embedding_dim, mask_zero=True),
                                    tf.keras.layers.Dropout(0.2),
                                    tf.keras.layers.GlobalAveragePooling1D(),
                                    tf.keras.layers.Dropout(0.2),
                                    tf.keras.layers.Dense(len(ret_type_dict))])
    
#     model = tf.keras.Sequential([tf.keras.layers.Embedding(int(vocab_size) + 1, embedding_dim, mask_zero=True),
#                                 tf.keras.layers.Dropout(0.2),
#                                 tf.keras.layers.GlobalAveragePooling1D(),
#                                 tf.keras.layers.Dropout(0.2),
#                                 tf.keras.layers.Dense(len(ret_type_dict))])

    model.summary()

                                  
    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=tensorboard_logdir, 
                                                             histogram_freq=1, 
                                                             write_graph=False, 
                                                             write_images=True)
                                                            
    #tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=tensorboard_logdir)

    
    model_checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
        filepath=checkpoint_filepath,
        save_weights_only=True,
        monitor='accuracy',
        mode='max',
        save_best_only=True)

    print(f'Storing tf checkpoint files to: {checkpoint_filepath}')
    
    model.compile(loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True), 
                optimizer='adam', 
                metrics=['accuracy'])

    history = model.fit(train_ds,
                        validation_data=val_ds,
                        epochs=5,
                        callbacks=[tensorboard_callback, model_checkpoint_callback])

    ### evaluate the model
    loss, accuracy = model.evaluate(test_ds)
    print("Loss: ", loss)
    print("Accuracy: ", accuracy)

    ### save trained word embeddings
    save_trained_word_embeddings(date_str, model)


if __name__ == "__main__":
    main()

   
    
    