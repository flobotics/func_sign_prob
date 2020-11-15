import cutter

from PySide2.QtCore import QObject, SIGNAL
from PySide2.QtWidgets import QAction, QLabel
from dis import dis

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
        
        offset = cutter.cmd("s").strip()
        #self._label.setText("current offset:\n{}".format(offset))
        
        ###get disas of currently selected function
        disasm_callee = cutter.cmd("pdf @ " + offset).strip()
        
        ###get XREFS, then get disas of XREFs
        xrefs_addr_list = list()
        xrefs_list = list()
        
        for elem in disasm_callee.split('\n'):
            #print(f'elem >{elem}<')
            if 'CALL XREF' in elem:
                xrefs_list.append(elem)
                for word in elem.split():
                    print(f'word >{word}<')
                    if '0x' in word:
                        xrefs_addr_list.append(word)
                
        #self._label.setText("xrefs_addr_list:{}\n xrefs_list:{}".format(xrefs_addr_list, xrefs_list))
        
        ### get disas of caller function
        ##if there are more call-xrefs ?
        for a in xrefs_addr_list:
            addr = a
        disasm_caller = cutter.cmd("pdf @ " + addr).strip()
        
        self._label.setText("xrefs_addr_list:{}\n xrefs_list:{}\n disasm_caller:{}".format(xrefs_addr_list, xrefs_list, disasm_caller))
        


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