import tarfile
import os

def untar_file_to_path(full_path_tar_file, work_dir):
    if not os.path.isdir(work_dir):
        print(f'Directory >{work_dir}< to untar tar.bz2 does not exist')
        return
        
    tar = tarfile.open(full_path_tar_file, "r:bz2")  
    tar.extractall(work_dir)
    tar.close()