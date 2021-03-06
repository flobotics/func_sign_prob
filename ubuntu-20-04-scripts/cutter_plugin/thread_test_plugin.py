import cutter
import time

from PySide2.QtCore import QObject, Signal, Slot, QThread
from PySide2.QtWidgets import QAction, QLabel

##this one freeze cutter
class oldthreadClass(QObject):
    resultReady = Signal()
    
    def __init__(self):
        super().__init__()
        #QObject.__init__(self)
    
    @Slot()
    def runSomethingInThread(self):
        ## you see print only on console if you start cutter from console
        print('send from threadd')
        
        ### next line freeze cutter, not everytime for the first time,
        ### sometimes it runs 2,3 times ,then freezes
        curr_pos = cutter.cmd('s')
        
        time.sleep(5)
        curr_pos = cutter.cmd('s')
    
        print('send from thread after time')
        self.resultReady.emit()
        
        
class threadClass(QThread):
    resultReady = Signal()
    
    def __init__(self):
        super().__init__()
    
    def run(self):
        ## you see print only on console if you start cutter from console
        print('send from thread')
        
        ### next line freeze cutter, not everytime for the first time,
        ### sometimes it runs 2,3 times ,then freezes
        curr_pos = cutter.cmd('s')
        
        time.sleep(1)
        curr_pos = cutter.cmd('s')
    
        print('send from thread after time')
        
        self.resultReady.emit()
        

class MyDockWidget(cutter.CutterDockWidget):
    startRunSomethingInThreadSignal = Signal()
    
    def __init__(self, parent, action):
        super(MyDockWidget, self).__init__(parent, action)
        self.setObjectName("MyDockWidget")
        self.setWindowTitle("My cool DockWidget")

        self._label = QLabel(self)
        self.setWidget(self._label)

        cutter.core().seekChanged.connect(self.update_contents)

        ##this will freeze cutter gui
#         self.threadClass = threadClass()
#         self.runSomethingInThreadThread = QThread()
#         self.runSomethingInThreadThread.start()
#         self.threadClass.moveToThread(self.runSomethingInThreadThread)
#          
#         self.threadClass.resultReady.connect(self.showResultFromThread)
#         self.startRunSomethingInThreadSignal.connect(self.threadClass.runSomethingInThread)

        self.threadClass = threadClass()
        self.threadClass.resultReady.connect(self.showResultFromThread)
        
        
    @Slot()
    def showResultFromThread(self):
        print(f'showResult')
        self._label.setText("showResult") 
            

    def update_contents(self):

        #self.startRunSomethingInThreadSignal.emit()
        
        self.threadClass.start()
        
        
#         disasm = cutter.cmd("pd 1").strip()
# 
#         instruction = cutter.cmdj("pdj 1")
#         size = instruction[0]["size"]
# 
#         self._label.setText("Current disassembly:\n{}\nwith size {}".format(disasm, size))


class MyCutterPlugin(cutter.CutterPlugin):
    name = "My Plugin"
    description = "This plugin does awesome things!"
    version = "1.0"
    author = "1337 h4x0r"

    def setupPlugin(self):
        pass

    def setupInterface(self, main):
        action = QAction("My Plugin", main)
        action.setCheckable(True)
        widget = MyDockWidget(main, action)
        main.addPluginDockWidget(widget, action)

    def terminate(self):
        pass

def create_cutter_plugin():
    return MyCutterPlugin()