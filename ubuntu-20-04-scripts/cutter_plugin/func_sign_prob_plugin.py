import cutter

from PySide2.QtCore import QObject, SIGNAL
from PySide2.QtWidgets import QAction, QLabel

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
        #disasm1 = cutter.cmd("pd").strip()
        
        offset = cutter.cmd("s").strip()
        self._label.setText("current offset:\n{}".format(offset))
        
        disasm = cutter.cmd("pdf @ " + offset).strip()
        
        
        
        #instruction = cutter.cmdj("pdj 1")
        #size = instruction[0]["size"]
# 
        self._label.setText("disassembly:\n{}".format(disasm))
#         
#         self._label.setText("disassembly1:\n{}".format(disasm1))


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