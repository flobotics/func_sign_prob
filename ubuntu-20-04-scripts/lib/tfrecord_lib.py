import os

def get_all_tfrecord_filenames(tfrecord_file_dir):
    files = os.listdir(tfrecord_file_dir)
    tfrecord_files = list()
    for f in files:
        if f.endswith(".tfrecord"):
            tfrecord_files.append(f)
    
    return tfrecord_files