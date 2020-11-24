import cutter
import subprocess
import re
#import tensorflow as tf
import sys

from PySide2.QtCore import QObject, SIGNAL, QProcess
from PySide2.QtWidgets import QAction, QLabel, QPlainTextEdit

#from dis import dis

class MyDockWidget(cutter.CutterDockWidget):
    def __init__(self, parent, action):
        super(MyDockWidget, self).__init__(parent, action)
        self.setObjectName("func_sign_probDockWidget")
        self.setWindowTitle("func_sign_prob DockWidget")

        #self._label = QLabel(self)
        self._disasTextEdit = QPlainTextEdit(self)
        #self.setWidget(self._label)
        self.setWidget(self._disasTextEdit)

        QObject.connect(cutter.core(), SIGNAL("seekChanged(RVA)"), self.update_contents)
        self.update_contents()
        

    def set_new_radare2_e(self):
        ##store values we modify
        self.asm_syntax = cutter.cmd("e asm.syntax")
        self.asm_arch = cutter.cmd("e asm.arch")
        self.asm_xrefs = cutter.cmd("e asm.xrefs")
        self.asm_bytes = cutter.cmd("e asm.bytes")
        self.asm_demangle = cutter.cmd("e asm.demangle")
        self.asm_var_sub = cutter.cmd("e asm.var.sub")
        self.asm_var = cutter.cmd("e asm.var")
        self.asm_sub_rel = cutter.cmd("e asm.sub.rel")
        self.asm_calls = cutter.cmd("e asm.calls")
        self.asm_comments = cutter.cmd("e asm.comments")
        self.asm_reloff = cutter.cmd("e asm.reloff")
        self.scr_color = cutter.cmd("e scr.color")
        self.asm_noisy = cutter.cmd("e asm.noisy")
        self.asm_functions = cutter.cmd("e asm.functions")
        self.asm_sub_section = cutter.cmd("e asm.sub.section")
        self.asm_filter = cutter.cmd("e asm.filter") ## replace numeric with sym.
        self.asm_lines = cutter.cmd("e asm.lines")
        self.asm_meta = cutter.cmd("e asm.meta")
        
        ### setup stuff to get gdb-style disassembly
        cutter.cmd("e asm.syntax=att")
        cutter.cmd("e asm.arch=x86")
        cutter.cmd("e asm.bytes=false")
        cutter.cmd("e asm.demangle=false")
        cutter.cmd("e asm.var.sub=false")
        cutter.cmd("e asm.var=false")     ##vars in head-part
        cutter.cmd("e asm.sub.rel=false")
        cutter.cmd("e asm.calls=false")
        cutter.cmd("e asm.comments=false")
        cutter.cmd("e asm.reloff=true")
        cutter.cmd("e scr.color=3")
        cutter.cmd("e asm.noisy=false")
        cutter.cmd("e asm.xrefs=false")   ##part in head-part
        cutter.cmd("e asm.functions=false")   ##part in head-part
        cutter.cmd("e asm.sub.section=false")
        cutter.cmd("e asm.filter=false") ## replace numeric with sym.
        cutter.cmd("e asm.lines=false")
        cutter.cmd("e asm.meta=false")
        #cutter.cmd("e asm.tabs=false") and other tabs
        
        
        
        
    def set_stored_radare2_e(self):
        cutter.cmd("e asm.syntax=" + self.asm_syntax)
        cutter.cmd("e asm.arch=" + self.asm_arch)
        cutter.cmd("e asm.bytes=" + self.asm_bytes)
        cutter.cmd("e asm.demangle=" + self.asm_demangle)
        cutter.cmd("e asm.var.sub=" + self.asm_var_sub)
        cutter.cmd("e asm.var=" + self.asm_var)     ##vars in head-part
        cutter.cmd("e asm.sub.rel=" + self.asm_sub_rel)
        cutter.cmd("e asm.calls=" + self.asm_calls)
        cutter.cmd("e asm.comments=" + self.asm_comments)
        cutter.cmd("e asm.reloff=" + self.asm_reloff)
        cutter.cmd("e scr.color=" + self.scr_color)
        cutter.cmd("e asm.noisy=" + self.asm_noisy)
        cutter.cmd("e asm.xrefs=" + self.asm_xrefs)   ##part in head-part
        cutter.cmd("e asm.functions=" + self.asm_functions)   ##part in head-part
        cutter.cmd("e asm.sub.section=" + self.asm_sub_section)
        cutter.cmd("e asm.filter=" + self.asm_filter) ## replace numeric with sym.
        cutter.cmd("e asm.lines=" + self.asm_lines)
        cutter.cmd("e asm.meta=" + self.asm_meta)
        
        
    
    def todo_placeholder(self):
        pass
        #         ### get disas from gdb
#         gdb_process = QProcess()
#         
#         binn = '/tmp/testapp'
#         bin = "file " + binn
#         
#         gdb_process.start("/usr/bin/gdb",
#                             ['-batch',  '-ex', bin, '-ex', 'info functions'])
#         
#         gdb_process.waitForFinished()
#         gdb_result = gdb_process.readAll()
#         
#         gdb_info_functions = str(gdb_result, 'utf-8')
#         
#         self._label.setText("disasm after {}".format(gdb_info_functions))
        
        ##search if function is available
        #seek = cutter.cmd('s')
     
    def modify_aflj_output(self, aflj_output):
        aflj_dict = dict()
        
        for elem in aflj_output:
            sign = elem['signature']
            
            if '(' in sign:
                idx = sign.index('(')
                sign = sign[:idx]
                sign = sign.strip()
            else:
                print(f'Error modify')
                 
            if ' ' in sign:
                idx = sign[::-1].index(' ')
                sign = sign[len(sign)-idx:]
                
                if sign[0] == '*':
                    sign = sign[1:]
                    
                if sign[0] == '*':
                    sign = sign[1:]
                 
                #print(f'sign >{sign}<')
             
            int_addr = int(elem['offset'])
            hex_addr = hex(int_addr)
                 
            aflj_dict[sign] = hex_addr

        print(f'modified aflj_dict >{aflj_dict}<')
                                        
        return aflj_dict    
             
             
    def modify_first_part_of_r2_disas_line(self, word, aflj_dict):
        
        ## fcn.00001289      --> fcn.00001289+0x4  to  0x0000000000001289 <+0x4>:
        ## main              --> main+0x4
        ## entry.init1       --> entry.init1+0x4  -->got dot,but no addr
        
        ### this is for the first line only
        if not '+' in word:  ##first line got no offset
            if '.' in word and word.startswith('fcn.'):  ##got e.g. fcn.00001289
                idx1 = word.index('.')
                addr = word[idx1+1:]
                addr_int = int(addr, 16)
                return f"{addr_int:#0{18}x}" + ' <+0>:'
                
            else:  ## got e.g. main
                found = False
                for key in aflj_dict:
                    if key == word:
                        addr = aflj_dict[key]
                        addr_int = int(addr, 16)
                        return f"{addr_int:#0{18}x}" + ' <+0x0>:'
                     
                if found == False:
                    print(f"no signature, no addr found-1 >{word}<")
                
        ### this is for all following lines, after line one
        else:
            #print(f'word seemed to contain +, think its not first lines')
            if '.' in word and word.startswith('fcn.'):  ##got e.g. fcn.00001289+0x4
                idx1 = word.index('.')
                idx2 = word.index('+')
                addr = word[idx1+1:idx2]
                off = word[idx2:]
                addr2 = int(addr, 16) + int(off, 16)
                return f"{addr2:#0{18}x}" + ' <+' + str(int(off, 0)) + '>:'
                
            else:   ### e.g. main+0x1d
                idx2 = word.index('+')
                stripped_word = word[:idx2]
                found = False
                for key in aflj_dict:
                    if key == stripped_word:
                        addr = aflj_dict[key]
                        addr_int = int(addr, 16)
                        idx2 = word.index('+')
                        off = word[idx2:]
                        addr2 = int(addr, 16) + int(off, 16)
                        return f"{addr2:#0{18}x}" + ' <+' + str(int(off, 0)) + '>:'
                     
                if found == False:
                    print(f"no signature, no addr found-2 >{word}<")
                

                     
        
    def modify_radare2_disassembly(self, disassembly, aflj_dict):
        modified_disassembly = list()
        
        ## modify radare2 disassembly to be like gdb disassembly
        for line in disassembly.split('\n'):
            #print(f'line >{line}<')
            is_first_word = True
            
            for word in line.split():
                #word = word1.encode('ascii', errors='ignore').decode()
                
                if is_first_word:
                    ### hack, radare2 pdf output prints sometimes some lines at the beginning,delete
                    if 'section..text' == line.strip():
                        continue
                    if 'rip' == line.strip():
                        continue
        
                    ret = self.modify_first_part_of_r2_disas_line(word, aflj_dict)
                    modified_disassembly.append(ret)
                
#                 if word.startswith('fcn.') and is_first_word:
#                     print(f'word >{word}< starts with fcn.')
#                     ret = self.modify_first_part_of_r2_disas_line(word, aflj_dict)
#                     modified_disassembly.append(ret)
#                  
#                 elif word.startswith('main') and is_first_word:
#                     print(f'word >{word}< starts with main')
#                     ret = self.modify_first_part_of_r2_disas_line(word, aflj_dict)
#                     modified_disassembly.append(ret)
# 
#                 elif word.startswith('entry0') and is_first_word:
#                     #print(f'found entry0')
#                     ret = self.modify_first_part_of_r2_disas_line(word, aflj_dict)
#                     modified_disassembly.append(ret)
                    
                elif word.startswith('fcn.') and not is_first_word:
                    ##fcn.00001289    the fcn. in the disas, not at start-of-line
                    modified_disassembly.append(word.replace('fcn.', '0x'))
                    
                elif 'sym.' in word:
                    #print(f'word >{word}< got sym in it, replace with addr')
                    found = False
                    for key in aflj_dict:
                        if key == word:
                            modified_disassembly.append(aflj_dict[key])
                            found = True
                            
                    if found == False:
                        print(f"no signature found >{word}<")
                        
                    
                elif 'loc.' in word:
                    print(f'word >{word}< got loc. in it, replace with addr')
                    ## loc.00001376
                    modified_disassembly.append(word.replace('loc.', '0x'))
                    
                else:
                    #print(f'Nothing found >{word}<')
                    modified_disassembly.append(word)
                    
                is_first_word = False
                    
            modified_disassembly.append('\n')       
         
        modified_disassembly_str = ' '.join(modified_disassembly)
        
        return modified_disassembly_str
        
        
    def trim_terminal_color_codes(self, a):
        ESC = r'\x1b'
        CSI = ESC + r'\['
        OSC = ESC + r'\]'
        CMD = '[@-~]'
        ST = ESC + r'\\'
        BEL = r'\x07'
        pattern = '(' + CSI + '.*?' + CMD + '|' + OSC + '.*?' + '(' + ST + '|' + BEL + ')' + ')'
        return re.sub(pattern, '', a)
    
        
    def update_contents(self):
        ### get actual loaded bin-filename
        ### cmdj('ij').get('Core').get('file')   or something like that
        
        self.set_new_radare2_e()
        
        ## find data/code references to this address with $F
        current_func_header = cutter.cmdj("axtj $F")
        
        ## get addr of callee
        callee_addr = 0
        for item_dicts in current_func_header:
            #print(f'item_dicts >{item_dicts}<')
            for elem in item_dicts:
                if elem == 'from':
                    callee_addr = item_dicts[elem]
                    print(f'address of callee >{item_dicts[elem]}<')
                
        
        ## get disassembly of current function
        disasm_callee = cutter.cmd("pdf @ $F").strip()
        print(disasm_callee)
        disasm_callee = self.trim_terminal_color_codes(disasm_callee)
        
        ## get disas of caller function
        disasm_caller = cutter.cmd("pdf @ " + str(callee_addr))
        print(disasm_caller)
        disasm_caller = self.trim_terminal_color_codes(disasm_caller)
        
        ## get sym. functions and its addresses
        aflj_output = cutter.cmdj("aflj")
        aflj_dict = self.modify_aflj_output(aflj_output)
        
        ## make r2 disas to be like gdb disas
        modified_disasm_caller = self.modify_radare2_disassembly(disasm_caller, aflj_dict)
        modified_disasm_callee = self.modify_radare2_disassembly(disasm_callee, aflj_dict)
                      
        
        self._disasTextEdit.setPlainText("disasm_caller:\n{}\ndisasm_callee:\n{}".format(modified_disasm_caller, modified_disasm_callee))
        
        #self._label.setText("disasm_caller:\n{}\ndisasm_callee:\n{}".format(disasm_caller, disasm_callee))
        #self._label.setText("disasm before")
        
        #self._disasTextEdit.setPlainText(sys.version)  ##3.6.4 ?????
        
        
        file = open("/tmp/cutter-disas.txt", 'w+')
        
        file.write("\ndisasm_caller-----------\n")
        file.write(disasm_caller)
        
        file.write("\ndisasm_callee-----------\n")
        file.write(disasm_callee)
        file.close()
        
        self.set_stored_radare2_e()
        
        
        

class MyCutterPlugin(cutter.CutterPlugin):
    name = "func_sign_prob plugin"
    description = "func_sign_prob plugin"
    version = "0.1"
    author = "flo"

    def setupPlugin(self):
        pass

    def setupInterface(self, main):
        action = QAction("func_sign_prob Plugin", main)
        action.setCheckable(True)
        widget = MyDockWidget(main, action)
        main.addPluginDockWidget(widget, action)

    def terminate(self):
        pass

def create_cutter_plugin():
    return MyCutterPlugin()