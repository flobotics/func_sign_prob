import getopt
import tensorflow as tf
from tensorflow.keras import Model, Sequential
from tensorflow.keras.layers import Activation, Dense, Embedding, GlobalAveragePooling1D
from tensorflow.keras.layers.experimental.preprocessing import TextVectorization
import sys
import os
sys.path.append('../../lib/')
import pickle_lib


def parseArgs():
    short_opts = 'hs:w:t:r:m:v:f:'
    long_opts = ['work-dir=', 'save-dir=', 'save-file-type=', 
                 'return-type-dict-file', 'max-seq-length-file=', 'vocab-file=', 'tfrecord-dir=']
    config = dict()
    
    config['work_dir'] = ''
    config['save_dir'] = ''
    config['save_file_type'] = ''
    config['return_type_dict_file'] = ''
    config['max_seq_length_file'] = ''
    config['vocabulary_file'] = ''
    config['tfrecord_dir'] = ''
    config['tensorboard_log_dir'] = ''
    config['checkpoint_dir'] = '' ##need to be in base-dir for projector to work
    config['save_model_dir'] = ''
    config['trained_word_embeddings_dir'] = ''
    
 
    try:
        args, rest = getopt.getopt(sys.argv[1:], short_opts, long_opts)
    except getopt.GetoptError as msg:
        print(msg)
        print(f'Call with argument -h to see help')
        exit()
    
    for option_key, option_value in args:
        if option_key in ('-w', '--work-dir'):
            config['work_dir'] = option_value[1:]
        elif option_key in ('-s', '--save-dir'):
            config['save_dir'] = option_value[1:]
        elif option_key in ('-t', '--save-file-type'):
            config['save_file_type'] = option_value[1:]
        elif option_key in ('-r', '--return-type-dict-file'):
            config['return_type_dict_file'] = option_value[1:]
        elif option_key in ('-m', '--max-seq-length-file'):
            config['max_seq_length_file'] = option_value[1:]
        elif option_key in ('-v', '--vocab-file'):
            config['vocabulary_file'] = option_value[1:]
        elif option_key in ('-f', '--tfrecord-dir'):
            config['tfrecord_dir'] = option_value[1:]
        elif option_key in ('-h'):
            print(f'<optional> -p or --pickle-dir The directory with disassemblies,etc. Default: ubuntu-20-04-pickles')
            print(f'<optional> -w or --work-dir   The directory where we e.g. untar,etc. Default: /tmp/work_dir/')
            print(f'<optional> -s or --save-dir   The directory where we save dataset.  Default: /tmp/save_dir')
            
    if config['work_dir'] == '':
        config['work_dir'] = '/tmp/work_dir/'
    if config['save_dir'] == '':
        config['save_dir'] = '/tmp/save_dir/'
    if config['save_file_type'] == '':
        config['save_file_type'] = 'pickle'
    if config['return_type_dict_file'] == '':
        config['return_type_dict_file'] = config['save_dir'] + 'tfrecord/' + 'return_type_dict.pickle'
    if config['max_seq_length_file'] == '':
        config['max_seq_length_file'] = config['save_dir'] + 'tfrecord/' + 'max_seq_length.pickle'
    if config['vocabulary_file'] == '':
        config['vocabulary_file'] = config['save_dir'] + 'tfrecord/' + 'vocabulary_list.pickle'
    if config['tfrecord_dir'] == '':
        config['tfrecord_dir'] = config['save_dir'] + 'tfrecord/'
    if config['tensorboard_log_dir'] == '':
        config['tensorboard_log_dir'] = config['save_dir'] + 'tensorboard_logs/'
    if config['checkpoint_dir'] == '':
        config['checkpoint_dir'] = config['tensorboard_log_dir'] + 'checkpoint/' ##need to be in base-dir for projector to work
    if config['save_model_dir'] == '':
        config['save_model_dir'] = config['tensorboard_log_dir'] +  'saved_model/'
    if config['trained_word_embeddings_dir'] == '':
        config['trained_word_embeddings_dir'] = config['tensorboard_log_dir'] +  'trained_word_embeddings/'
            
    return config


def check_config(config):
    if not os.path.isdir(config['tfrecord_dir'] + 'train/'):
        print(f"Directory with train tfrecord files >{config['tfrecord_dir'] + 'train/'}< does not exist")
        exit()
        
    if not os.path.isdir(config['tfrecord_dir'] + 'val/'):
        print(f"Directory with train tfrecord files >{config['tfrecord_dir'] + 'val/'}< does not exist")
        exit()
        
    if not os.path.isdir(config['tfrecord_dir'] + 'test/'):
        print(f"Directory with train tfrecord files >{config['tfrecord_dir'] + 'test/'}< does not exist")
        exit()


def _parse_function(example_proto):
    # Create a description of the features.
    feature_description = {
      'caller_callee_disassembly': tf.io.FixedLenFeature([], tf.string, default_value=''),
      'callee_return_type_int': tf.io.FixedLenFeature([], tf.int64, default_value=0),
    }
    
    # Parse the input `tf.train.Example` proto using the dictionary above.
    ex = tf.io.parse_single_example(example_proto, feature_description)
    
    return ex['caller_callee_disassembly'], ex['callee_return_type_int']


def configure_for_performance(ds):
  ds = ds.cache()
  ds = ds.shuffle(buffer_size=1000)
  ds = ds.batch(100)
  ds = ds.prefetch(buffer_size=tf.data.experimental.AUTOTUNE)
  return ds
  

def save_trained_word_embeddings(model, trained_word_embeddings_dir, vectorize_layer):
    vecs_filename = trained_word_embeddings_dir + "vecs.tsv"
    meta_filename = trained_word_embeddings_dir + "meta.tsv"
    
    vocab = vectorize_layer.get_vocabulary()
    print(f'10 vocab words >{vocab[:10]}<')
    
    # Get weights matrix of layer named 'embedding'
    weights = model.get_layer('embedding').get_weights()[0]
    print(f'Shape of the weigths >{weights.shape}<') 
    
    os.mkdir(trained_word_embeddings_dir)
    out_v = open(vecs_filename, 'w+')
    out_m = open(meta_filename, 'w+')
    
    print(f'len vocab-- >{len(vocab)}<')
    
    for num, word in enumerate(vocab):
        if num == 0: continue # skip padding token from vocab
        vec = weights[num]
        #print(f'vec >{vec}<  word >{word}<')
        out_m.write(word + "\n")
        out_v.write('\t'.join([str(x) for x in vec]) + "\n")
        #break
    out_v.close()
    out_m.close()


def main():
    
    AUTOTUNE = tf.data.experimental.AUTOTUNE
    
    config = parseArgs()
    
    check_config(config)
    
    print(f"Build tf.data.dataset with tfrecord files from directory >{config['tfrecord_dir'] + 'train/'}< \
            >{config['tfrecord_dir'] + 'val/'}< >{config['tfrecord_dir'] + 'test/'}<")

    tfrecord_train_dataset = tf.data.Dataset.list_files(config['tfrecord_dir'] + 'train/' + '*.tfrecord')
    train_dataset = tf.data.TFRecordDataset(tfrecord_train_dataset)
    
    tfrecord_val_dataset = tf.data.Dataset.list_files(config['tfrecord_dir'] + 'val/' + '*.tfrecord')
    val_dataset = tf.data.TFRecordDataset(tfrecord_val_dataset)
    
    tfrecord_test_dataset = tf.data.Dataset.list_files(config['tfrecord_dir'] + 'test/' + '*.tfrecord')
    test_dataset = tf.data.TFRecordDataset(tfrecord_test_dataset)
    
    
    train_dataset = train_dataset.map(_parse_function, num_parallel_calls=AUTOTUNE)
    val_dataset = val_dataset.map(_parse_function, num_parallel_calls=AUTOTUNE)
    test_dataset = test_dataset.map(_parse_function, num_parallel_calls=AUTOTUNE)
    
    for text, label in train_dataset.take(1):
        print(f'One example from train_dataset with int-as-label:\nText: >{text}<\n Label: >{label}<')
        
    ###load return-type-dict
    return_type_dict = pickle_lib.get_pickle_file_content(config['return_type_dict_file'])
    
    ###load max-sequence-length 
    max_seq_length = pickle_lib.get_pickle_file_content(config['max_seq_length_file'])
    
    ###load vocabulary list
    vocabulary = pickle_lib.get_pickle_file_content(config['vocabulary_file'])
    
    vocab = vectorize_layer.get_vocabulary()
    print(f'10 vocab words >{vocab[:10]}<')
    
    exit()
    
    vectorize_layer = TextVectorization(standardize=None,
                                    max_tokens=len(vocabulary)+2,
                                    output_mode='int',
                                    output_sequence_length=max_seq_length)
    
    vectorize_layer.set_vocabulary(vocabulary)
    
    
    train_dataset = configure_for_performance(train_dataset)
    val_dataset = configure_for_performance(val_dataset)
    test_dataset = configure_for_performance(test_dataset)
    
    
    embedding_dim = 8
    
    model = tf.keras.Sequential([tf.keras.Input(shape=(1,), dtype=tf.string),
                                 vectorize_layer,
                                 tf.keras.layers.Embedding(len(vocabulary)+2, embedding_dim, mask_zero=True,
                                    name='embedding'),
                                    tf.keras.layers.Dropout(0.2),
                                    tf.keras.layers.GlobalAveragePooling1D(),
                                    tf.keras.layers.Dropout(0.2),
                                    tf.keras.layers.Dense(len(return_type_dict))])
    
    model.summary()
    
    ## callbacks to save tensorboard-files and model
    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=config['tensorboard_log_dir'], 
                                                            histogram_freq=1, 
                                                            write_graph=False, 
                                                            write_images=False)
                                                            

    model_checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(filepath=config['checkpoint_dir'],
                                                                    save_weights_only=True,
                                                                    monitor='accuracy',
                                                                    mode='max',
                                                                    save_best_only=True)
    
    model_checkpoint_callback2 = tf.keras.callbacks.ModelCheckpoint(filepath=config['save_model_dir'],
                                                                    save_weights_only=False,
                                                                    monitor='accuracy',
                                                                    mode='max',
                                                                    save_best_only=True)
       
    model.compile(loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True), 
                optimizer='adam', 
                metrics=['accuracy'])

    history = model.fit(train_dataset,
                        validation_data=val_dataset,
                        epochs=2,
                        )
                        #callbacks=[tensorboard_callback, model_checkpoint_callback, model_checkpoint_callback2])

    ### evaluate the model
    loss, accuracy = model.evaluate(test_dataset)
    print("Loss: ", loss)
    print("Accuracy: ", accuracy)

    ### save trained word embeddings
    print(f'Saving trained word embeddings (meta.tsv,vecs.tsv) (usable in tensorboard->Projector)')
    save_trained_word_embeddings(model, config['trained_word_embeddings_dir'], vectorize_layer) 
    
    
    
    

if __name__ == "__main__":
    main()