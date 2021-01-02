###konclude, mysql*, ovn*, cmake


import subprocess
import pickle
import glob
import os
import pexpect
import sys
import psutil
from shutil import copyfile

sys.path.append('../lib/')
import common_stuff_lib
import pickle_lib
import tarbz2_lib
import gdb_lib

gcloud = False

def get_pickle_list(path):
    file_list = []
    file_list = glob.glob(path + '*.pickle.tar.bz2')
    #print(file_list)
    return file_list

def open_pickle(filename):
    #filename = "/tmp/test/tree.pickle"
    infile = open(filename,'rb')
    pickle_list = pickle.load(infile, encoding="latin1")
    infile.close()
    
    return pickle_list


def get_start_end_line_of_func(source_file, func_name, verbose=False):
    start = ''
    end = ''
    
    if verbose:
        print(f'source_file:{source_file} and func_name:{func_name}')
        
    #source_file = "/home/ubu/Documents/src-tree/tree-1.8.0/" + source_file

    ###ctags -x --c-kinds=f /home/ubu/Documents/src-tree/tree-1.8.0/color.c
    ctags_funcs = subprocess.run(['ctags',
                                 "-x",
                                 "--c-kinds=f",
                                 source_file],
                                capture_output=True,
                                universal_newlines=True)
    
    ctags_funcs_out = ctags_funcs.stdout
    ctags_funcs_out_split = ctags_funcs_out.split("\n")
    
    if verbose:
        #print(f'ctags_funcs_out:{ctags_funcs_out_split}')
        pass
    
    ### searching for function and get the start-line, to compare later with ctags output
    for ctags_funcs_split in ctags_funcs_out_split:
        #if verbose:
            #print(f'\n\nsplit:{ctags_funcs_split}  funcname:{func_name}')
        ctags_funcs_split_split = ctags_funcs_split.split()
        #print(f'split-split:{ctags_funcs_split_split}')
        if (len(ctags_funcs_split_split) >= 3) and (ctags_funcs_split_split[0] == func_name):
            #print(f'split-func:{ctags_funcs_split_split[2]}')
            start = ctags_funcs_split_split[2]
            if verbose:
                print(f'found >{func_name}< start-line >{start}<')
            break
      
    if start == '':
        print("func start-line not found-------------")
        return (start, end)
    
    ## ctags --fields=+ne -o - --sort=no tree.c|grep usage
    ctags = subprocess.run(["ctags", 
                                "--fields=+ne", 
                                "-o", 
                                "-", 
                                "--sort=no", 
                                source_file], 
                               capture_output=True, 
                               universal_newlines=True)

    ctags_out = ctags.stdout
    
    if verbose:
        #print(f'ctags_out: {ctags_out}')
        pass
        
    ctags_out_split = ctags_out.split('\n')
    
    for items in ctags_out_split:
        #print(f'items: {items}\n')
        if func_name in items:
            if verbose:
                print(f'func_name in items: {items}\n')
            if "line:" + start in items:
                if verbose:
                    print(f'start-line found, so end: should be here')
                for subItem in items.split():
                    if verbose:
                        print(f'subItem:{subItem}')
                    if "end:" in subItem:
                        end = subItem.replace('end:','')
                        if verbose:
                            print(f'found end-line:{end}')
                        return (start,end)

    
    return (start,end)


def get_full_path(base_source_path, filename):
    #filename = 'format'
    out = subprocess.run(["find", base_source_path, "-type", "f", "-name", filename], capture_output=True, universal_newlines=True)
    find_out = out.stdout

    full_path = list()
    
    for file in find_out.split('\n')[0:-1]:
        full_path.append(file)
        
    return full_path

def get_source_code(src_file, func_name, gdb_func_sign):
    src_code = list()
    gdb_func_sign_ret_type = ''
    
    print(f'src_file:{src_file}')
    print(f'func_name:{func_name}')
    print(f'gdb_func_sign:{gdb_func_sign}')
    idx = gdb_func_sign.index('(')
    if idx:
        print('found gdb (')
        gdb_func_sign_ret_type = gdb_func_sign[:idx]
        print(f'gdb_func_sign_ret_type:{gdb_func_sign_ret_type}')
            
    
    start_end_lines = list()
    
    start, end = get_start_end_line_of_func(src_file, func_name, verbose=True)
    print(f'source-file: {src_file} func-name: {func_name} start:{start}   end:{end}')
    start_end_lines.append((src_file, func_name, start, end))

        
    ### now that we got start and end line numbers, we copy the src code
    ### we need to check here if we need to copy some lines above the start-line
    ### because ctags does not find the correct start line if return-type is above line
    if start and end:
        with open(src_file) as f:
            lines = [line.rstrip() for line in f]

        ##get first line ctags thinks
        first_line = lines[start]
        print(f'first_line:{first_line}')
        ### get return-type
        ## get first occurece of (
        idx = first_line.index('(')
        if idx:
            print(f'found (')
            pre_first_line = first_line[:idx]
            print(f'pre_first_line:{pre_first_line}')
            ### check if its full return type
            if gdb_func_sign_ret_type == pre_first_line:
                print('found full ret_type')
        
        
        
        
            
        l = 1
        for line in lines:
            if l >= int(start) and l <= int(end):
                #print(f'line:{l} content:{line}')
                src_code.append(line)
            l+=1
     
    return src_code


# def install_source_package(src_package, config):
#     print(f"We install with apt-source the source-package of package: {src_package} into : {config['ubuntu_src_pkgs']}{src_package}")
#     try:
#         os.mkdir(config['ubuntu_src_pkgs'] + src_package)
#     except OSError:
#         print (f"Creation of the directory {config['ubuntu_src_pkgs']}{src_package} failed")
#     else:
#         print (f"Successfully created the directory {config['ubuntu_src_pkgs']}{src_package}")
#     
#         os.chdir(config['ubuntu_src_pkgs'] + src_package)
# 
#         ###install the package
#         #child = pexpect.spawn('apt source -y {0}'.format(src_package), timeout=None)
#         #if not gcloud:
#         #    child.expect('ubu:', timeout=None)
#             # enter the password
#        #    child.sendline('ubu\n')
#         #print(child.read())
#         #tmp = child.read()
#         
#         out = subprocess.run(["apt", 
#                           "source",
#                           src_package],
#                           capture_output=True, 
#                           universal_newlines=True)
#         gdb_out = out.stdout
#         
        
def get_dirname_of_src(pickle_file_name):
    print(f'get_dirname_of_src: {pickle_file_name}')
    src_dir_name = ''
     
    for file_ in os.listdir(pickle_file_name):
        #print(f'file:{file_}')
        if os.path.isdir(pickle_file_name + '/' + file_):
            print(f'dir:{file_}')
            src_dir_name = file_
             
    return src_dir_name


def check_if_src_match_binary(pickle_file_name, dir_name, config):
    
    #print(f'Need to "apt install" and "apt install x-dbgsym" to work .hmmm')
    
            
    print(f'Checking with gdb which functions exist in pickle_file_name >{pickle_file_name}<')
    ###get inside src dir and exec gdb
    src_dir_name = get_dirname_of_src(dir_name + pickle_file_name)
    os.chdir(dir_name + pickle_file_name + '/' + src_dir_name)
    
    
    
    out = subprocess.run(["gdb",
                          "-batch",
                          "-ex",
                          "file {}".format(pickle_file_name),
                          "-ex",
                          "info functions"],
                          capture_output=True, 
                          universal_newlines=True)
    gdb_out = out.stdout
    print(f'gdb_out:{gdb_out}') 
    
    
    ### select the first file
    src_file = ''
    for line in gdb_out.split('\n'):
        linesplit = line.split()
        if (len(linesplit) >= 2) and linesplit[0] == 'File':
            #print(f'found file: {linesplit[1]}')
            src_file = linesplit[1]
            break
        
    print(f'Found source filename >{src_file}<')
    
    #exit()
    
    nr_tokens = 0
    
    ## check how many times ../ tokens are there
    if len(src_file) > 0:
        nr_tokens = src_file.count('../')
        print(f'found ../ >{nr_tokens}< times')
        
    ### create as many dirs as nr_tokens
    import pathlib
    path_to_create = "/tmp/" + pickle_file_name + "/" + dir_name + "/"
    for i in range(nr_tokens):
        path_to_create = path_to_create + "aaaaa/"

    pathlib.Path(path_to_create).mkdir(parents=True, exist_ok=True)
    
    ### change to new dir
    os.chdir(path_to_create)
    
    src_file_base = os.path.basename(src_file)
    print(f'src_file_base:{src_file_base}')
    
    out = subprocess.run(["gdb",
                          "-batch",
                          "-ex",
                          "file {}".format(pickle_file_name),
                          "-ex",
                          "list {}".format('glob_filename'),],
                          capture_output=True, 
                          universal_newlines=True)
    gdb_out = out.stdout
    gdb_stderr = out.stderr
    
    #print(f'gdb_stderr:{gdb_stderr}')
    #print(f'gdb_out:{gdb_out}')
    if "warning: Source file is more recent than executable." in gdb_stderr:
        print(f'src more recent than installed executable')  
        return False
    else:
        return True

#res = check_if_src_match_binary("bash", "bash-5.0")
#print(f'result:{res}')


def unpack_second_src(pickle_file_name):
    tarfile = ''
    tar_option = ''
    first_src_dir = ''
    
    ### check the ending e.g. .tar.bz2 .tar.gz .tar.xz
    for file_ in os.listdir("/tmp/" + pickle_file_name):
        #print(f'file:{file_}')
        if os.path.isfile("/tmp/" + pickle_file_name + '/' + file_):
            if "orig" in file_:
                print(f'file:{file_}')
                tarfile = file_
        if os.path.isdir("/tmp/" + pickle_file_name + '/' + file_):
            first_src_dir = file_
            
    tarfile_split = tarfile.split(".")
    if tarfile_split[-1] == "xz":
        print(f'found xz ending')
        tar_option = '-xJf'
    else:
        print(f'ERRROR no recognized ending')
        exit()
            
            
    ###remove first src folder, because name is (mostly??) the same of untarred pkg     
    #os.rmdir("/tmp/" + pickle_file_name + '/' + first_src_dir)
    os.rename("/tmp/" + pickle_file_name + '/' + first_src_dir, "/tmp/" + pickle_file_name + '/' + "backup-" + first_src_dir)

    print(f'tarfile:{tarfile} pickle_file_name:{pickle_file_name} tar_option:{tar_option}')    
        
    os.chdir("/tmp/" + pickle_file_name)
    out = subprocess.run(["tar",
                          tar_option,
                          tarfile], capture_output=True, universal_newlines=True)
    tar_out = out.stdout
    print(f'tar_out:{tar_out}')
    
    
#unpack_second_src("bash")

def copy_files_to_build_dataset(config):
    pickle_files = common_stuff_lib.get_all_filenames_of_type(config['pickle_dir'], '.tar.bz2')
    if len(pickle_files) > 0:
        decision = 'z'
        while( (decision != 'y') and (decision != 'n' ) ):
            decision = input(f"There are still files in >{config['pickle_dir']}< . Do you want to use them: Type in (y/n):")
    
        if decision == 'y':
            print(f'Using files still there')
            return
            
    pickle_path = config['git_repo_path'] + '/ubuntu-20-04-pickles/'
    
    pickle_files = common_stuff_lib.get_all_filenames_of_type(pickle_path, '.tar.bz2')
    counter = 0
    for file in pickle_files:
        counter += 1
      
    nr_files = 'z'
    while( not nr_files.isdecimal()):
        nr_files = input(f'In directory >{pickle_path}< are >{counter}< files.\nHow many files to use for dataset? Type in:')
    
    counter = 0
    for file in pickle_files:
        print(f'Copy file >{file}<                 ', end='\r')
        copyfile(pickle_path + file, config['pickle_dir'] + file)
        counter += 1
        if counter >= int(nr_files):
            break
        
    print(f'Copied >{nr_files}< files')
    print()



def check_config(config):
    if config['base_dir'] == '':
        print(f'Please specify a base-dir (-b or --base-dir) , where all work is done. Check -h for help.')
        exit()
        
    if not os.path.isdir(config['base_dir']):
        print(f"Creating >{config['base_dir']}<")
        os.mkdir(config['base_dir'])
        
    if not os.path.isdir(config['pickle_dir']):
        print(f"Creating >{config['pickle_dir']}<")
        os.mkdir(config['pickle_dir'])
        
    if not os.path.isdir(config['ubuntu_src_pkgs']):
        print(f"Creating >{config['ubuntu_src_pkgs']}<")
        os.mkdir(config['ubuntu_src_pkgs'])
        
    if not os.path.isdir(config['work_dir']):
        print(f"Creating >{config['work_dir']}<")
        os.mkdir(config['work_dir'])
    


##### main
def main():
    config = common_stuff_lib.parseArgs()
    check_config(config)
    
    nr_of_cpus = psutil.cpu_count(logical=True)
    print(f'We got >{nr_of_cpus}< CPUs for threading\n')
    print()
    
    copy_files_to_build_dataset(config)
    
    pickle_files = common_stuff_lib.get_all_filenames_of_type(config['pickle_dir'], '.tar.bz2')
    ### print 5 files, check and debug
    pickle_lib.print_X_pickle_filenames(pickle_files, 5)
    
    
    ###loop through all pickle.tar.bz2 files
    for pickle_file in pickle_files:
        print(f"Untar pickle-file >{pickle_file}< to >{config['work_dir']}<")
        
        tarbz2_lib.untar_file_to_path(config['pickle_dir'] + pickle_file, config['work_dir'])
        
        
        ###install source-package of pickle-file-content
        pickle_file_name = os.path.basename(pickle_file)
        pickle_file_name = pickle_file_name.replace('.pickle.tar.bz2', '')
        
        gdb_lib.install_source_package(pickle_file_name, config)
        
        
        
        ###check with gdb (list cmd) if the sources are newer/older than binary
        ## warning: Source file is more recent than executable.
        ###get dir name
        
        dir_name = config['ubuntu_src_pkgs']
        ##dir_name = get_dirname_of_src(pickle_file_name)
        print(f'Dir with src is:{dir_name}')
        res = check_if_src_match_binary(pickle_file_name, dir_name, config)
               
        
        ##src and binary dont match, unpack the second src in the dir
        if not res:
            unpack_second_src(pickle_file_name)
            res = check_if_src_match_binary(pickle_file_name, dir_name)
            print(f'res of second src dir: {res}')
        else:
            print(f'src match binary')
        
        #break
        
        
        ###open the pickle
        print(f"Open untarred pickle file: >{config['work_dir'] + pickle_file}<")
        pickle_content = open_pickle(config['work_dir'] + pickle_file.replace('.tar.bz2', ''))
        
        #print(f'pickle_content >{pickle_content}<')
        
        
        #exit()
        
        fcn = ''
        fl = ''
        bina = ''
        gdb_func_sign = ''
        ### loop through the pickle-file and get source-code from function
        #print(f'pickle-content: {next(iter(pickle_content))}')
        for funcSign, gdb_ret_type, func_name, file_name, disas_att, disas_intel, package_name, binary in pickle_content:
            print(f'funcSign: {funcSign}')
            #print(f'gdb_ret_type: {gdb_ret_type}')
            print(f'func_name: {func_name}')
            print(f'file_name: {file_name}')
            #print(f'disas_att: {disas_att}')
            #print(f'disas_intel: {disas_intel}')
            print(f'package_name: {package_name}')
            print(f'binary: {binary}')
            fcn = func_name
            fl = file_name
            bina = binary
            gdb_func_sign = funcSign
            #break
        
            ### get source code of function
            pkg_name = pickle_file.replace('.pickle.tar.bz2', '')
            pkg_name = os.path.basename(pkg_name)
            print(f'pkg_name:{pkg_name}')
    
            #pkg_src_name = "/tmp/" + pkg_name + "/" + dir_name
            pkg_src_name = config['ubuntu_src_pkgs']
            
            print(f'pkg_src_name:{pkg_src_name}')
    
            full_path = get_full_path(pkg_src_name, fl)
            print(f'full-path:{full_path}')
    
            len_full_path = len(full_path)
            nr_of_empty_src_code = 0
    
            ### ctags does not get return-type if its located lines above func_name
            ### gdb funcSign got it, we need to check if we need more lines than ctags tells us
            for f in full_path:
                src_code = get_source_code(f, fcn, gdb_func_sign)
                if src_code:
                    print(f'src-code:{src_code}')
                else:
                    print(f'no src-code found')
                    nr_of_empty_src_code += 1
    
            print(f'nr_of_empty_src_code:{nr_of_empty_src_code}   len_full_path:{len_full_path}')
            if len_full_path == nr_of_empty_src_code+1:
                print('only found one source code, thats good')
            else:
                print('ERROR found more than one source code for a function')
                break
    
        #break


if __name__ == "__main__":
    main()