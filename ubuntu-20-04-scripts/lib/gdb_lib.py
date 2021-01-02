import os


def install_source_package(src_package, config):
    print(f"We install with apt-source >{src_package}< into >{config['ubuntu_src_pkgs']}{src_package}<")
    
    try:
        os.mkdir(config['ubuntu_src_pkgs'] + src_package)
    except OSError:
        print (f"Creation of the directory {config['ubuntu_src_pkgs']}{src_package} failed")
    else:
        print (f"Successfully created the directory {config['ubuntu_src_pkgs']}{src_package}")
    
        os.chdir(config['ubuntu_src_pkgs'] + src_package)

        ###install the package
        #child = pexpect.spawn('apt source -y {0}'.format(src_package), timeout=None)
        #if not gcloud:
        #    child.expect('ubu:', timeout=None)
            # enter the password
       #    child.sendline('ubu\n')
        #print(child.read())
        #tmp = child.read()
        
        out = subprocess.run(["apt", 
                          "source",
                          src_package],
                          capture_output=True, 
                          universal_newlines=True)
        gdb_out = out.stdout
        