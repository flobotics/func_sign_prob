import cutter

from PySide2.QtCore import QObject, SIGNAL
from PySide2.QtWidgets import QAction, QLabel
#from dis import dis

class MyDockWidget(cutter.CutterDockWidget):
    def __init__(self, parent, action):
        super(MyDockWidget, self).__init__(parent, action)
        self.setObjectName("func_sign_probDockWidget")
        self.setWindowTitle("func_sign_prob DockWidget")

        self._label = QLabel(self)
        self.setWidget(self._label)

        QObject.connect(cutter.core(), SIGNAL("seekChanged(RVA)"), self.update_contents)
        self.update_contents()

    def update_contents(self):
        
        ### setup stuff
        cutter.cmd("e asm.syntax=att")
        asm_syntax = cutter.cmd("e asm.syntax")
        cutter.cmd("e asm.arch=x86")
        asm_arch = cutter.cmd("e asm.arch")
        cutter.cmd("e asm.xrefs=false")
        asm_xrefs = cutter.cmd("e asm.xrefs")
        
        
        ## get header of current function with $F
        current_func_header = cutter.cmdj("axtj $F")
        
        ## get addr of callee
        for item_dicts in current_func_header:
            #print(f'item_dicts >{item_dicts}<')
            for elem in item_dicts:
                if elem == 'from':
                    print(f'address of callee >{item_dicts[elem]}<')
                
        
        ## get disassembly of current function
        disasm_callee = cutter.cmd("pdf @ $F").strip()
        print(disasm_callee)
        self._label.setText("disasm_callee:\n{}".format(disasm_callee))
        
        file = open("/tmp/out.txt", 'w+')
        file.write("asm_syntax----------------\n")
        file.write(asm_syntax)
        file.write("asm_arch------------------\n")
        file.write(asm_arch)
        file.write("asm_xrefs-----------------\n")
        file.write(asm_xrefs)
        file.write("\ndisasm_callee-----------\n")
        file.write(disasm_callee)
        
        
        
        
#         offset = cutter.cmd("s").strip()
#         #self._label.setText("current offset:\n{}".format(offset))
#         
#         ###get disas of currently selected function
#         ## e asm.arch=    asm.assembler=  asm.syntax=att
#         ## e? asm
#         disasm_callee = cutter.cmd("pdf @ " + offset).strip()
#         
#         ###get XREFS, then get disas of XREFs
#         xrefs_addr_list = list()
#         xrefs_list = list()
#         
#         ### axtj $F   ## $F current function
#         ### cutter.cmdj("axtj $F")
#         prev_word = ''
#         for line in disasm_callee.split('\n'):
#             #print(f'elem >{elem}<')
#             if 'CALL XREF' in line:
#                 xrefs_list.append(line)
#                 for word in line.split():
#                     print(f'word >{word}<')
#                     if '@' in word:
#                         xrefs_addr_list.append(prev_word)
#                     prev_word = word
#                 
#         #self._label.setText("xrefs_addr_list:{}\n xrefs_list:{}".format(xrefs_addr_list, xrefs_list))
#         
#         ### get disas of caller function
#         ##if there are more call-xrefs ?
#         addr = 0
#         for a in xrefs_addr_list:
#             addr = a
#         if addr != 0:
#             disasm_caller = cutter.cmd("pdf @ " + str(addr)).strip()
#         else:
#             disasm_caller = ''
#         
#         self._label.setText("xrefs_addr_list:{}\n xrefs_list:{}\n disasm_caller:{}\n disas_callee:{}".format(xrefs_addr_list, xrefs_list, disasm_caller, disasm_callee))
#         
#         ## get a gdb-like disas output
#         cutter.cmd("e asm.xrefs=false")
#         disasm_callee = cutter.cmd("pdf @ " + offset).strip()
#         disasm_caller = cutter.cmd("pdf @ " + str(addr)).strip()
#         
#         file = open("/tmp/out.txt", 'w+')
#         file.write("asm_syntax----------------\n")
#         file.write(asm_syntax)
#         file.write("asm_arch------------------\n")
#         file.write(asm_arch)
#         file.write("asm_xrefs-----------------\n")
#         file.write(asm_xrefs)
#         file.write("\nxrefs_addr_list-----------\n")
#         file.write(''.join(xrefs_addr_list))
#         file.write("\nxrefs_list----------------\n")
#         file.write(''.join(xrefs_list))
#         file.write("\ndisasm_caller-------------\n")
#         file.write(''.join(disasm_caller))
#         file.write("\ndisasm_callee-------------\n")
#         file.write(''.join(disasm_callee))
#         file.write("\n--------------------------")
#         file.close()


class MyCutterPlugin(cutter.CutterPlugin):
    name = "func_sign_prob plugin"
    description = "func_sign_prob plugin"
    version = "1.0"
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