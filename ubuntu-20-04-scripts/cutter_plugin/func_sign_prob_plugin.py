import cutter
import subprocess

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

    def update_contents(self):
        
        ### setup stuff to get gdb-style disassembly
        cutter.cmd("e asm.syntax=att")
        asm_syntax = cutter.cmd("e asm.syntax")
        cutter.cmd("e asm.arch=x86")
        asm_arch = cutter.cmd("e asm.arch")
        cutter.cmd("e asm.xrefs=false")
        asm_xrefs = cutter.cmd("e asm.xrefs")
        cutter.cmd("e asm.bytes=false")
        asm_bytes = cutter.cmd("e asm.bytes")
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
        
        ### get actual loaded bin-filename
        ### cmdj('ij').get('Core').get('file')   or something like that
        
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
        
        modified_disasm_caller = list()
        
        for line in disasm_callee.split('\n'):
            #print(f'line >{line}<')
            for word in line.split():
                if word.strip().startswith('fcn.'):
                    print(f'word starts with fcn.')
                    ##fcn.00001289+0x4  to  0x0000000000001289 <+0x4>:
                    if not word.contains('+'):  ##first line
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
                else:
                    print(f'Nothing found >{word}<')
                    modified_disasm_caller.append(word)       
         
        disasm_callee = ' '.join(modified_disasm_caller)               
        
        self._disasTextEdit.setPlainText("disasm_caller:\n{}\ndisasm_callee:\n{}".format(disasm_caller, disasm_callee))
        
        #self._label.setText("disasm_caller:\n{}\ndisasm_callee:\n{}".format(disasm_caller, disasm_callee))
        #self._label.setText("disasm before")
        
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
        
        
        
        
        #out_list = out.split('\n')
        
        file = open("/tmp/cutter-disas.txt", 'w+')
        file.write("gdb-info-func-------------\n")
        #file.write(''.join(gdb_result))
        file.write("asm_syntax----------------\n")
        file.write(asm_syntax)
        
        file.write("asm_arch------------------\n")
        file.write(asm_arch)
        
        file.write("asm_xrefs-----------------\n")
        file.write(asm_xrefs)
        
        file.write("asm_bytes-----------------\n")
        file.write(asm_bytes)
        
        file.write("\ndisasm_caller-----------\n")
        file.write(disasm_caller)
        
        file.write("\ndisasm_callee-----------\n")
        file.write(disasm_callee)
        file.close()
        
       


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