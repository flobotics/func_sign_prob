import getopt
import sys
import tensorflow as tf
import pickle
import re
import string
from tensorflow.keras import Model, Sequential
from tensorflow.keras.layers import Activation, Dense, Embedding, GlobalAveragePooling1D
from tensorflow.keras.layers.experimental.preprocessing import TextVectorization


def get_pickle_file_content(full_path_pickle_file):
    pickle_file = open(full_path_pickle_file,'rb')
    pickle_list = pickle.load(pickle_file, encoding='latin1')
    pickle_file.close()
    
    return pickle_list


def parseArgs():
    short_opts = 'ht:v:e:f:s:'
    long_opts = ['tfrecord-train-dir=', 'tfrecord-val-dir=', 'tfrecord-test-dir=', 'vocab-file=', 'seq-length-file=']
    config = dict()
    
    config['tfrecord_train_dir'] = '/tmp/tf_record_dir/train/'
    config['tfrecord_val_dir'] = '/tmp/tf_record_dir/val/'
    config['tfrecord_test_dir'] = '/tmp/tf_record_dir/test/'
    config['vocab_file'] = '/tmp/vocab.pickle'
    config['seq_length_file'] = "/tmp/sequence_length.txt"
    
    
    try:
        args, rest = getopt.getopt(sys.argv[1:], short_opts, long_opts)
    except getopt.GetoptError as msg:
        print(msg)
        print(f'Call with argument -h to see help')
        exit()
    
    for option_key, option_value in args:
        if option_key in ('-t', '--tfrecord-train-dir'):
            config['tfrecord_train_dir'] = option_value[1:]
        elif option_key in ('-v', '--tfrecord-val-dir'):
            config['tfrecord_val_dir'] = option_value[1:]
        elif option_key in ('-e', '--tfrecord-test-dir'):
            config['tfrecord_test_dir'] = option_value[1:]
        elif option_key in ('-f', '--vocab-file'):
            config['vocab_file'] = option_value[1:]
        elif option_key in ('-s', '--seq-length-file'):
            config['seq_length_file'] = option_value[1:]
        elif option_key in ('-h'):
            print(f'<optional> -p or --pickle-dir The directory with disassemblies,etc. Default: /tmp/save_dir')
           
           
    return config   


def _parse_function(example_proto):
    # Create a description of the features.
    feature_description = {
        'caller_callee': tf.io.FixedLenFeature([], tf.string, default_value=''),
        'label_int': tf.io.FixedLenFeature([], tf.int64, default_value=0),
    }
    
    # Parse the input `tf.train.Example` proto using the dictionary above.
    ex = tf.io.parse_single_example(example_proto, feature_description)
    
    return ex['caller_callee'], ex['label_int']


def get_vocab(config):
    vocab_word_list = list()
    
    ### get vocabulary, to feed into textvectorization.set_vocabulary() , much faster than .adapt()
    if config['vocab_file']:
        print(f'We got a vocabulary file, so we use it')
        vocab_ret1 = get_pickle_file_content(config['vocab_file'])
        
        c = 0
        vocab_ret = list(vocab_ret1)
        print(f'Print 3 words from our vocabulary')
        for key in vocab_ret:
            if c <= 2:
                print(f'vocab key >{key}<')
                c += 1
            vocab_word_list.append(str(key))
            
    return vocab_word_list


def print_vocab_info(vectorize_layer):
    v = vectorize_layer.get_vocabulary()
    c =0
    print(f'Print 5 words from TextVectorization layer vocabulary')
    for v1 in v:
        print(f'TextVectorization-vocabulary-word: >{v1}<')
        c += 1
        if c > 6:
            break
    print(f'The TextVectorization layer vocabulary got >{len(v)}< words in it')
    
 
def save_trained_word_embeddings(model):
    trained_dir = "/tmp/logs/trained_word_embeddings"
    vecs_filename = "/tmp/logs/trained_word_embeddings/vecs.tsv"
    meta_filename = "/tmp/logs/trained_word_embeddings/meta.tsv"
    
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

  
def custom_standardization(input_data):
    lowercase = tf.strings.lower(input_data)
    #stripped_html = tf.strings.regex_replace(lowercase, '<br />', ' ')
    stripped_html = tf.strings.regex_replace(lowercase, '\t', ' ')
    return tf.strings.regex_replace(stripped_html,
                                    '[%s]' % re.escape(string.punctuation), '')
 
def get_sequence_length(full_path_seq_file):
    file = open(full_path_seq_file,'r')
    ret = file.read()
    file.close()
    return ret

  
def vectorize_text(text, label):
    text = tf.expand_dims(text, -1)
    return vectorize_layer(text), label


def main():
    nr_of_cpus = 16
    
    config = parseArgs()
    
    print(f'Build tf.data.dataset with tfrecord files from directory >{config["tfrecord_train_dir"]}< \
            >{config["tfrecord_train_dir"]}< >{config["tfrecord_train_dir"]}<')

    tfrecord_train_dataset = tf.data.Dataset.list_files(config['tfrecord_train_dir'] + '*.tfrecord')
    train_dataset = tf.data.TFRecordDataset(tfrecord_train_dataset)
    
    tfrecord_val_dataset = tf.data.Dataset.list_files(config['tfrecord_val_dir'] + '*.tfrecord')
    val_dataset = tf.data.TFRecordDataset(tfrecord_val_dataset)
    
    tfrecord_test_dataset = tf.data.Dataset.list_files(config['tfrecord_test_dir'] + '*.tfrecord')
    test_dataset = tf.data.TFRecordDataset(tfrecord_test_dataset)
    
    for raw_record in train_dataset.take(1):
        example = tf.train.Example()
        example.ParseFromString(raw_record.numpy())
        print(f'One example from train_dataset:\n>{example}<')
    
    print(f'tf.data.Dataset element_spec of train_dataset >{train_dataset.element_spec}<')
    
    ## map all elements to string,int for model.fit
    train_dataset = train_dataset.map(_parse_function, num_parallel_calls=nr_of_cpus)
    val_dataset = val_dataset.map(_parse_function, num_parallel_calls=nr_of_cpus)
    test_dataset = test_dataset.map(_parse_function, num_parallel_calls=nr_of_cpus)
    train_dataset

    for text, label in train_dataset.take(1):
        print(f'One example from train_dataset:\nText: >{text}<\n Label: >{label}<')
        
    sequence_length = get_sequence_length(config['seq_length_file'])
    ### add 2   UNK and empty
    vectorize_layer = TextVectorization(standardize=custom_standardization,
                                        max_tokens=None,
                                        output_mode='int',
                                        output_sequence_length=int(sequence_length))

    ## check if vocab file is there
    if config['vocab_file']:
        print(f'Set own vocabulary to TextVectorization layer')
        vocab_word_list = get_vocab(config)
        vectorize_layer.set_vocabulary(vocab_word_list)
    else:
        print(f'No vocab file. Adapt our text to tf TextVectorization layer, \
                this could take some time ')
        ## add all three datasets together to build a vocab from all
        text_ds = train_dataset.map(lambda x, y: x)
        tmp_ds = val_dataset.map(lambda x, y: x)
        text_ds = text_ds.concatenate(tmp_ds)
        tmp_ds = test_dataset.map(lambda x, y: x)
        text_ds = text_ds.concatenate(tmp_ds)
        print(f'text_ds element_spec >{text_ds.element_spec}<')
        
        vectorize_layer.adapt(text_ds.batch(64))
        
    ## print info about vocabulary
    print_vocab_info(vectorize_layer)
    
    ### optimize
    train_dataset = train_dataset.shuffle(buffer_size=10000)
    train_dataset = train_dataset.batch(100)
    val_dataset = val_dataset.shuffle(buffer_size=10000)
    val_dataset = val_dataset.batch(100)
    test_dataset = test_dataset.shuffle(buffer_size=10000)
    test_dataset = test_dataset.batch(100)
    
    
    ### vec text
    train_dataset = train_dataset.map(vectorize_text)
    val_dataset = val_dataset.map(vectorize_text)
    test_dataset = test_dataset.map(vectorize_text)
    
    ### optimize
    AUTOTUNE = tf.data.experimental.AUTOTUNE
    print(f'AUTOTUNE value for prefetch >{AUTOTUNE}<')
    train_dataset = train_dataset.prefetch(buffer_size=AUTOTUNE)
    
    
    ### the model
    embedding_dim = 8
    
    print(f'Storing tf model checkpoint files to: {config["checkpoint_dir"]}')
    
    print(f'Check if we got a model saved from a previous run')
    if os.path.isdir(config['checkpoint_dir']):
        print(f'Found checkpoint path, think there is a model')
        model = tf.keras.models.load_model(config['checkpoint_dir'])
    else:
        print(f'No checkpoint path, so i think no model, we create one')
        model = tf.keras.Sequential([tf.keras.layers.Embedding(int(vocab_size)+2, embedding_dim, mask_zero=True),
                                        tf.keras.layers.Dropout(0.2),
                                        tf.keras.layers.GlobalAveragePooling1D(),
                                        tf.keras.layers.Dropout(0.2),
                                        tf.keras.layers.Dense(len(ret_type_dict))])
        
    model.summary()

    ## callbacks to save tensorboard-files and model
    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=tensorboard_logdir, 
                                                            histogram_freq=1, 
                                                            write_graph=False, 
                                                            write_images=True)
                                                            

    model_checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(filepath=config['checkpoint_dir'],
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
                        callbacks=[tensorboard_callback, model_checkpoint_callback])

    ### evaluate the model
    loss, accuracy = model.evaluate(test_dataset)
    print("Loss: ", loss)
    print("Accuracy: ", accuracy)

    ### save trained word embeddings
    save_trained_word_embeddings(model) 
        
        

if __name__ == "__main__":
    main()
