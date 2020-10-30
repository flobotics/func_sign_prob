import os
import tensorflow as tf

def get_all_tfrecord_filenames(tfrecord_file_dir):
    files = os.listdir(tfrecord_file_dir)
    tfrecord_files = list()
    for f in files:
        if f.endswith(".tfrecord"):
            tfrecord_files.append(f)
    
    return tfrecord_files


def serialize_caller_callee_example(feature0, feature1):
    """
    Creates a tf.train.Example message ready to be written to a file.
    """
    # Create a dictionary mapping the feature name to the tf.train.Example-compatible
    # data type.
    feature0 = feature0.numpy()
    feature1 = feature1.numpy()
 
    feature = {
      'caller_callee_disassembly': tf.train.Feature(bytes_list=tf.train.BytesList(value=[feature0])),
      'callee_return_type_int': tf.train.Feature(int64_list=tf.train.Int64List(value=[feature1])),
    }

    # Create a Features message using tf.train.Example.

    example_proto = tf.train.Example(features=tf.train.Features(feature=feature))
    return example_proto.SerializeToString()    



def tf_serialize_caller_callee_example(f0,f1):
    tf_string = tf.py_function(
      serialize_caller_callee_example,
      (f0,f1),  # pass these args to the above function.
      tf.string)      # the return type is `tf.string`.
    return tf.reshape(tf_string, ()) # The result is a scalar  


def save_caller_callee_to_tfrecord(ds_list, tfrecord_file):
    item0_list = list()
    item1_list = list()
    
    
    if len(ds_list) > 0:
        for item in ds_list:
            #print(f'ds_list_item:{item}')
            #print(f'ds_list_item[0]:{item[0]}')
#             if not isinstance(item[0], str):
#                 print(f'type 0 >{type(item[0])}<')
#             if not isinstance(item[1], int):
#                 print(f'type 1 >{type(item[1])}<')
           
            item0_list.append(item[0])
            item1_list.append(item[1])
            
    tfrecord_dataset = tf.data.Dataset.from_tensor_slices( (item0_list, item1_list) )

    serialized_features_dataset = tfrecord_dataset.map(tf_serialize_caller_callee_example)
    
    
    writer = tf.data.experimental.TFRecordWriter(tfrecord_file)
    writer.write(serialized_features_dataset)
    
 
def split_to_train_val_test(tfrecord_dir):
    ## now get number of tfrecord files, and split numbers
    files = os.listdir(tfrecord_dir)
    nr_of_files = len(files)
    
    print(f'We got >{nr_of_files}< tfrecord files')
    train_size = int(0.7 * nr_of_files)
    val_size = int(0.15 * nr_of_files)
    test_size = int(0.15 * nr_of_files)
    print(f'We split to train >{train_size}< val >{val_size}< test >{test_size}<')
    
    ## create train,val,test dir
    if not os.path.isdir(tfrecord_dir + 'train'):
        os.mkdir(tfrecord_dir + 'train')
    if not os.path.isdir(tfrecord_dir + 'val'):
        os.mkdir(tfrecord_dir + 'val')
    if not os.path.isdir(tfrecord_dir + 'test'):
        os.mkdir(tfrecord_dir + 'test')
    
    ## move files to extra dirs
    counter = 1
    for file in files:
        print(f'----file >{file}<   >{tfrecord_dir}<')
        if counter <= train_size:
            os.rename(tfrecord_dir + file, tfrecord_dir + 'train/' + file)
            counter += 1
        elif counter <= (train_size + val_size):
            os.rename(tfrecord_dir + file, tfrecord_dir + 'val/' + file)
            counter += 1
        else:
            os.rename(tfrecord_dir + file, tfrecord_dir + 'test/' + file)
               
    
    