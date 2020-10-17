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
import getopt
import sys
from itertools import repeat
import re
import string

nr_of_cpus = 16



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

def get_vocab_size(vocab_size_file):
    file = open(vocab_size_file,'r')
    ret = file.read()
    file.close()
    return ret


def get_sequence_length(full_path_seq_file):
    file = open(full_path_seq_file,'r')
    ret = file.read()
    file.close()
    return ret

vocab_size_file = "/tmp/vocab_size.txt"
full_path_seq_file = "/tmp/sequence_length.txt"
# Vocabulary size and number of words in a sequence.
vocab_size = get_vocab_size(vocab_size_file)
sequence_length = get_sequence_length(full_path_seq_file)


def custom_standardization(input_data):
  lowercase = tf.strings.lower(input_data)
  #stripped_html = tf.strings.regex_replace(lowercase, '<br />', ' ')
  stripped_html = tf.strings.regex_replace(lowercase, '\t', ' ')
  return tf.strings.regex_replace(stripped_html,
                                  '[%s]' % re.escape(string.punctuation), '')


### add 2   UNK and empty
vectorize_layer = TextVectorization(standardize=custom_standardization,
                                        max_tokens=None,
                                        output_mode='int',
                                        output_sequence_length=int(sequence_length))

# vectorize_layer = TextVectorization(standardize=None,
#                                         max_tokens=755+2,
#                                         output_mode='int',
#                                         output_sequence_length=int(sequence_length))

def vectorize_text(text, label):
    text = tf.expand_dims(text, -1)
    return vectorize_layer(text), label
  
  
def save_trained_word_embeddings(date_str, model):
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


def proc_build_list_with_label_ints(file, save_dir):
    global ret_type_dict
    
    ds_counter = 0
    
    ret_list = list()
            
    cont = get_pickle_file_content(file)
    for dis,ret in cont:
        
        ret_type_int = ret_type_dict[ret] -1
        
        #ret_list.append( (dis, ret_type_int) )
        ret_list.append( (dis.encode('utf-8'), ret_type_int) )
        


    ret_file = open(save_dir + os.path.basename(file), 'wb+')
    pickle_list = pickle.dump(ret_list, ret_file)
    ret_file.close()
    
    #return ret_list


def does_file_exist(file):
    if os.path.isfile(file):
        print(f'File >{file}< exists')
    else:
        print(f'File >{file}< does not exist')
        exit()
    
    
def parseArgs():
    short_opts = 'hp:c:t:d:v:s:l:i:r:'
    long_opts = ['pickle-dir=', 'checkpoint-dir=', 'tensorboard-log-dir=', 'tf-dataset-save-dir=', 'vocab-file=',
                 'vocab-size-file=', 'seq-length-file=', 'label-ints-dir=', 'tf-record-dir=']
    config = dict()
    
    config['pickle_dir'] = '/tmp/save_dir'
    config['checkpoint_dir'] = '/tmp/logs/checkpoint'
    config['tensorboard_log_dir'] = '/tmp/logs'
    config['tf_dataset_save_dir'] = '/tmp/logs/tf_dataset_dir'
    config['vocab_file'] = ''
    config['vocab_size_file'] = ''
    config['seq_length_file'] = ''
    config['label_ints_dir'] = '/tmp/label-ints-dir/'
    config['tf_record_dir'] = '/tmp/tf_record_dir/'
    
    try:
        args, rest = getopt.getopt(sys.argv[1:], short_opts, long_opts)
    except getopt.GetoptError as msg:
        print(msg)
        print(f'Call with argument -h to see help')
        exit()
    
    for option_key, option_value in args:
        if option_key in ('-p', '--pickle-dir'):
            config['pickle_dir'] = option_value[1:]
        elif option_key in ('-c', '--checkpoint-dir'):
            config['checkpoint_dir'] = option_value[1:]
        elif option_key in ('-t', '--tensorboard-log-dir'):
            config['tensorboard_log_dir'] = option_value[1:]
        elif option_key in ('-d', '--tf-dataset-save-dir'):
            config['tf_dataset_save_dir'] = option_value[1:]
        elif option_key in ('-v', '--vocab-file'):
            config['vocab_file'] = option_value[1:]
        elif option_key in ('-s', '--vocab-size-file'):
            config['vocab_size_file'] = option_value[1:]
        elif option_key in ('-l', '--seq-length-file'):
            config['seq_length_file'] = option_value[1:]
        elif option_key in ('-i', '--label-ints-dir'):
            config['label_ints_dir'] = option_value[1:]
        elif option_key in ('-r', '--tf-record-dir'):
            config['tf_record_dir'] = option_value[1:]
        elif option_key in ('-h'):
            print(f'<optional> -p or --pickle-dir The directory with disassemblies,etc. Default: /tmp/save_dir')
            print(f'<optional> -w or --checkpoint-dir   The directory where we store tensorflow checkpoints Default: /tmp/logs/checkpoint')
            print(f'<optional> -v or --vocab-file   The file with the vocabulary. Default: None')
            print(f'<optional> -s or --vocab-size-file  The file with the size of the vocabulary. Default: None')
            print(f'<optional> -l or --seq-length-file   The file with the sequence lenght. Default: None')
            print(f'<optional> -i or --label-ints-dir   The directory we store pickles with string,int tuples')
            print(f'<optional> -r or --tf-record-dir   The directory we store tfrecord files')
            
    return config   
    
    

#path_to_return_type_dict_file = "/tmp/full_dataset_att_int_seq_ret_type_dict.pickle"
path_to_return_type_dict_file = "/tmp/ret_type_dict.pickle"
ret_type_dict = get_pickle_file_content(path_to_return_type_dict_file)


def check_if_dir_exists(dir):
    if not os.path.isdir(dir):
        print(f'Directory >{dir}< does not exist. Create it.')
        exit()
        
def serialize_example(feature0, feature1):
    """
    Creates a tf.train.Example message ready to be written to a file.
    """
    # Create a dictionary mapping the feature name to the tf.train.Example-compatible
    # data type.
    feature0 = feature0.numpy()
    feature = {
              'caller_callee': tf.train.Feature(bytes_list=tf.train.BytesList(value=[feature0])),
              'label_int': tf.train.Feature(int64_list=tf.train.Int64List(value=[feature1])),
    }
    
    # Create a Features message using tf.train.Example.
    
    example_proto = tf.train.Example(features=tf.train.Features(feature=feature))
    return example_proto.SerializeToString()  


def tf_serialize_example(f0,f1):
    tf_string = tf.py_function(
      serialize_example,
      (f0,f1),  # pass these args to the above function.
      tf.string)      # the return type is `tf.string`.
    return tf.reshape(tf_string, ()) # The result is a scalar     


def generator():
    for features in raw_dataset:
        yield serialize_example(*features)
    
    
def _parse_function(example_proto):
    # Create a description of the features.
    feature_description = {
        'caller_callee': tf.io.FixedLenFeature([], tf.string, default_value=''),
        'label_int': tf.io.FixedLenFeature([], tf.int64, default_value=0),
    }
    # Parse the input `tf.train.Example` proto using the dictionary above.
    
    ex = tf.io.parse_single_example(example_proto, feature_description)
    e = ex['caller_callee']
    #e = ex.features.feature['features'].bytes_list.value[0]
    print(f'\n\n example parse >{e}<')
    
    #return tf.io.parse_single_example(example_proto, feature_description)
    
    return ex['caller_callee'], ex['label_int']


def check_dir_and_files_exists(config):
    ### check, else exit and inform user
    check_if_dir_exists(config['pickle_dir'])
    check_if_dir_exists(config['label_ints_dir'])
    ##check_if_dir_exists(config['tf_record_dir'])
    
    if config['vocab_file']:
        does_file_exist(config['vocab_file'])
    if config['vocab_size_file']:
        does_file_exist(config['vocab_size_file'])
    if config['seq_length_file']:
        does_file_exist(config['seq_length_file'])

def main():
    global vectorize_layer
    global vocab_size
    global sequence_length
    global vocab_size_file
    global full_path_seq_file
    global nr_of_cpus
    global ret_type_dict
    global path_to_return_type_dict_file
    
    config = parseArgs()
    
    date_str = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    ### check if the dirs and files needed are there, else exit
    check_dir_and_files_exists(config)


    #checkpoint_filepath = config['checkpoint_dir']
    tensorboard_logdir = config['tensorboard_log_dir']
    pickle_file_dir = config['pickle_dir']
    raw_dataset_path = config['tf_dataset_save_dir']
    pickle_file_int_dir = config['label_ints_dir']
    
    
    does_file_exist(path_to_return_type_dict_file)
    
    print(f'tensorflow version >{tf.__version__}<, build with 2.3.1')
    if config['vocab_size_file']:
        print(f'Vocabulary size read from file >{vocab_size_file}< is >{vocab_size}<')
    if config['seq_length_file']:
        print(f'Sequence length read from file >{full_path_seq_file}< is >{sequence_length}<')
    print(f'TF dataset directory is >{raw_dataset_path}<')
    
    print('----\n')  ###for nicer output
    
    ### get vocabulary, to feed into textvectorization.set_vocabulary() , much faster than .adapt()
    if config['vocab_file']:
        print(f'We got a vocabulary file, so we use it')
        vocab_ret1 = get_pickle_file_content(config['vocab_file'])
        vocab_word_list = list()
        c = 0
        vocab_ret = list(vocab_ret1)
        print(f'Print 3 words from our vocabulary')
        for key in vocab_ret:
            if c <= 2:
                print(f'vocab key >{key}<')
                c += 1
            vocab_word_list.append(str(key))
            
        #print(f'vocab-word-list >{vocab_word_list}<')
    print('----\n')  ###for nicer output

    #exit()
    ### get return type dict
    ret_type_dict = get_pickle_file_content(path_to_return_type_dict_file)
    
    got_dataset = False
    ### check if we already got a dataset from tokenized files
#     print(f'Check if we already got a tf.data.Dataset from tokenized files, from a previous run')
#     if os.path.isdir(raw_dataset_path):
#         print(f'Found tf.data.Dataset, will use it')
#         raw_dataset = tf.data.experimental.load(raw_dataset_path, (tf.TensorSpec(shape=(), dtype=tf.string, name=None), tf.TensorSpec(shape=(), dtype=tf.int32, name=None)) )
#         got_dataset = True
#     else:
#         print('No tf.data.Dataset from tokenized files found')

    if os.path.isdir(config['tf_record_dir']):
        got_dataset = True
    
    
    if not got_dataset:
        ### build ds from tokenized files, then get texts
        print(f'Building tf.data.Dataset from tokenized files from dir >{config["pickle_dir"]}<')
        ds_counter = 0
        pickle_files = get_all_pickle_filenames(pickle_file_dir)
        nr_of_pickle_files = len(pickle_files)
        pickle_file_counter = 0
        dis_counter = 1
        
        #### convert string return type to int
        p = Pool(nr_of_cpus)
        
        pickle_files = [config["pickle_dir"] + "/" + f for f in pickle_files]
        star_list = zip(pickle_files, repeat(config['label_ints_dir']))
        all_ret_types = p.starmap(proc_build_list_with_label_ints, star_list)
        #p.map(proc_build_list_with_label_ints, pickle_files )
        p.close()
        p.join()    
            
        
        ds_counter = 0
        
        print(f'Build tf dataset now')
        dis_list = list()
        ret_list = list()
        
        pickle_files_int = get_all_pickle_filenames(pickle_file_int_dir)
        for file in pickle_files_int:
            dis_list.clear()
            ret_list.clear()
            
            cont = get_pickle_file_content(pickle_file_int_dir + file)
            
            if (ds_counter+1) >= nr_of_pickle_files:
                print(f'From file >{pickle_file_int_dir + file}< nr >{ds_counter+1}/{nr_of_pickle_files}<', end='\n')
            else:
                print(f'From file >{pickle_file_int_dir + file}< nr >{ds_counter+1}/{nr_of_pickle_files}<', end='\r')
        
            
            for dis,ret in cont:
                dis_list.append(dis)
                ret_list.append(ret)
                 
            raw_dataset = tf.data.Dataset.from_tensor_slices( (dis_list, ret_list ))

            ## ValueError: Can't convert Python sequence with mixed types to Tensor.
            ##raw_dataset = tf.data.Dataset.from_tensor_slices(cont)
              
            ds_counter += 1
            
            serialized_features_dataset = raw_dataset.map(tf_serialize_example)
#             serialized_features_dataset = tf.data.Dataset.from_generator(
#                                                 generator, output_types=tf.string, output_shapes=())
            
            if ds_counter == 1:
                os.mkdir(config['tf_record_dir'])
            filename = config['tf_record_dir'] + file.replace('.pickle','') + '.tfrecord'
            writer = tf.data.experimental.TFRecordWriter(filename)
            writer.write(serialized_features_dataset)

        
        ### save dataset 
        #print(f'Saving tf.data.Dataset files to directory >{raw_dataset_path}<')
        #tf.data.experimental.save(raw_dataset, raw_dataset_path)
     
    
    ## we read the ds again
    ### we got tfrecord files, so create dataset
    d = config['tf_record_dir']
    print(f'Build dataset with tfrecord files from directory >{d}<')

    tfrecord_files_dataset = tf.data.Dataset.list_files(config['tf_record_dir'] + '*.tfrecord')
    raw_dataset = tf.data.TFRecordDataset(tfrecord_files_dataset)
      
    print('----\n')  ###for nicer output
    
    print(f'Print one element from tf.data.Dataset')
    #a = next(iter(raw_dataset))
    #print(f'proto-string >{a.numpy}<')
    
#     for raw_record in raw_dataset.take(1):
#         print(repr(raw_record))
    for raw_record in raw_dataset.take(1):
        example = tf.train.Example()
        example.ParseFromString(raw_record.numpy())
        print(f'One example: >{example}<')

    
    print(f'tf.data.Dataset element_spec >{raw_dataset.element_spec}<')
    
    #nr = tf.data.experimental.cardinality(raw_dataset).numpy()
    #print(f'Number of item in ds >{nr}<')
    
    raw_dataset = raw_dataset.map(_parse_function, num_parallel_calls=nr_of_cpus)
    raw_dataset
    
    for text,label in raw_dataset.take(1):
        print(f'text: >{text}<  label >{label}<')
        

    #nr = tf.data.experimental.cardinality(raw_dataset).numpy()
    #print(f'Number of item in ds >{nr}<')
    
    #for raw_record in raw_dataset.take(1):
    #   print(f'raw_record >{raw_record}<')
    
    
    print('----\n')  ###for nicer output
    
    if config['vocab_file']:
        print(f'Set own vocabulary to TextVectorization layer')
        vectorize_layer.set_vocabulary(vocab_word_list)
    else:
        text_ds = raw_dataset.map(lambda x, y: x)
        print(f'text_ds element_spec >{text_ds.element_spec}<')
        print(f'Adapt our text to tf TextVectorization layer, this could take some time (+17min on 8vcpu,tesla-p100-gpu)')
        vectorize_layer.adapt(text_ds.batch(64))
    
    
    v = vectorize_layer.get_vocabulary()
    c =0
    print(f'Print 5 words from TextVectorization layer vocabulary')
    for v1 in v:
        print(f'TextVectorization-vocabulary-word: >{v1}<')
        c += 1
        if c > 6:
            break
    print(f'The TextVectorization layer vocabulary got >{len(v)}< words in it')
    
    print('----\n')  ###for nicer output
    
    raw_dataset = raw_dataset.shuffle(buffer_size=10000)
    raw_dataset = raw_dataset.batch(100)
    

    ### vec text
    train_ds = raw_dataset.map(vectorize_text)
#     val_ds = val_dataset.map(vectorize_text)
#     test_ds = test_dataset.map(vectorize_text)
    
    print(f'train_ds element_spec >{train_ds.element_spec}<')
    
#     text_batch, label_batch = next(iter(train_ds))
#     first_review, first_label = text_batch, label_batch
#     print("Text", first_review)
#     print("Label", first_label)
    #print("Vectorized review", vectorize_text(first_review, first_label))
    
#     print('----\n')  ###for nicer output
    

    ### config for performance
    AUTOTUNE = tf.data.experimental.AUTOTUNE
    #AUTOTUNE = 50
    print(f'AUTOTUNE value for prefetch >{AUTOTUNE}<')

    train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)
#     val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)
#     test_ds = test_ds.prefetch(buffer_size=AUTOTUNE)
    
    ## build model
    embedding_dim = 8
    
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
    
#     model = tf.keras.Sequential([tf.keras.layers.Embedding(int(vocab_size) + 1, embedding_dim, mask_zero=True),
#                                 tf.keras.layers.Dropout(0.2),
#                                 tf.keras.layers.GlobalAveragePooling1D(),
#                                 tf.keras.layers.Dropout(0.2),
#                                 tf.keras.layers.Dense(len(ret_type_dict))])

    model.summary()

                                  
    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=tensorboard_logdir, 
                                                             histogram_freq=1000, 
                                                             write_graph=False, 
                                                             write_images=True)
                                                            
    #tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=tensorboard_logdir)

    
    model_checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
        filepath=config['checkpoint_dir'],
        save_weights_only=False,
        monitor='accuracy',
        mode='max',
        save_best_only=True)
    
    d = config['checkpoint_dir']
    print(f'Storing tf checkpoint files to: {d}')
    
    exit()
    
    model.compile(loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True), 
                optimizer='adam', 
                metrics=['accuracy'])

    history = model.fit(train_ds,
                        validation_data=val_ds,
                        epochs=30,
                        callbacks=[tensorboard_callback, model_checkpoint_callback])

    ### evaluate the model
    loss, accuracy = model.evaluate(test_ds)
    print("Loss: ", loss)
    print("Accuracy: ", accuracy)

    ### save trained word embeddings
    save_trained_word_embeddings(date_str, model)


if __name__ == "__main__":
    main()

   
    
    