import cutter
import subprocess
import re

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
        cutter.cmd("e scr.color=0")
        cutter.cmd("e asm.noisy=false")
        cutter.cmd("e asm.xrefs=false")   ##part in head-part
        cutter.cmd("e asm.functions=false")   ##part in head-part
        
        
        
        
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
        
        ## get disas of caller function
        disasm_caller = cutter.cmd("pdf @ " + str(callee_addr))
        print(disasm_caller)
        
        ## get sym functions and its address
        aflj_output = cutter.cmdj("aflj")
        for elem in aflj_output:
            for key in elem:
                if key == 'signature':
                    print(f"item >{key}<  sign >{elem[key]}<  addr >{elem['offset']}<")
        
        
        modified_disasm_caller = list()
        
        ## find loc. and replace
        new_str = ''
        #for char in disasm_callee:
        #new_char = re.sub(u'\u001b\[.*?[@-~]', '', disasm_callee)
        #new_str = new_str + str(char)
        
        #disasm_callee = new_char
        
        for line in disasm_callee.split('\n'):
            #print(f'line >{line}<')
            #line = re.sub(u'\u001b\[.*?[@-~]', '', line)
            #line = str(line)
            for word in line.split():
                #word = word1.encode('ascii', errors='ignore').decode()
                if word.startswith('fcn.'):  ##remove color codes, radare2 e scr.color=0 removes stuff
                    print(f'word >{word}< starts with fcn.')
                    ##fcn.00001289+0x4  to  0x0000000000001289 <+0x4>:
                    if not '+' in word:  ##first line
                        print(f'word NOT contains +, think its first line')
                        idx1 = word.index('.')
                        addr = word[idx1+1:]
                        l = len(addr)
                        addr = '0x' + '0'*(16-l) + addr
                        modified_disasm_caller.append(addr + ' <+0>:')
                    else:  ### other lines
                        print(f'word seemed not to contain +, think its other lines')
                        idx1 = word.index('.')
                        idx2 = word.index('+')
                        addr = word[idx1+1:idx2]
                        off = word[idx2:]
                        modified_disasm_caller.append('0x' + addr + ' <' + off + '>:')
                elif word.startswith('main'):
                    print(f'word >{word}< starts with main')
                    if '+0x' in word:
                        print(f'word contains +0x')
                        idx1 = word.index('+')
                        off = word[idx1+1:]
                        ###main must be replaced with an address ??
                        #get addr of main()
                        main_addr = cutter.cmd('afi main~offset')
                        print(f'main offset/addr >{main_addr}<')
                        main_addr = '0x00000000' + main_addr[2:]
                        print(f'main offset/addr modified >{main_addr}<')
                        modified_disasm_caller.append('0x' + main_addr + ' <' + off + '>:')
                    else:
                        print(f'word main is first line, or?')
                        main_addr = cutter.cmd('afi main~offset')
                        print(f'main offset/addr >{main_addr}<')
                        main_addr = '0x00000000' + main_addr[2:]
                        print(f'main offset/addr modified >{main_addr}<')
                        modified_disasm_caller.append(main_addr + ' <+0>:')
                elif 'sym' in word:
                    print(f'word >{word}< got sym in it, replace with addr')
                    found = False
                    for elem in aflj_output:
                        #print(f"elem-sig >{elem['signature']}<")
                        sign = elem['signature']
                        #print(f'sign >{sign}<')
                        if '(' in sign:
                            idx = sign.index('(')
                            sign = sign[:idx]
                            sign = sign.strip()
                            
                        if 'sym.' in sign:
                            idx = sign.index('sym.')
                            sign = sign[idx:]
                            
                            
                            if sign == word:
                                #print(f"found sign >{sign}<  addr >{elem['offset']}<")
                                
                                ## translate int-addr to hex without leading zeros only e.g. 0x7 not 0x07
                                hex_addr = int(elem['offset'])
                                hex_addr = hex(hex_addr)
                                #print(f"hex-addr >{hex_addr}<")
                                modified_disasm_caller.append(hex_addr)
                                found = True
                    if found == False:
                        print(f"no signature found >{word}<")
                        
                    
                elif 'loc.' in word:
                    print(f'word >{word}< got loc. in it, replace with addr')
                    
                else:
                    print(f'Nothing found >{word}<')
                    modified_disasm_caller.append(word)
                    
            modified_disasm_caller.append('\n')       
         
        disasm_callee = ' '.join(modified_disasm_caller)               
        
        self._disasTextEdit.setPlainText("disasm_caller:\n{}\ndisasm_callee:\n{}".format(disasm_caller, disasm_callee))
        
        #self._label.setText("disasm_caller:\n{}\ndisasm_callee:\n{}".format(disasm_caller, disasm_callee))
        #self._label.setText("disasm before")
        
        
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