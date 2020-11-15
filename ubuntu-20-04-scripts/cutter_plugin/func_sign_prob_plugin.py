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
        self._label.setText("current offset:\n{}".format(offset))
        
        ###get disas of currently selected function
        disasm = cutter.cmd("pdf @ " + offset).strip()
        
        ###get XREFS, then get disas of XREFs
        for elem in disasm.split('\n'):
            if elem in 'XREF':
                self._label.setText("XREF:{}".format(elem))
        
        #self._label.setText("current offset:{}\ndisassembly:{}".format(offset, disasm))


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