import tensorflow as tf
from tensorflow.keras import Model, Sequential
from tensorflow.keras.layers import Activation, Dense, Embedding, GlobalAveragePooling1D
from tensorflow.keras.layers.experimental.preprocessing import TextVectorization
import pickle
import os  

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

def vectorize_text(text, label):
    text = tf.expand_dims(text, -1)
    return vectorize_layer(text), label
  

def main():
    full_path_vocab_file = "/tmp/vocab_size.txt"
    full_path_seq_file = "/tmp/sequence_length.txt"
    pickle_file_dir = "/tmp/savetest"
    tensorboard_logdir = "/tmp/logs"
    
    # Vocabulary size and number of words in a sequence.
    vocab_size = get_vocab_size(full_path_vocab_file)
    sequence_length = get_sequence_length(full_path_seq_file)
    
    print(f'Vocabulary size is >{vocab_size}<')
    print(f'Sequence length is >{sequence_length}<')
    
    vectorize_layer = TextVectorization(standardize=None,
                                        max_tokens=int(vocab_size),
                                        output_mode='int',
                                        output_sequence_length=int(sequence_length))

    ### build ds from tokenized files, then get texts
    ds_counter = 0
    pickle_files = get_all_pickle_filenames(pickle_file_dir)
    for file in pickle_files:
        cont = get_pickle_file_content(pickle_file_dir + '/' + file)
        for dis,ret in cont:
            if ds_counter == 0:
                raw_dataset = tf.data.Dataset.from_tensors( (dis, vectorize_layer(ret) ) )
                ds_counter = 1
            else:
                ds = tf.data.Dataset.from_tensors( (dis, vectorize_layer(ret) ) )
                raw_dataset = raw_dataset.concatenate( ds )


    text_ds = raw_dataset.map(lambda x, y: x)
    vectorize_layer.adapt(text_ds)
    
    

    ### split dataset
    DATASET_SIZE = tf.data.experimental.cardinality(raw_dataset).numpy()
    train_size = int(0.7 * DATASET_SIZE)
    val_size = int(0.15 * DATASET_SIZE)
    test_size = int(0.15 * DATASET_SIZE)
    
    train_dataset = raw_dataset.take(train_size)
    remaining = raw_dataset.skip(train_size)
    test_dataset = remaining.take(test_size)
    val_dataset = remaining.skip(test_size)
    
    ### vec text
    train_ds = train_dataset.map(vectorize_text)
    val_ds = val_dataset.map(vectorize_text)
    test_ds = test_dataset.map(vectorize_text)

    ### config for performance
    AUTOTUNE = tf.data.experimental.AUTOTUNE

    train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)
    test_ds = test_ds.cache().prefetch(buffer_size=AUTOTUNE)
    
    ## build model
    embedding_dim = 8
    
    model = tf.keras.Sequential([layers.Embedding(vocab_size + 1, embedding_dim),
                                layers.Dropout(0.2),
                                layers.GlobalAveragePooling1D(),
                                layers.Dropout(0.2),
                                layers.Dense(4)])
                                  
    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=tensorboard_logdir)



    model.compile(loss=losses.SparseCategoricalCrossentropy(from_logits=True), 
                optimizer='adam', 
                metrics=['accuracy'])

    history = model.fit(train_ds,
                        validation_data=val_ds,
                        epochs=5)

    ### evaluate the model
    loss, accuracy = model.evaluate(test_ds)
    print("Loss: ", loss)
    print("Accuracy: ", accuracy)




if __name__ == "__main__":
    main()

   
    
    