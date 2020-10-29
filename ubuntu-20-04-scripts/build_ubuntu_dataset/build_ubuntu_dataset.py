import subprocess
import os
import tensorflow as tf
#from tensorflow import keras
#from tensorflow.keras.preprocessing.text import Tokenizer
import pexpect
import numpy as np
import pickle
import getopt
import sys
from multiprocessing import Pool

### amazon cloud aws path
base_path = "/home/ubuntu/git/func_sign_prob/"
### google cloud gcp path
#base_path = "/home/infloflo/git/func_sign_prob/"
### virtualbox path
#base_path = "/home/ubu/git/test2/func_sign_prob/"

### dir where packages-* files are located
config_dir = "ubuntu-20-04-config/"
### dir where the build pickle files are stored
pickles_dir = "ubuntu-20-04-pickles/"

### if aws or gcp is used
gcloud = False

###aws c5d.x12large
nr_of_cpus = 48
###virtualbox
#nr_of_cpus = 2

def parseArgs():
    short_opts = 'hw:u:p:t:c:b:v:'
    long_opts = ['work-dir=', 'git-user=', 'git-pwd=', 'tfrecord-save-dir=', 'config-dir=', 'ubuntu-pwd=', 'verbose=']
    
    config = dict()
    config['work_dir'] = ''
    config['tfrecord_save_dir'] = ''
    config['config_dir'] = ''
    config['git_user'] = ''
    config['git_pwd'] = ''
    config['ubuntu_pwd'] = ''
    config['verbose'] = ''
    
    
    
    try:
        args, rest = getopt.getopt(sys.argv[1:], short_opts, long_opts)
    except getopt.GetoptError as msg:
        print(msg)
        print(f'Call with argument -h to see help')
        exit()
    
    for option_key, option_value in args:
        if option_key in ('-w', '--work-dir'):
            config['work_dir'] = option_value[1:]
        elif option_key in ('-u', '--git-user'):
            config['git_user'] = option_value[1:]
        elif option_key in ('-p', '--git-pwd'):
            config['git_pwd'] = option_value[1:]
        elif option_key in ('-t', '--tfrecord-save-dir'):
            config['tfrecord_save_dir'] = option_value[1:]
        elif option_key in ('-c', '--config-dir'):
            config['config_dir'] = option_value[1:]
        elif option_key in ('-b', '--ubuntu-pwd'):
            config['ubuntu_pwd'] = option_value[1:]
        elif option_key in ('-v', '--verbose'):
            if option_value[1:] in 'False':
                config['verbose'] = False
            else:
                config['verbose'] = True
        elif option_key in ('-h'):
            print(f'<optional> -w or --work-dir The directory where all work is done. Default: /tmp/work')
            print(f'<optional> -u or --git-user  The username for github repo')
            print(f'<optional> -p or --git-pwd  The password for github repo')
            print(f'<optional> -c or --config-dir  The directory to save config files to run this script twice or more, without \
                    doing the same packages again')
            print(f'<optional> -b or --ubuntu-pwd The ubuntu user password to install packages with apt')
     
    if config['work_dir'] == '':
        config['work_dir'] = '/tmp/work/'
    if config['tfrecord_save_dir'] == '':
        config['tfrecord_save_dir'] = config['work_dir'] + 'tfrecord_files/'
    if config['config_dir'] == '':
        config['config_dir'] = config['work_dir'] + 'config-files/'
    if config['git_user'] == '':
        config['git_user'] = ''
    if config['git_pwd'] == '':
        config['git_pwd'] = ''
    if config['ubuntu_pwd'] == '':
        config['ubuntu_pwd'] = ''
    if config['verbose'] == '':
        config['verbose'] = True
    ###check little down for more configs
    
    ###configs without argument, but perhaps depend on configs-with-arguments
    config['filtered_out_config_file'] = config['config_dir'] + 'package-filtered-out.txt'
    config['package_all_config_file'] = config['config_dir'] + 'package-all.txt'
    config['package_work_config_file'] = config['config_dir'] + 'package-work.txt'
    config['package_dont_work_config_file'] = config['config_dir'] + 'package-dont-work.txt'
    config['package_binaries_config_file'] = config['config_dir'] + 'package-binaries.txt'
    
           
    return config   


### get a list with all packages with ending -dbgsym
def get_all_ubuntu_dbgsym_packages(verbose=False):
    pack_dbgsym_list = list()
    pack_with_dbgsym = subprocess.run(['apt-cache', 'search', 'dbgsym'], capture_output=True, universal_newlines=True)
    pack_with_dbgsym_out = pack_with_dbgsym.stdout
    pack_with_dbgsym_out = pack_with_dbgsym_out.split('\n')
    
    for l in pack_with_dbgsym_out:
        if verbose and l:
            print(f'Pkg: {l}')
        if l.split() and l.split()[0].endswith('-dbgsym'):
            if verbose:
                print('Pkg ends with -dbgsym, add to list')
            pack_dbgsym_list.append(l.split()[0])
        else:
            if verbose:
                print('Pkg ends not with -dbgsym, dont add to list')
            pass

    if verbose:
        print(f'We got >{len(pack_dbgsym_list)}< pkgs in our dbgsym list')
        
    if len(pack_dbgsym_list) == 0:
        print("Install ubuntu debug symbol packages")
        exit()
        
    return pack_dbgsym_list



def filter_dbgsym_package_list(dbgsym_list, config, verbose=False):
    new_list = list()
    
    
    
    for item in dbgsym_list:
        subItem = item.split()[0]
        
        filtered_out = False
        
        if subItem.startswith('lib') or subItem.startswith('firmware'):
            if verbose:
                print(f'Filter out, because of >lib,firmware< {subItem}')
            filtered_out = True
            pass
        elif 'plugin' in subItem:
            if verbose:
                print(f'Filter out, because of >plugin< {subItem}')
            filtered_out = True
            pass
        elif 'linux' in subItem:
            if verbose:
                print(f'Filter out, because of >linux< {subItem}')
            filtered_out = True
            pass
        else:
            if verbose:
                print(f'Add to filtered list >{subItem}<')
            new_list.append(subItem)
            
        ### for later inspection what packages we filtered out
        if filtered_out:
            #file = open(base_path + config_dir + "package-filtered-out.txt", "a+")
            file = open(config['filtered_out_config_file'], "a+")
            
            if verbose:
                print(f"Write to >{config['filtered_out_config_file']}< file: {subItem}")
            file.write(str(subItem) + '\n')
            file.close()
    
    if verbose:
        print(f'Length of filtered_pkgs_with_dbgsym:{len(new_list)}')
    
    return new_list



        
def get_binaries_in_package(package, config, verbose=False):
    new_binaries_in_package = list()
    package_work = list()
    c = 0
    already_done = False
    binaries_in_package = list()

    f_without_dbgsym = package.replace('-dbgsym', '')
    already_done = False

    #check if we got this package already
    if verbose:
        print(f"Check in file >{config['package_all_config_file']}< if we already processed this package")
    file = open(config['package_all_config_file'], "r+")
    
    for pack in file:
        #print(f'pack:{pack}  f_without_dbgsym:{f_without_dbgsym}')
        if f_without_dbgsym in pack:
            if verbose:
                print(f"Skip package >{f_without_dbgsym}<, already in package-all.txt file")
            already_done = True
            break
        
    if verbose and not already_done:
        print(f"Package >{f_without_dbgsym}< not in >{config['package_all_config_file']}< file")
    file.close()

    if not already_done:
        ###we write the package name into package-all.txt to know that we got it already
        file = open(config['package_all_config_file'], "a+")
        if verbose:
            print(f"Write to >{config['package_all_config_file']}< : {f_without_dbgsym}")
        file.write(str(f_without_dbgsym) + '\n')
        file.close()

        ###install the package
        if verbose:
            print(f'Installing >{f_without_dbgsym}< with apt')
        child = pexpect.spawn('sudo DEBIAN_FRONTEND=noninteractive apt install -y {0}'.format(f_without_dbgsym), timeout=None)
        if not gcloud:
            child.expect(':', timeout=None)
            # enter the password
            child.sendline(config['ubuntu_pwd'] + '\n')
        #print(child.read())
        tmp = child.read()

        ###check with dpkg -L what files are installed and if some binaries are there
        dpkg_proc = subprocess.run(['dpkg', '-L', f_without_dbgsym], capture_output=True, universal_newlines=True)
        dpkg_proc_out = dpkg_proc.stdout
        dpkg_proc_out = dpkg_proc_out.split('\n')

        for path in dpkg_proc_out:
            if 'bin' in path:
                #print(f'bin-path:{path}')
                basename = os.path.basename(path)
                #print(f'base-bin-path:{basename}')
                if 'bin' not in basename:
                    #print(f'filtered-basename:{basename}')
                    binaries_in_package.append(path)

        #print(f'dpkg_proc_out: {dpkg_proc_out}')

        ###if we found some binaries in package, we install the -dbgsym package
        if len(binaries_in_package) > 0:
            if verbose:
                print(f'Found binaries in package, install >{package}< with apt now')
            child = pexpect.spawn('sudo DEBIAN_FRONTEND=noninteractive apt install -y {0}'.format(package), timeout=None)
            ### if you run in google cloud, it directly installs the pkg
            if not gcloud:
                child.expect(':', timeout=None)
                ### enter the password
                child.sendline(config['ubuntu_pwd'] + '\n')
            #print(child.read())
            tmp = child.read()

        if verbose:
            print(f'In package >{f_without_dbgsym}< are these binaries: {binaries_in_package}')

        ###check if binaries are binaries or scripts,etc.
        real_binaries_in_package = list()

        for b in binaries_in_package:
            file_proc = subprocess.run(['file', b], capture_output=True, universal_newlines=True)
            file_proc_out = file_proc.stdout
            file_proc_out = file_proc_out.split('\n')
            for line in file_proc_out:
                if ('ELF 64-bit LSB shared object' in line) or ('ELF 64-bit LSB executable' in line):
                    real_binaries_in_package.append(b)

        if verbose:
            print(f'Real binaries:{real_binaries_in_package}')

        ###Write package to package-work.txt, to know that this package got binaries
        if len(real_binaries_in_package) > 0:
            file = open(config['package_work_config_file'], "a+")
            if verbose:
                print(f"Write to >{config['package_work_config_file']}<: {f_without_dbgsym}")
            file.write(str(f_without_dbgsym) + '\n')
            file.close()
        ###Write package to package-dontwork.txt, to know that this package got NO binaries
        else:
            file = open(config['package_dont_work_config_file'], "a+")
            if verbose:
                print(f"Write to >{config['package_dont_work_config_file']}< : {f_without_dbgsym}")
            file.write(str(f_without_dbgsym) + '\n')
            file.close()


        ###check if we already got these binaries in our package-binaries.txt
        #new_binaries_in_package = list()
        found_bin = False

        if len(real_binaries_in_package) > 0:
            file = open(config['package_binaries_config_file'], "r+")
            #check if binary is still in the file, if not ,put it into new list  
            for b in real_binaries_in_package:
                #print(f'b:{b}')
                for stored_bin in file:
                    #print(f's:{stored_bin}')
                    if b in stored_bin:
                        #print("found it in file")
                        found_bin = True
                        break
                    else:
                        pass

                if not found_bin:
                    new_binaries_in_package.append(b)
                else:
                    found_bin = False

            file.close()

            if len(new_binaries_in_package) > 0:
                file = open(config['package_binaries_config_file'], "a+")
                if verbose:
                    print(f"Write to >{config['package_binaries_config_file']}< : {new_binaries_in_package}")
                    
                for b in new_binaries_in_package:
                    file.write(str(b) + '\n')
                file.close()
            else:
                if verbose:
                    print(f"No binaries to write to >{config['package_binaries_config_file']}<")
                pass


    return new_binaries_in_package
    
    
def get_function_signatures_and_ret_types(binaryName, verbose=False):
    funcs_and_ret_types = list()
    all_funcs = list()
    ret_types = set()
    baseFileName = ''

    if verbose:
        print(f'Get function-signatures and return-types with "gdb info functions" from >{binaryName}<')
    gdb_output = subprocess.run(["gdb",  "-batch", "-ex", "file {}".format(binaryName), "-ex", "info functions"], capture_output=True, universal_newlines=True)

    out = gdb_output.stdout
    out_list = out.split('\n')

    for line in out_list:
        linesplit = line.split()
        #print(f'linesplit: {linesplit}')
        if linesplit:
            # Get filename, where the following functions are inside
            if line.split()[0] == 'File':
                filename = line.split()[1]
                #print(f'filename {filename}')
                baseFileName = os.path.basename(filename)
                if baseFileName[-1] == ':':
                    baseFileName = baseFileName[:-1]
                #print(f'filename-filter: {baseFileName}')

            # Get function signature
            if line.split()[0][0].isnumeric():
                #found func name
                funcSignature = line.split()[1:]
                funcSignature = ' '.join(funcSignature)
                #print(f'funcname: {funcname}')

                #Get the return type from the function signature
                if '(' in funcSignature:
                    idx = funcSignature.index('(')
                    #print(idx)
                    new_idx = idx
                    for c in funcSignature[idx-1::-1]:
                        #print(c)
                        new_idx -= 1
                        #if found_ret_type == False:
                        if c == '*' or c == ' ':
                            found_ret_type = True
                            ret_type = funcSignature[:new_idx+1]
                            ret_types.add(ret_type)
                            funcName = funcSignature[new_idx+1:idx]
                            #print(f'funcName: {funcName}')
                            
                            if funcSignature and ret_type and funcName and baseFileName:
                                funcs_and_ret_types.append((funcSignature, ret_type, funcName, baseFileName))
                            #print(funcs_and_ret_types[0])
                            #if 'enum' in ret_type:
                                #print(f'ret_type: {ret_type}')
                            break

                        else:
                            #print(f"scan till funcname end, now at: {c}")
                            pass


    return funcs_and_ret_types
 
 
def proc_get_types_from_names(ret_type, binary_name):
    verbose = False
        
                   
    ###ask gdb for type
    #type: ['type', '=', 'int', '(*)(int,', 'int)']
    #type: ['type', '=', 'int', '(*)(WORD_LIST', '*)']  
    gdb_output_ptype = subprocess.run(["gdb",  "-batch", "-ex", "file {0}".format(binary_name), "-ex", "ptype {0}".format(ret_type)], capture_output=True, universal_newlines=True)
    out_ptype = gdb_output_ptype.stdout
    if verbose:
        print(f'gdb_ptype: {out_ptype}', flush=True)
            
            
    return out_ptype.strip()
    
    
def get_types_from_names(funcs_and_ret_types, binary_name, verbose=False):
    funcs_and_ret_types_filtered = list()
    proc_ret_type_list = list()

    # does not find **  ?????
    #legal_types = ['void', 'void *', '**' 'unsigned', 'char', 'static', '_Bool', 'int', 'wchar_t',
    #               'ssize_t', 'unsigned', 'struct', 'long', 'enum']

    ##, 'static enum char_class '
    legal_types = ['static unsigned char *', 'static char *', 'char **', 'struct', 'static _Bool ', 
                   'static int ', 'static char **', 
                   'long', 'static struct *', 'const char **', 'long ', 'void', 
                   'unsigned char *', 'void *', 'void ', 'int *', 'char ','char *', 
                   'static void ', '_Bool ', 'unsigned int ', 'int', 'int ', 'unsigned long']

    counter = -1
    replace_str = ''

    if verbose:
        print(f'Binary_name:{binary_name}')
        print(f'len(funcs_and_ret_types):{len(funcs_and_ret_types)}')
        
        
    if len(funcs_and_ret_types) < 1:
        print(f'len funcs_and_ret_types: {len(funcs_and_ret_types)}')
        return funcs_and_ret_types_filtered
    
    p = Pool(nr_of_cpus)
    for a, ret_type, funcName, baseFileName in funcs_and_ret_types:
        proc_ret_type_list.append((ret_type, binary_name))
        
    all_ret_types = p.starmap(proc_get_types_from_names, proc_ret_type_list)
    p.close()
    p.join()    
        
    c = 0
    if all_ret_types:
        for func, ret_type, funcName, baseFileName in funcs_and_ret_types:
            if func and funcName and baseFileName and all_ret_types[c]:
                if "DELETE" in all_ret_types[c]:
                    if verbose:
                        print("Delete return type")
                    pass
                else:
                    funcs_and_ret_types_filtered.append((func, all_ret_types[c], funcName, baseFileName ))
            c += 1      
      
            
    return funcs_and_ret_types_filtered    
        
            
        
        
def proc_disas(funcName, baseFileName, binary_name):
    verbose = False 
    gdb_output_disas = subprocess.run(["gdb",  "-batch", "-ex", "file {0}".format(binary_name), "-ex", "disassemble {0}".format(funcName)], capture_output=True, universal_newlines=True)
    out = gdb_output_disas.stdout
    out_list = out.split('\n')
    out_split = list()
    disas_list = []

    for out_list_item in out_list:
        if 'Dump of assembler code' in out_list_item:
            if verbose:
                print('Start of assembler code')
            pass
        elif '\t' in out_list_item:
            if verbose:
                print(f'out_list_item: {out_list_item}')
            out_split = out_list_item.split('\t')
            if verbose:
                print(f'out_split[1]: {out_split[1]}')
                
            out_split_val = out_split[1]
            ###remove comments
            if '<' in out_split_val:
                out_split_idx = out_split_val.index('<')
                out_split_val = out_split_val[:out_split_idx]
            if '#' in out_split_val:   
                out_split_idx = out_split_val.index('#')
                out_split_val = out_split_val[:out_split_idx]

            ###remove trailing whitespace which could result from above 'remove comments'
            out_split_val = out_split_val.rstrip()

            ###make space between these signs to better split
            out_split_val = out_split_val.replace(',', ' , ')
            out_split_val = out_split_val.replace('(', ' ( ')
            out_split_val = out_split_val.replace(')', ' ) ')
            out_split_val = out_split_val.replace(':', ' : ')

            ###replace all numbers with 0x or -0x...
            v = list()
            for val in out_split_val.split():
                if '0x' in val:
                    if val[0] == '$':
                        if val[1] == '-':
                            v.append('$-0x')
                        else:
                            v.append('$0x')
                    elif val[0] == '-':
                        v.append('-0x')
                    else:
                        v.append('0x')
                else:
                    v.append(val)
            out_split_val = ' '.join(v)

            if verbose:
                print(f'One assembly line after filtering:{out_split_val}')
            if out_split_val:
                disas_list.append(out_split_val)

        else:
            if verbose:
                print(f"Mostly empty line or end of assembly or SOMETHING WRONG:{out_list_item}")
            pass        
        
     
    return disas_list 
        
            
            
def get_disassemble(funcs_and_ret_types_filtered, binary_name, verbose=False):
    dataset = list()
    disas_list = list()
    proc_disas_list = list()

    if len(funcs_and_ret_types_filtered) < 1:
        print(f'len funcs_and_ret_types_filtered: {len(funcs_and_ret_types_filtered)}')
        return dataset
    
    p = Pool(nr_of_cpus)
    for a,b,funcName, baseFileName in funcs_and_ret_types_filtered:
        proc_disas_list.append((funcName, baseFileName, binary_name))
        
    all_disas = p.starmap(proc_disas, proc_disas_list)
    p.close()
    p.join()
    
    #for disas in all_disas:
    c = 0
    if all_disas:
        for a,b,funcName, baseFileName in funcs_and_ret_types_filtered:
            if a and b and funcName and baseFileName and all_disas[c]:
                dataset.append((a,b,funcName, baseFileName, all_disas[c]))
            c += 1    
            
 
    if verbose:
        print(f'One dataset item: dataset[0]: {next(iter(dataset))}')
        
    return dataset      


### get at&t or intel disas from funcName
def proc_disas_raw(funcName, binary_name, disas_flavor, verbose=False):
    disas_list = []
    
    gdb_output_disas = subprocess.run(["gdb",  
                                       "-batch",
                                       "-ex",
                                       "set disassembly-flavor {0}".format(disas_flavor),
                                       "-ex", 
                                       "file {0}".format(binary_name), 
                                       "-ex", 
                                       "disassemble {0}".format(funcName)],
                                        capture_output=True, 
                                        universal_newlines=True)
    
    out = gdb_output_disas.stdout
    
    out_list = out.split('\n')
    
    

    for out_list_item in out_list:
        if 'Dump of assembler code' in out_list_item:
            if verbose:
                print('Start of assembler code')
            pass
        elif 'End of assembler dump' in out_list_item:
            if verbose:
                print('End asm code')
            break
        elif '\t' in out_list_item:
            if verbose:
                print(f'One assembly line:{out_list_item}')
            if out_list_item:
                disas_list.append(out_list_item.lstrip())
        else:
            if verbose:
                print(f"Mostly empty line or SOMETHING WRONG:{out_list_item}")
            pass        
        
    #print(f'disaslist:{disas_list}')
    disas_str = ' '.join(disas_list)
    return disas_str
    #return disas_list 


        
  
def get_disassemble_att(funcs_and_ret_types_filtered, binary_name, verbose=False):
    dataset = list()
    disas_list = list()
    proc_disas_list = list()

    if len(funcs_and_ret_types_filtered) < 1:
        print(f'len funcs_and_ret_types_filtered: {len(funcs_and_ret_types_filtered)}')
        return dataset
    
    p = Pool(nr_of_cpus)
    for a,b,funcName, baseFileName in funcs_and_ret_types_filtered:
        proc_disas_list.append((funcName, binary_name, "att", False))
        
    all_disas = p.starmap(proc_disas_raw, proc_disas_list)
    p.close()
    p.join()
    
    return all_disas
  
  
def get_disassemble_intel(funcs_and_ret_types_filtered, binary_name, verbose=False):
    dataset = list()
    disas_list = list()
    proc_disas_list = list()

    if len(funcs_and_ret_types_filtered) < 1:
        print(f'len funcs_and_ret_types_filtered: {len(funcs_and_ret_types_filtered)}')
        return []
    
    p = Pool(nr_of_cpus)
    for a,b,funcName, baseFileName in funcs_and_ret_types_filtered:
        proc_disas_list.append((funcName, binary_name, "intel", False))
        
    all_disas = p.starmap(proc_disas_raw, proc_disas_list)
    p.close()
    p.join()
    
    return all_disas
    
    #for disas in all_disas:
    #c = 0
    #if all_disas:
    #   for a,b,funcName, baseFileName in funcs_and_ret_types_filtered:
    #        if a and b and funcName and baseFileName and all_disas[c]:
    #            dataset.append((a,b,funcName, baseFileName, all_disas[c]))
    #        c += 1    
     
    #if c != len(funcs_and_ret_types_filtered):
    #    print("Not so many disassemblies as funcs ????")      
 
    #if verbose:
    #    print(f'One dataset item: dataset[0]: {next(iter(dataset))}')
        
    #return dataset 

  
def build_tf_dataset(ds_list):
    counter = 0
    tf_dataset = ''
    
    if len(ds_list) > 0:
        for ds in ds_list:
            if counter == 0:
                tf_dataset = tf.data.Dataset.from_tensors([ds[0], ds[1]])
                counter = 1
            if counter > 0:
                tf_dataset = tf_dataset.concatenate(tf.data.Dataset.from_tensors([ds[0], ds[1]]))

        #tf_dataset = tf.data.Dataset.from_tensor_slices(ds_list)

        for elem in tf_dataset:
            print(f'dataset element:{elem}')
            break
        
def _bytes_feature(value):
    """Returns a bytes_list from a string / byte."""
    #if isinstance(value, type(tf.constant(0))):
        #value = value.numpy() # BytesList won't unpack a string from an EagerTensor.
    #value = np.fromiter(value, dtype=int)

    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


    return tf_dataset
      
def serialize_example(feature0, feature1, feature2, feature3, feature4, feature5, feature6, feature7):
    """
    Creates a tf.train.Example message ready to be written to a file.
    """
    # Create a dictionary mapping the feature name to the tf.train.Example-compatible
    # data type.
    feature0 = feature0.numpy()
    feature1 = feature1.numpy()
    feature2 = feature2.numpy()
    feature3 = feature3.numpy()
    feature4 = feature4.numpy()
    feature5 = feature5.numpy()
    feature6 = feature6.numpy()
    feature7 = feature7.numpy()
 
    feature = {
      'func-signature': tf.train.Feature(bytes_list=tf.train.BytesList(value=[feature0])),
      'func-return-type': tf.train.Feature(bytes_list=tf.train.BytesList(value=[feature1])),
      'func-name': tf.train.Feature(bytes_list=tf.train.BytesList(value=[feature2])),
      'func-file-name': tf.train.Feature(bytes_list=tf.train.BytesList(value=[feature3])),
      'func-att-disas': tf.train.Feature(bytes_list=tf.train.BytesList(value=[feature4])),
      'func-intel-disas': tf.train.Feature(bytes_list=tf.train.BytesList(value=[feature5])),
      'ubuntu-package-name': tf.train.Feature(bytes_list=tf.train.BytesList(value=[feature6])),
      'ubuntu-package-binary': tf.train.Feature(bytes_list=tf.train.BytesList(value=[feature7])),
    }

    # Create a Features message using tf.train.Example.

    example_proto = tf.train.Example(features=tf.train.Features(feature=feature))
    return example_proto.SerializeToString()    
   
   
def tf_serialize_example(f0,f1, f2, f3, f4, f5, f6, f7):
    tf_string = tf.py_function(
      serialize_example,
      (f0,f1,f2,f3,f4,f5,f6,f7),  # pass these args to the above function.
      tf.string)      # the return type is `tf.string`.
    return tf.reshape(tf_string, ()) # The result is a scalar  
   
    
def save_list_to_tfrecord(ds_list, file):
    item0_list = list()
    item1_list = list()
    item2_list = list()
    item3_list = list()
    item4_list = list()
    item5_list = list()
    item6_list = list()
    item7_list = list()
    
    
    if len(ds_list) > 0:
        for item in ds_list:
            #print(f'ds_list_item:{item}')
            #print(f'ds_list_item[0]:{item[0]}')
            if not isinstance(item[0], str):
                print(f'type 0 >{type(item[0])}<')
            if not isinstance(item[1], str):
                print(f'type 1 >{type(item[1])}<')
            if not isinstance(item[2], str):
                print(f'type 2 >{type(item[2])}<')
            if not isinstance(item[3], str):
                print(f'type 3 >{type(item[3])}<')
            if not isinstance(item[4], str):
                print(f'type 4 >{type(item[4])}<')
            if not isinstance(item[5], str):
                print(f'type 5 >{type(item[5])}<')
            if not isinstance(item[6], str):
                print(f'type 6 >{type(item[6])}<')
            if not isinstance(item[7], str):
                print(f'type 7 >{type(item[7])}<')
            item0_list.append(item[0])
            item1_list.append(item[1])
            item2_list.append(item[2])
            item3_list.append(item[3])
            item4_list.append(item[4])
            item5_list.append(item[5])
            item6_list.append(item[6])
            item7_list.append(item[7])
            
    tfrecord_dataset = tf.data.Dataset.from_tensor_slices( (item0_list, 
                                                       item1_list,  
                                                       item2_list, 
                                                       item3_list, 
                                                       item4_list, 
                                                       item5_list, 
                                                       item6_list,
                                                       item7_list) )

    serialized_features_dataset = tfrecord_dataset.map(tf_serialize_example)
    
    
    #filename = tf_record_dir + file.replace('.pickle','') + '.tfrecord'
    writer = tf.data.experimental.TFRecordWriter(file)
    writer.write(serialized_features_dataset)



def save_list_to_pickle(ds_list, package_name):
    with open(base_path + pickles_dir + "{0}.pickle".format(package_name), 'wb') as f:
        pickle.dump(ds_list, f)
        
    ###tar and zip for github, dont allow larger than 100MB files
    tar_out = subprocess.run(["tar", 
                              "cjf", 
                              base_path + pickles_dir + package_name + ".pickle" + ".tar.bz2",
                              "-C",
                              base_path + pickles_dir,
                              package_name + ".pickle" , 
                              "--remove-files"], 
                              capture_output=True, 
                              universal_newlines=True)
    out = tar_out.stdout
    print(f'tar_out:{out}') 
    
    

   
def push_pickle_to_github(package_name):
    
    git_out = subprocess.run(["git", "add", "."], capture_output=True, universal_newlines=True)
    out = git_out.stdout
    #print(f'out1: {out}')
    
    git_out = subprocess.run(["git", "commit", "-m", package_name], capture_output=True, universal_newlines=True)
    out = git_out.stdout
    #print(f'out2: {out}')
    
    if '/' in git_pwd:
        git_pwd = git_pwd.replace('/', '%2F')
    
    url = "https://" + config['git_user'] + ":" + config['git_pwd'] + "@github.com/flobotics/func_sign_prob.git"
    git_out = subprocess.run(["git", "push", url, "--all"], capture_output=True, universal_newlines=True)
    out = git_out.stdout
    #print(f'out3: {out}')
    
  
def check_config(config): 
    if config['ubuntu_pwd'] == '':
        print(f'Forgot ubuntu password as argument, try -h for help')
        exit()
        
    if os.path.isdir(config['work_dir']):
        print(f'Found work-dir >{config["work_dir"]}<')
    else:
        print(f'Create work-dir >{config["work_dir"]}<')
        os.mkdir(config['work_dir'])
        
    if os.path.isdir(config['tfrecord_save_dir']):
        print(f'Found tfrecord_save_dir >{config["tfrecord_save_dir"]}<')
    else:
        print(f'Create tfrecord_save_dir >{config["tfrecord_save_dir"]}<')
        os.mkdir(config['tfrecord_save_dir'])
        
    if os.path.isdir(config['config_dir']):
        print(f'Found config_dir >{config["config_dir"]}<')
    else:
        print(f'Create config_dir >{config["config_dir"]}<')
        os.mkdir(config['config_dir'])
        
    if os.path.isfile(config['filtered_out_config_file']):
        print(f"Found filtered_out_config_file >{config['filtered_out_config_file']}<")
    else:
        print(f"Create filtered_out_config_file >{config['filtered_out_config_file']}<")
        open(config['filtered_out_config_file'], 'a').close()
        
    if os.path.isfile(config['package_all_config_file']):
        print(f"Found package_all_config_file >{config['package_all_config_file']}<")
    else:
        print(f"Create package_all_config_file >{config['package_all_config_file']}<")
        open(config['package_all_config_file'], 'a').close()
        
    if os.path.isfile(config['package_work_config_file']):
        print(f"Found package_work_config_file >{config['package_work_config_file']}<")
    else:
        print(f"Create package_work_config_file >{config['package_work_config_file']}<")
        open(config['package_work_config_file'], 'a').close()
        
    if os.path.isfile(config['package_dont_work_config_file']):
        print(f"Found package_dont_work_config_file >{config['package_dont_work_config_file']}<")
    else:
        print(f"Create package_dont_work_config_file >{config['package_dont_work_config_file']}<")
        open(config['package_dont_work_config_file'], 'a').close()
        
    if os.path.isfile(config['package_binaries_config_file']):
        print(f"Found package_binaries_config_file >{config['package_binaries_config_file']}<")
    else:
        print(f"Create package_binaries_config_file >{config['package_binaries_config_file']}<")
        open(config['package_binaries_config_file'], 'a').close()
     

    
def main():  
    config = parseArgs()
            
    check_config(config)
    
    ###get all packages with -dbgsym at the end
    pkgs_with_dbgsym = get_all_ubuntu_dbgsym_packages(config['verbose'])
    
    ###filter out some packages, e.g. which start with firmware
    filtered_pkgs_with_dbgsym = filter_dbgsym_package_list(pkgs_with_dbgsym, config, config['verbose'])
    
    
    
    c = 0
    
    #filtered_pkgs_with_dbgsym = ["tree-dbgsym"]
    
    disassembly_att = list()
    disassembly_intel = list()
    ds_list = list()
    
    ###we loop through all packages with -dbgsym at the end
    for package in filtered_pkgs_with_dbgsym:
        c += 1
        print(f'Package-nr:{c} of {len(filtered_pkgs_with_dbgsym)}, Name:{package}')
        
        ###get all binaries that are inside this package (without -dbgsym)
        all_binaries_in_package = get_binaries_in_package(package, config, True)
        #if c == 2:
            #sys.exit(0)
            
            
        ds_list.clear()
    
        for binary_name in all_binaries_in_package:
    
            #print(f'Get function signature and return type from binary: {binary_name}')
            func_sign_and_ret_types = get_function_signatures_and_ret_types(binary_name)
            #print(f'func_sign_and_ret_types: {func_sign_and_ret_types}')
            
            if not func_sign_and_ret_types:
                #print("NO func_sign_and_ret_types")
                break
            
            #print(f'Get return-types from names we dont know')
            extended_func_and_ret_types = get_types_from_names(func_sign_and_ret_types, binary_name, False)
            #print(f'extended_func_and_ret_types: {extended_func_and_ret_types}')
    
            if not extended_func_and_ret_types:
                #print("NO extended_func_and_ret_types")
                break
    
            #print(f'Get disassembly')
            ##disassemble_out = get_disassemble(extended_func_and_ret_types, binary_name)
            disassembly_att.clear()
            disassembly_att = get_disassemble_att(extended_func_and_ret_types, binary_name)
            
            disassembly_intel.clear()
            disassembly_intel = get_disassemble_intel(extended_func_and_ret_types, binary_name)
            
            if disassembly_att and disassembly_intel:
                ###save everything to a list to store it later
                if len(disassembly_att) != len(disassembly_intel):
                    print(f'Number of att and intel disassembly is different')
                elif len(disassembly_att) != len(extended_func_and_ret_types):
                    print(f'Number of att and functions is different')
                else:
                    disas_len = len(disassembly_att)
                    i = 0
                    while i < disas_len:
                         ds_list.append((extended_func_and_ret_types[i][0], 
                                         extended_func_and_ret_types[i][1], 
                                         extended_func_and_ret_types[i][2], 
                                         extended_func_and_ret_types[i][3], 
                                         disassembly_att[i],
                                         disassembly_intel[i], 
                                         package.replace('-dbgsym', ''), 
                                         binary_name))
                         i += 1
                
                
                
            else:
                 print(f'NO disassembly_att or disassembly intel')          
                 pass
    
    
        if len(ds_list) > 0:
            print(f'Write pickle file')
            #save_list_to_pickle(ds_list, package.replace('-dbgsym', ''))
            
            #push_pickle_to_github(package.replace('-dbgsym', ''))
        
            #package_dataset = build_tf_dataset(ds_list)
    
            save_list_to_tfrecord(ds_list, config['tfrecord_save_dir'] + package.replace('-dbgsym', '.tfrecord'))       
         
        exit()   
        
 
 
if __name__ == "__main__":
    main()   
