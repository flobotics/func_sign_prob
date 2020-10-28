import getopt
import sys
import tensorflow as tf
import pickle
import re
import string
from tensorflow.keras import Model, Sequential
from tensorflow.keras.layers import Activation, Dense, Embedding, GlobalAveragePooling1D
from tensorflow.keras.layers.experimental.preprocessing import TextVectorization
import os


def get_pickle_file_content(full_path_pickle_file):
    pickle_file = open(full_path_pickle_file,'rb')
    pickle_list = pickle.load(pickle_file, encoding='latin1')
    pickle_file.close()
    
    return pickle_list


def get_vocab_size(vocab_size_file):
    file = open(vocab_size_file,'r')
    ret = file.read()
    file.close()
    return ret


def parseArgs():
    short_opts = 'ht:v:e:f:s:c:t:r:l:'
    long_opts = ['tfrecord-train-dir=', 'tfrecord-val-dir=', 'tfrecord-test-dir=', 'vocab-file=', 'seq-length-file=',
                 'checkpoint-dir=', 'vocab-size-file=', 'ret-type-dict-file=', 'tensorboard-log-dir=']
    config = dict()
    
    config['tfrecord_train_dir'] = '/tmp/tf_record_dir/train/'
    config['tfrecord_val_dir'] = '/tmp/tf_record_dir/val/'
    config['tfrecord_test_dir'] = '/tmp/tf_record_dir/test/'
    config['vocab_file'] = '/tmp/vocab.pickle'
    config['seq_length_file'] = "/tmp/sequence_length.txt"
    config['checkpoint_dir'] = '/tmp/logs/checkpoint.ckpt'  ##need to be in base-dir for projector to work
    config['vocab_size_file'] = "/tmp/vocab_size.txt"
    config['ret_type_dict_file'] = "/tmp/ret_type_dict.pickle"
    config['tensorboard_log_dir'] = '/tmp/logs'
    
    
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
        elif option_key in ('-c', '--checkpoint-dir'):
            config['checkpoint_dir'] = option_value[1:]
        elif option_key in ('-t', '--vocab-size-file'):
            config['vocab_size_file'] = option_value[1:]
        elif option_key in ('-r', '--ret-type-dict-file'):
            config['ret_type_dict_file'] = option_value[1:]
        elif option_key in ('-l', '--tensorboard-log-dir'):
            config['tensorboard_log_dir'] = option_value[1:]
        elif option_key in ('-h'):
            print(f'<optional> -p or --pickle-dir The directory with disassemblies,etc. Default: /tmp/save_dir')
           
           
    return config   


def _parse_function(example_proto):
    # Create a description of the features.
    feature_description = {
        'caller_callee': tf.io.FixedLenFeature([], tf.string, default_value=''),
        'label': tf.io.FixedLenFeature([], tf.string, default_value=''),
    }
    
    # Parse the input `tf.train.Example` proto using the dictionary above.
    ex = tf.io.parse_single_example(example_proto, feature_description)
    
    return ex['caller_callee'], ex['label']


def get_vocab(config):
    vocab_word_list = list()
    
    ### get vocabulary, to feed into textvectorization.set_vocabulary() , much faster than .adapt()
    if os.path.isfile(config['vocab_file']):
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
    else:
        print(f'No vocabulary file found, we build it now')
            
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

def configure_for_performance(ds):
  ds = ds.cache()
  ds = ds.shuffle(buffer_size=1000)
  ds = ds.batch(100)
  ds = ds.prefetch(buffer_size=tf.data.experimental.AUTOTUNE)
  return ds
  
def get_vocab_size(vocab_size_file):
    file = open(vocab_size_file,'r')
    ret = file.read()
    file.close()
    return ret

global_ret_type_dict = dict()

### wrapper to convert tensor to eagerTensor for .numpy
def map_label_to_int_wrapper(text, label):
    return tf.numpy_function(func=map_label_to_int, 
                             inp=[text,label], 
                             Tout=[tf.string, tf.int64])

def map_label_to_int(text, label):
    global global_ret_type_dict
    
    text = bytes.decode(text)
    label = bytes.decode(label)
    #print(f'text >{text}< \nlabel >{label}<')
    
    #print(f'global_ret_type_dict >{global_ret_type_dict}<')
    #global_ret_type_dict_int = global_ret_type_dict[label.encode('utf-8')]
    #print(f'global_ret_type_dict_int >{global_ret_type_dict_int}<')
    
    #tf.expand_dims(text, -1)
    #tf.reshape(tf_string, ())
    return text, global_ret_type_dict[label.encode('utf-8')]


def set_lost_shapes(text, label):
    text.set_shape([])
    label.set_shape([])
    
    return text, label

#vocab_size_file = "/tmp/vocab_size.txt"
#vocab_size = get_vocab_size(vocab_size_file)
#print(f'vocab-size from file >{vocab_size}<')
#sequence_length = get_sequence_length('/tmp/sequence_length.txt')
### add 2   UNK and empty
vectorize_layer = TextVectorization(standardize=None,
                                    max_tokens=None,
                                    output_mode='int',
                                    output_sequence_length=None)

def save_vocab_word_list(vocab_word_list, file):
    ret_file = open(file, 'wb+')
    pickle_list = pickle.dump(vocab_word_list, ret_file)
    ret_file.close()
    
    

def main():
    global global_ret_type_dict
    
    nr_of_cpus = 16
    
    config = parseArgs()
    
    print(f'Build tf.data.dataset with tfrecord files from directory >{config["tfrecord_train_dir"]}< \
            >{config["tfrecord_val_dir"]}< >{config["tfrecord_test_dir"]}<')

    tfrecord_train_dataset = tf.data.Dataset.list_files(config['tfrecord_train_dir'] + '*.tfrecord')
    train_dataset = tf.data.TFRecordDataset(tfrecord_train_dataset)
    
    tfrecord_val_dataset = tf.data.Dataset.list_files(config['tfrecord_val_dir'] + '*.tfrecord')
    val_dataset = tf.data.TFRecordDataset(tfrecord_val_dataset)
    
    tfrecord_test_dataset = tf.data.Dataset.list_files(config['tfrecord_test_dir'] + '*.tfrecord')
    test_dataset = tf.data.TFRecordDataset(tfrecord_test_dataset)
    
#     for raw_record in train_dataset.take(1):
#         example = tf.train.Example()
#         example.ParseFromString(raw_record.numpy())
#         print(f'One example from train_dataset:\n>{example}<')
    
    print(f'tf.data.Dataset element_spec of train_dataset >{train_dataset.element_spec}<')
    
    AUTOTUNE = tf.data.experimental.AUTOTUNE
    print(f'AUTOTUNE value for prefetch >{AUTOTUNE}<')
    
    ## map all elements to string,string 
    train_dataset = train_dataset.map(_parse_function, num_parallel_calls=AUTOTUNE)
    val_dataset = val_dataset.map(_parse_function, num_parallel_calls=AUTOTUNE)
    test_dataset = test_dataset.map(_parse_function, num_parallel_calls=AUTOTUNE)
    train_dataset

    #for text, label in train_dataset.take(1):
    #    print(f'One example from train_dataset with label-as-string:\nText: >{text}<\n Label: >{label}<')
    print(f'train_dataset element_spec >{train_dataset.element_spec}<')    

    ### get unique return types from dataset and map string to int
    label_ds = train_dataset.map(lambda x, y: y, num_parallel_calls=AUTOTUNE)
    tmp_ds = val_dataset.map(lambda x, y: y, num_parallel_calls=AUTOTUNE)
    label_ds = label_ds.concatenate(tmp_ds)
    tmp_ds = test_dataset.map(lambda x, y: y, num_parallel_calls=AUTOTUNE)
    label_ds = label_ds.concatenate(tmp_ds)
    
    label_ds = label_ds.apply(tf.data.experimental.unique())
    #for label in label_ds.take(1):
    #    print(f'One example from text_ds_dataset: Label: >{label}<')
    
    print(f'train_dataset2 element_spec >{train_dataset.element_spec}<')  
        
    ret_type_dict = dict()
    label_counter = 0
    for x in label_ds:
        #print(f'label_ds x >{x.numpy()}< nr >{label_counter}<')
        ret_type_dict[x.numpy()] = label_counter
        label_counter += 1
        
    
    global_ret_type_dict = ret_type_dict
    
    train_dataset = train_dataset.map(map_label_to_int_wrapper, num_parallel_calls=AUTOTUNE)
    val_dataset = val_dataset.map(map_label_to_int_wrapper, num_parallel_calls=AUTOTUNE)
    test_dataset = test_dataset.map(map_label_to_int_wrapper, num_parallel_calls=AUTOTUNE)
    
    print(f'train_dataset3 element_spec >{train_dataset.element_spec}<')  
    
    ### the shape is getting lost with tf.numpy_function(), so we set it again
    train_dataset = train_dataset.map(set_lost_shapes, num_parallel_calls=AUTOTUNE)
    val_dataset = val_dataset.map(set_lost_shapes, num_parallel_calls=AUTOTUNE)
    test_dataset = test_dataset.map(set_lost_shapes, num_parallel_calls=AUTOTUNE)
    
    print(f'train_dataset4 element_spec >{train_dataset.element_spec}<')  
    
    for text, label in train_dataset.take(1):
        print(f'One example from train_dataset with int-as-label:\nText: >{text}<\n Label: >{label}<')
        
    #exit()
    
#     vectorize_layer = TextVectorization(standardize=None,
#                                     max_tokens=None,
#                                     output_mode='int',
#                                     output_sequence_length=int(sequence_length))


    vocab_word_list_set = set()
    
    ## check if vocab file is there
    if os.path.isfile(config['vocab_file']):
        print(f'Set own vocabulary to TextVectorization layer')
        vocab_word_list = get_vocab(config)
        print(f'len vocab_word_list >{len(vocab_word_list)}<')
        vectorize_layer.set_vocabulary(vocab_word_list)
    else:
        print(f'No vocab file. Adapt our text to tf TextVectorization layer, \
                this could take some time ')
        ## add all three datasets together to build a vocab from all
        text_ds = train_dataset.map(lambda x, y: x, num_parallel_calls=AUTOTUNE)
        tmp_ds = val_dataset.map(lambda x, y: x, num_parallel_calls=AUTOTUNE)
        text_ds = text_ds.concatenate(tmp_ds)
        tmp_ds = test_dataset.map(lambda x, y: x, num_parallel_calls=AUTOTUNE)
        text_ds = text_ds.concatenate(tmp_ds)
        print(f'text_ds element_spec >{text_ds.element_spec}<')
        
        text_ds = text_ds.apply(tf.data.experimental.unique())
        for txt in text_ds:
            for txt_part in txt.numpy().split():
                #print(f'txt-part >{txt_part}<')
                vocab_word_list_set.add(txt_part)
        
        vocab_word_list = list(vocab_word_list_set)
        
        if config['vocab_file']:
            print(f'Save vocab-word-list to file >{config["vocab_file"]}<')
            save_vocab_word_list(vocab_word_list, config['vocab_file'])
        else:
            print(f'Save vocab-word-list to file >/tmp/vocab.pickle<')
            save_vocab_word_list(vocab_word_list, "/tmp/vocab.pickle")
            
        vectorize_layer.set_vocabulary(vocab_word_list)
        
        
        #print(f'vocab_size >{len(vectorize_layer.get_vocabulary())}< for model')
        #exit()
        #vectorize_layer.adapt(text_ds.batch(64))
        
    ## print info about vocabulary
    print_vocab_info(vectorize_layer)
    
    
    ### optimize
    train_dataset = configure_for_performance(train_dataset)
    val_dataset = configure_for_performance(val_dataset)
    test_dataset = configure_for_performance(test_dataset)
    
#     train_dataset = train_dataset.shuffle(buffer_size=10000)
#     train_dataset = train_dataset.batch(100)
#     val_dataset = val_dataset.shuffle(buffer_size=10000)
#     val_dataset = val_dataset.batch(100)
#     test_dataset = test_dataset.shuffle(buffer_size=10000)
#     test_dataset = test_dataset.batch(100)
    
    
    ### vec text
    train_dataset = train_dataset.map(vectorize_text, num_parallel_calls=AUTOTUNE)
    val_dataset = val_dataset.map(vectorize_text, num_parallel_calls=AUTOTUNE)
    test_dataset = test_dataset.map(vectorize_text, num_parallel_calls=AUTOTUNE)
    
    ### optimize
    #train_dataset = train_dataset.prefetch(buffer_size=AUTOTUNE)
    
    
    ### the model
    embedding_dim = 8
    
    print(f'Storing tf model checkpoint files to: {config["checkpoint_dir"]}')
    
    print(f'Check if we got a model saved from a previous run')
    if os.path.isdir(config['checkpoint_dir']):
        print(f'Found checkpoint path, think there is a model')
        model = tf.keras.models.load_model(config['checkpoint_dir'])
    else:
        print(f'No checkpoint path, so i think no model, we create one')
        #ret_type_dict = get_pickle_file_content(config['ret_type_dict_file'])
        
        #tf.keras.Input(shape=(1,), dtype=tf.string)
        #vectorize_layer
        
        vocab_size = len(vectorize_layer.get_vocabulary())
        print(f'vocab_size >{vocab_size}< for model')
        
        ##tensors 74   lines in metadata 71
        
        #exit()
        
        model = tf.keras.Sequential([tf.keras.layers.Embedding(int(vocab_size), embedding_dim, mask_zero=True),
                                    tf.keras.layers.Dropout(0.2),
                                    tf.keras.layers.GlobalAveragePooling1D(),
                                    tf.keras.layers.Dropout(0.2),
                                    tf.keras.layers.Dense(len(ret_type_dict))])
        
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
    
    model_checkpoint_callback2 = tf.keras.callbacks.ModelCheckpoint(filepath='/tmp/logs/SaveModel',
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
                        callbacks=[tensorboard_callback, model_checkpoint_callback, model_checkpoint_callback2])

    ### evaluate the model
    loss, accuracy = model.evaluate(test_dataset)
    print("Loss: ", loss)
    print("Accuracy: ", accuracy)

    ### save trained word embeddings
    print(f'Saving trained word embeddings (meta.tsv,vecs.tsv) (usable in tensorboard->Projector)')
    save_trained_word_embeddings(model) 
        
        

if __name__ == "__main__":
    main()
