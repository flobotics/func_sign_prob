import os

def get_all_filenames_of_type(file_dir, type):
    filtered_files = list()
    
    if not type.startswith("."):
       type = '.' + type
  
    ### check if dir exists
    if not os.path.isdir(file_dir):
        print(f'Directory >{file_dir}< does not exist')
        return filtered_files
    
    files = os.listdir(file_dir)
    
    for f in files:
        if f.endswith(type):
            filtered_files.append(f)
    
    return filtered_files