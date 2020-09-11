import subprocess
import os
#import tensorflow as tf
#from tensorflow import keras
#from tensorflow.keras.preprocessing.text import Tokenizer
import pexpect
import numpy as np
import pickle
import getopt
import sys
from multiprocessing import Pool

base_path = "/home/infloflo/git/func_sign_prob/"
#base_path = "/home/ubu/git/test/func_sign_prob/"
config_dir = "ubuntu-20-04-config/"
pickles_dir = "ubuntu-20-04-pickles/"
gcloud = True 


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
        
    return pack_dbgsym_list



def filter_dbgsym_package_list(dbgsym_list, verbose=False):
    new_list = list()
    
    for item in dbgsym_list:
        subItem = item.split()[0]
        
        
        if subItem.startswith('lib') or subItem.startswith('firmware'):
            if verbose:
                print(f'Filter out, because of >lib,firmware< {subItem}')
            pass
        elif 'plugin' in subItem:
            if verbose:
                print(f'Filter out, because of >plugin< {subItem}')
            pass
        else:
            if verbose:
                print(f'Add to filtered list >{subItem}<')
            new_list.append(subItem)
    
    if verbose:
        print(f'Length of filtered_pkgs_with_dbgsym:{len(new_list)}')
    
    return new_list



        
def get_binaries_in_package(package, verbose=False):
    new_binaries_in_package = list()
    package_work = list()
    c = 0
    already_done = False
    binaries_in_package = list()

    f_without_dbgsym = package.replace('-dbgsym', '')
    already_done = False

    #check if we got this package already 
    file = open(base_path + config_dir + "package-all.txt", "r+")
    for pack in file:
        if f_without_dbgsym in pack:
            if verbose:
                print(f"Skip package >{f_without_dbgsym}<, already in package-all.txt file")
            already_done = True
            break
        
    if verbose and not already_done:
        print(f"Package >{f_without_dbgsym}< not in package-all.txt file")
    file.close()

    if not already_done:
        ###we write the package name into package-all.txt to know that we got it already
        file = open(base_path + config_dir + "package-all.txt", "a+")
        if verbose:
            print(f"Write to package-all.txt file: {f_without_dbgsym}")
        file.write(str(f_without_dbgsym) + '\n')
        file.close()

        ###install the package
        child = pexpect.spawn('sudo DEBIAN_FRONTEND=noninteractive apt install -y {0}'.format(f_without_dbgsym), timeout=None)
        if not gcloud:
            child.expect('ubu:', timeout=None)
            # enter the password
            child.sendline('ubu\n')
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
            child = pexpect.spawn('sudo DEBIAN_FRONTEND=noninteractive apt install -y {0}'.format(package), timeout=None)
            ### if you run in google cloud, it directly installs the pkg
            if not gcloud:
                child.expect('ubu:', timeout=None)
                ### enter the password
                child.sendline('ubu\n')
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
            file = open(base_path + config_dir + "package-work.txt", "a+")
            if verbose:
                print(f"Write to package-work.txt file: {f_without_dbgsym}")
            file.write(str(f_without_dbgsym) + '\n')
            file.close()
        ###Write package to package-dontwork.txt, to know that this package got NO binaries
        else:
            file = open(base_path + config_dir + "package-dontwork.txt", "a+")
            if verbose:
                print(f"Write to package-dontwork.txt file: {f_without_dbgsym}")
            file.write(str(f_without_dbgsym) + '\n')
            file.close()


        ###check if we already got these binaries in our package-binaries.txt
        #new_binaries_in_package = list()
        found_bin = False

        if len(real_binaries_in_package) > 0:
            file = open(base_path + config_dir + "package-binaries.txt", "r+")
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
                file = open(base_path + config_dir + "package-binaries.txt", "a+")
                if verbose:
                    print(f"Write to package-binaries.txt file: {new_binaries_in_package}")
                    
                for b in new_binaries_in_package:
                    file.write(str(b) + '\n')
                file.close()
            else:
                if verbose:
                    print("No binaries to write to package-binaries.txt file")
                pass


    return new_binaries_in_package
    
    
def get_function_signatures_and_ret_types(binaryName, verbose=False):
    funcs_and_ret_types = list()
    all_funcs = list()
    ret_types = set()
    baseFileName = ''

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
    replace_str = ''
    
    legal_types = ['static unsigned char *', 'static char *', 'char **', 'struct', 'static _Bool ', 
                   'static int ', 'static char **', 
                   'long', 'static struct *', 'const char **', 'long ', 'void', 
                   'unsigned char *', 'void *', 'void ', 'int *', 'char ','char *', 
                   'static void ', '_Bool ', 'unsigned int ', 'int', 'int ', 'unsigned long']
    
    for ret_type_split in ret_type.split():
        if ret_type in legal_types:
            if verbose:
                print(f'Found legal return type:{ret_type}')
            break
        else:
            #not legal type, look with gdb ptype what type it is, and replace it
            if verbose:
                print(f'Not found in legal types:{ret_type}')
                
            ###ask gdb for type
            #type: ['type', '=', 'int', '(*)(int,', 'int)']
            #type: ['type', '=', 'int', '(*)(WORD_LIST', '*)']  
            gdb_output_ptype = subprocess.run(["gdb",  "-batch", "-ex", "file {0}".format(binary_name), "-ex", "ptype {0}".format(ret_type)], capture_output=True, universal_newlines=True)
            out_ptype = gdb_output_ptype.stdout
            if verbose:
                print(f'gdb_ptype: {out_ptype}', flush=True)

            notFound = True
            type = out_ptype.split()
            if len(type) == 3:
                if type[2] == 'long':
                    if verbose:
                        print("found long")
                    replace_str = 'long'
                    notFound = False
                elif type[2] == 'int':
                    if verbose:
                        print("found int")
                    replace_str = 'int'
                    notFound = False
                elif type[2] == 'void':
                    if verbose:
                        print("found void")
                    replace_str = 'void'
                    notFound = False

            if len(type) == 4:
                if type[2] == 'unsigned' and type[3] == 'long':
                    if verbose:
                        print("found unsigned long")
                    replace_str = 'unsigned long'
                    notFound = False
                elif type[2] == 'void' and type[3] == '*':
                    if verbose:
                        print("found void *")
                    replace_str = 'void *'
                    notFound = False
                elif type[2] == 'const' and type[3] == 'char':
                    if verbose:
                        print("found const char")
                    replace_str = 'const char'
                    notFound = False
                elif type[2] == 'int' and type[3] == '*':
                    if verbose:
                        print("found int *")
                    replace_str = 'int *'
                    notFound = False

            if len(type) == 5:
                if type[2] == 'const' and type[3] == 'char' and type[4] == '**':
                    if verbose:
                        print("found const char **")
                    replace_str = 'const char **'
                    notFound = False

            if notFound and len(type) >= 3:
                if type[2] == 'struct':
                    if verbose:
                        print("found struct")
                    replace_str = 'struct'
                    notFound = False
                    
            if notFound:
                replace_str = 'DELETE'
                break
            else:
                break
            
    return replace_str
    
    
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
    
    p = Pool(4)
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
    
    p = Pool(4)
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
      
def serialize_example(feature0, feature1, feature2, feature3, feature4, feature5, feature6):
    """
    Creates a tf.train.Example message ready to be written to a file.
    """
    # Create a dictionary mapping the feature name to the tf.train.Example-compatible
    # data type.
    feature = {
      'func-signature': _bytes_feature(feature0),
      'func-return-type': _bytes_feature(feature1),
      'func-name': _bytes_feature(feature2),
      'func-file-name': _bytes_feature(feature3),
      'func-intel-disas': _bytes_feature(feature4),
      'ubuntu-package-name': _bytes_feature(feature5),
      'ubuntu-package-binary': _bytes_feature(feature6),
    }

    # Create a Features message using tf.train.Example.

    example_proto = tf.train.Example(features=tf.train.Features(feature=feature))
    return example_proto.SerializeToString()    
    
def save_list_to_tfrecord(ds_list, package):
    if len(ds_list) > 0:
        for item in ds_list:
            print(f'ds_list_item:{item}')
            print(f'ds_list_item[0]:{item[0]}')
            serialized_example = serialize_example(item[0].encode('utf-8'),
                                                   item[1].encode('utf-8'),
                                                   item[2].encode('utf-8'),
                                                   item[3].encode('utf-8'),
                                                   item[4].encode('utf-8'),
                                                   item[5].encode('utf-8'),
                                                   item[6].encode('utf-8'))
            break

        example_proto = tf.train.Example.FromString(serialized_example)
        example_proto
        
        
        
        #filename = package + '.tfrecord'
        #print(f'tfrecord-filename:{filename}')
        #writer = tf.data.experimental.TFRecordWriter(filename)
        #writer.write(serialized_features_dataset)


def save_list_to_pickle(ds_list, package_name):
    with open(base_path + pickles_dir + "{0}.pickle".format(package_name), 'wb') as f:
        pickle.dump(ds_list, f)    

   
def push_pickle_to_github(package_name):
    global git_user
    global git_pwd
    
    git_out = subprocess.run(["git", "add", "."], capture_output=True, universal_newlines=True)
    out = git_out.stdout
    #print(f'out1: {out}')
    
    git_out = subprocess.run(["git", "commit", "-m", package_name], capture_output=True, universal_newlines=True)
    out = git_out.stdout
    #print(f'out2: {out}')
    
    if '/' in git_pwd:
        git_pwd = git_pwd.replace('/', '%2F')
    
    url = "https://" + git_user + ":" + git_pwd + "@github.com/flobotics/func_sign_prob.git"
    git_out = subprocess.run(["git", "push", url, "--all"], capture_output=True, universal_newlines=True)
    out = git_out.stdout
    #print(f'out3: {out}')
    
        
    
        
        
git_user = ''
git_pwd = ''
        
opts, args = getopt.getopt(sys.argv[1:], "ho:v", ["help", "git-user=", "git-pwd="])

for o, a in opts:
    if o == "--git-user":
        git_user = a
    elif o == '--git-pwd':
        git_pwd = a
        
if git_user == '' or git_pwd == '':
    print("You forgot git credentials")
    exit()
else:
    print(f"git-user:{git_user}  git-pwd:{git_pwd}")

###get all packages with -dbgsym at the end
pkgs_with_dbgsym = get_all_ubuntu_dbgsym_packages(False)

###filter out some packages, e.g. which start with firmware
filtered_pkgs_with_dbgsym = filter_dbgsym_package_list(pkgs_with_dbgsym, False)



c = 0

###we loop through all packages with -dbgsym at the end
for package in filtered_pkgs_with_dbgsym:
    c += 1
    print(f'Package-nr:{c} of {len(filtered_pkgs_with_dbgsym)}, Name:{package}')
    
    ###get all binaries that are inside this package (without -dbgsym)
    all_binaries_in_package = get_binaries_in_package(package, False)  
    print(all_binaries_in_package)
    #if c == 2:
        #sys.exit(0)
        
        
    ds_list = list()

    for b in all_binaries_in_package:

        print(f'Get function signature and return type from binary: {b}')
        func_sign_and_ret_types = get_function_signatures_and_ret_types(b)
        #print(f'func_sign_and_ret_types: {func_sign_and_ret_types}')
        
        if not func_sign_and_ret_types:
            print("NO func_sign_and_ret_types")
            break
        
        print(f'Get return-types from names we dont know')
        extended_func_and_ret_types = get_types_from_names(func_sign_and_ret_types, b, False)
        #print(f'extended_func_and_ret_types: {extended_func_and_ret_types}')

        if not extended_func_and_ret_types:
            print("NO extended_func_and_ret_types")
            break

        print(f'Get disassembly')
        disassemble_out = get_disassemble(extended_func_and_ret_types, b)
        
        if disassemble_out:
            ###save everything to a list to store it later
            for funcSign, returnType, funcName, funcFileName, disassembly_list in disassemble_out:
                if funcSign and returnType and funcName and funcFileName and disassembly_list:
                    ds_list.append((funcSign, returnType, funcName, funcFileName, disassembly_list, package.replace('-dbgsym', ''), b))
        else:
             print(f'NO disassemble_out')           

    if len(ds_list) > 0:
        print(f'Write pickle file')
        save_list_to_pickle(ds_list, package.replace('-dbgsym', ''))
        
        push_pickle_to_github(package.replace('-dbgsym', ''))
    
        #package_dataset = build_tf_dataset(ds_list)

        #save_list_to_tfrecord(ds_list, package.replace('-dbgsym', ''))       
        
    

