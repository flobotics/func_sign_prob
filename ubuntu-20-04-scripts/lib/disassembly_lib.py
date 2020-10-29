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