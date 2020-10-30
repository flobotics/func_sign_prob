from numpy.core.defchararray import isnumeric
def find_call_in_disassembly_line(disassembly_line):
    if 'call' in disassembly_line:
        if '@plt' in disassembly_line:
            return False
        if 'std::' in disassembly_line:
            return False
    
        return True
    
    else:
        return False
    

def get_callee_name_from_disassembly_line(disassembly_line):
    callee_name = ''
    disassembly_line_split = disassembly_line.split()
    callee_name = disassembly_line_split[len(disassembly_line_split)-1]
    callee_name = callee_name.replace('<', '')
    callee_name = callee_name.replace('>', '')
    
    return callee_name


def check_for_hex_string(item):
    new_item = ''
    #print(f'item--> >{item}<')
    
    if len(item) >= 2:
        ## check for 0x  -0x
        if (item[0] == '0' and item[1] == 'x') or (item[0] == '-' and item[1] == '0' and item[2] == 'x'):
            item_len = len(item)
            counter = 0
            while(item_len):
                if item[counter] == '0':
                    item_str = 'null'
                else:
                    item_str = item[counter]
                    
                if item_len == 1:
                    new_item = new_item + item_str
                else:
                    new_item = new_item + item_str + ' '
                item_len -= 1
                counter += 1
            #print(f'new-item >{new_item}<')
            return new_item
        else:
            return 'process_further'
    else:
        return 'process_further'
    

def check_for_numbers(item):
    if not isnumeric(item[0]):
        return 'process_further'
    
    ## check if every single char is numeric
    for char in item:
        if not isnumeric(char):
            print(f'found char not number-----------')
            
    item_len = len(item)
    counter = 0
    new_item = ''
    while(item_len):
        if item[counter] == '0':
            item_str = 'null'
        else:
            item_str = item[counter]
                    
        if item_len == 1:
            new_item = new_item + item_str
        else:
            new_item = new_item + item_str + ' '
        item_len -= 1
        counter += 1
    
    return new_item
    
def split_disassembly(dis):
    new_line = list()
    
    for line in dis.split('\t'):
        #print(f'One line-----------')
        #print(f'line: >{line}<')
        
        line = line.replace('(', ' ( ')
        line = line.replace(')', ' ) ')
        line = line.replace('%', ' % ')
        line = line.replace(',', ' , ')
        line = line.replace('$', ' $ ')
        line = line.replace('*', ' * ')
        line = line.replace('<', ' < ')
        line = line.replace('>', ' > ')
        line = line.replace('+', ' + ')
        line = line.replace('@', ' @ ')
        line = line.replace(':', ' : ')
        #print(f'line after giving space: >{line}<')
    
        #new_item = ''
        for item in line.split():
            
            ret = check_for_hex_string(item)
            if not ret == 'process_further':
                new_line.append(ret)
                continue
            
            ret = check_for_numbers(item)
            if not ret == 'process_further':
                new_line.append(ret)
                continue
            
            new_line.append(item)
            
    new_str = ' '.join(new_line)
    #print(f'New-line >{new_str}<')
    
    return new_str
    
    

    