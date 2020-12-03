import cutter
import subprocess
import re
import os
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.layers.experimental.preprocessing import TextVectorization
from tensorflow.keras.layers import Activation, Dense, Embedding, GlobalAveragePooling1D

from PySide2.QtCore import QObject, SIGNAL, QProcess, QThread, Signal, Slot
from PySide2.QtWidgets import QAction, QLabel, QPlainTextEdit, QWidget, QVBoxLayout

##from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot

import time

#sys.path.append('./')
import disassembly_lib
import pickle_lib


class InferenceClass(QObject):
    resultReady = Signal()
    
        
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

        #print(f'modified aflj_dict >{aflj_dict}<')
                                        
        return aflj_dict    
             
             
    def get_disassembly_of(self, address):
        #disasm_callee = cutter.cmdj("pdrj @ $F")
        disassembly = cutter.cmdj("pdrj @ " + str(address))
        disassembly_str = ''
        offset = ''
        fcn_addr = ''
        opcode = ''
        size = ''
        oldsize = 0
        
        for dis_dict in disassembly:
            for key in dis_dict:
                if key == 'offset':
                    offset = dis_dict['offset']
                elif key == 'fcn_addr':
                    fcn_addr = dis_dict['fcn_addr']
                elif key == 'size':
                    size = dis_dict['size']
                elif key == 'opcode':
                    opcode = dis_dict['opcode']
                elif key == 'disasm':
                    disasm = dis_dict['disasm']
                    
                    
            ## 0x0000000000001394 <+18>:    callq  0x1289 <my_function(int, char)>
            ## 0x00001394      call fcn.00001289
            
            ##{"offset":5012,"esil":"4745,rip,8,rsp,-=,rsp,=[],rip,=","refptr":false,"fcn_addr":4994,
            ##"fcn_last":5019,"size":5,"opcode":"call 0x1289","disasm":"call fcn.00001289","bytes":"e8f0feffff",
            ##"family":"cpu","type":"call","reloc":false,"type_num":3,"type2_num":0,"jump":4745,"fail":5017,
            ##"refs":[{"addr":4745,"type":"CALL"}]}
            
                
            if offset and fcn_addr and opcode and size:
                #disassembly_str = disassembly_str + f"{offset:#0{18}x}" + ' <+' + str(oldsize) + '>: ' + opcode + '\n'
                disassembly_str = disassembly_str + opcode + '\n'
                oldsize += size
            
            offset = ''
            fcn_addr = ''
            opcode = ''
            size = ''
            
        return disassembly_str
    
    
    def predict(self, model_path, vocab_len, max_seq_len, disas):
                            
        model = tf.keras.models.load_model(model_path)

        ##summary_str = str(model.to_json())
        stringlist = []
        model.summary(print_fn=lambda x: stringlist.append(x))
        self.model_summary_str = "\n".join(stringlist)
        
        vectorize_layer = TextVectorization(standardize=None,
                                            max_tokens=vocab_len+2,
                                            output_mode='int',
                                            output_sequence_length=max_seq_len)

        export_model = tf.keras.Sequential([vectorize_layer,
                                          model,
                                          tf.keras.layers.Activation('softmax')
                                        ])
        
        example = [disas]
        ret = export_model.predict(example)
        #print(f"Prediction: >{ret}<")
        #print()  ##just a newline 
        
        return ret
    
    
    def get_prediction_summary(self, ret_type_dict, ret):
        
        reverse_ret_type_dict = dict()
        counter = 0
        for key in ret_type_dict:
            reverse_ret_type_dict[counter] = key
            counter += 1
        
        arg_one_prediction_summary = []
        arg_one_prediction_summary.append('\n')
        
        
        for item in ret:
            result = 0
            biggest = 0
            biggest_count = 0
            counter = 0
            for i in item:
                if i > biggest:
                    biggest = i
                    biggest_count = counter
                
                tmp_str = f'Type >{reverse_ret_type_dict[counter] : <{30}}< has a probability of >{i}<\n'
                #print(tmp_str)
                arg_one_prediction_summary.append(tmp_str)
                counter += 1
                
                result += i
            for ret in ret_type_dict:
                if ret_type_dict[ret] == biggest_count:
                    #print()
                    #print(f'argument one is of type >{ret}<')
                    arg_one_prediction_summary.append(f'\nBiggest Probability type >{ret}< with prob >{biggest}<\n\n')
                    
                    self.biggest_prob = biggest
                    self.biggest_prob_type = ret
                    
        arg_one_prediction_summary.append(f'Does last count together to 1 ? Result: >{result}<')

        arg_one_prediction_summary_str = ''.join(arg_one_prediction_summary)
        
        return arg_one_prediction_summary_str
    
    
    
    def get_prediction(self, model, disasm_caller_callee_str, func_sign_prob_git_path):
        ### predict now    
        model_path = func_sign_prob_git_path + \
                            "ubuntu-20-04-scripts/trained_models/" + model + "/saved_model/"
                            
        ###load vocabulary list
        vocab_file = func_sign_prob_git_path + \
                            "ubuntu-20-04-scripts/trained_models/" + model + "/" + \
                            'vocabulary_list.pickle'
        
                                                    
        vocabulary = pickle_lib.get_pickle_file_content(vocab_file)
        
        ###load max-sequence-length
        max_seq_len_file = func_sign_prob_git_path + \
                            "ubuntu-20-04-scripts/trained_models/" + model + "/" + \
                            'max_seq_length.pickle'
                            
        max_seq_length = pickle_lib.get_pickle_file_content(max_seq_len_file)
        
        ret = self.predict(model_path, len(vocabulary), max_seq_length, disasm_caller_callee_str)
        
        ## get strings for ints, with ret_type_dict
        ret_type_dict_file = func_sign_prob_git_path + \
                                    "ubuntu-20-04-scripts/trained_models/" + model + "/" + \
                                    'return_type_dict.pickle'
                            
        ret_type_dict = pickle_lib.get_pickle_file_content(ret_type_dict_file)
        
        ### get human-readable output
        prediction_summary_str = self.get_prediction_summary(ret_type_dict, ret)
       
        ## store for later
#         nr_of_args_model_summary_str = self.model_summary_str
#         self._disasTextEdit.setPlainText(f"tf model summary:\n{self.model_summary_str}\n \
#                                         {nr_of_args_model_summary_str}")
       
        return prediction_summary_str   
        
        
    @Slot()
    def oldrunInference(self):
        print('runInference---test')
  
    @Slot()
    def runInference(self):
        print('runInference')
        curr_pos = cutter.cmd('s')
        if curr_pos.strip() == '0x0':
            print('runInference not from addr 0x0')
            return
         
        print('runInference 2')
        self.set_new_radare2_e()
        print('runInference 3')
        
        ### get name of current function
        current_func_name = cutter.cmdj("afdj $F").get('name')
         
        print(f'current_func_name >{current_func_name}<')
        
        self.resultReady.emit()
        return
    
        ## find data/code references to this address with $F
        current_func_header = cutter.cmdj("axtj $F")
         
        ## get addr of callee
        caller_addr = 0
        for item_dicts in current_func_header:
            #print(f'item_dicts >{item_dicts}<')
            for elem in item_dicts:
                if elem == 'from':
                    caller_addr = item_dicts[elem]
                    #print(f'address of caller >{item_dicts[elem]}<')
                 
         
        ## get disassembly of current/callee function
        address = cutter.cmd('s').strip()
        print(f'address >{address}<')
        if address == '0x0':
            print(f'address kicked >{address}<')
            return
        
        disasm_callee_str = self.get_disassembly_of(address)
         
        print(f'disasm_callee_str >{disasm_callee_str}<')
     
        ### get disassembly of caller function
        #print(f'caller-addr >{str(caller_addr)}<')
        disasm_caller_str = self.get_disassembly_of(caller_addr)
         
        print(f'disasm_caller_str >{disasm_caller_str}<')
         
        #return
  
        ### split disas for the tf-model     
        disasm_caller_str = disassembly_lib.split_disassembly(disasm_caller_str)
        print('runInference 4')
        disasm_callee_str = disassembly_lib.split_disassembly(disasm_callee_str)
        print('runInference 5')
         
        
        
        #self._disasTextEdit.setPlainText("disasm_caller_callee:\n{}".format(disasm_caller_str + disasm_callee_str))
         
        ##check if we got caller and callee disassembly
        if (len(disasm_caller_str) == 0) or (len(disasm_callee_str) == 0):
            print(f'Not found callee and caller disassembly.')
            return
         
        ### the path were we cloned git repo to
        self._userHomePath = os.path.expanduser('~')
        print(f'userHomePath >{self._userHomePath}<')
        func_sign_prob_git_path = self._userHomePath + "/git/func_sign_prob/"
         
        ### predict now ret-type
#         self._funcSignLabel.setText(f'plugin freeze cutter gui, wait some minutes, or wait longer till threading is implemented.\n \
#                                     Predict return type now.')
        ret_type_prediction_summary_str = self.get_prediction('return_type/words_100000', 
                                                                disasm_caller_str + disasm_callee_str, 
                                                                func_sign_prob_git_path)
        
        print('runInference 5')
           
        ## store for later, will be overridden
        ret_type_model_summary_str = self.model_summary_str
        ret_type_biggest_prob = self.biggest_prob
        ret_type_biggest_prob_type = self.biggest_prob_type
        ret_type_biggest_prob_percent = 100 * ret_type_biggest_prob
                  
         ### predict now nr_of_args
        self._funcSignLabel.setText(f'plugin freeze cutter gui, wait some minutes, or wait longer till threading is implemented.\n \
                                    Predict number of arguments now.')
        nr_of_args_prediction_summary_str = self.get_prediction('nr_of_args', 
                                                                disasm_caller_str + disasm_callee_str, 
                                                                func_sign_prob_git_path)
                   
               
        ## store for later, will be overridden
        nr_of_args_model_summary_str = self.model_summary_str
        nr_of_args_biggest_prob = self.biggest_prob
        nr_of_args_biggest_prob_type = self.biggest_prob_type
           
        ###predict now arg_one
        self._funcSignLabel.setText(f'plugin freeze cutter gui, wait some minutes, or wait longer till threading is implemented.\n \
                                    Predict argument one now.')
        arg_one_prediction_summary_str = self.get_prediction('arg_one', 
                                                                disasm_caller_str + disasm_callee_str, 
                                                                func_sign_prob_git_path)
            
    
        ## store for later, will be overridden
        arg_one_model_summary_str = self.model_summary_str
        arg_one_biggest_prob = self.biggest_prob
        arg_one_biggest_prob_type = self.biggest_prob_type
        arg_one_biggest_prob_percent = 100 * arg_one_biggest_prob
            
        nr_of_args_biggest_prob_type = 1
        if nr_of_args_biggest_prob_type == 1:
              
            self._disasTextEdit.setPlainText(f"tf return type model summary:\n \
                                        {ret_type_model_summary_str}\n \
                                        {ret_type_prediction_summary_str}\n \
                                        tf nr_of_args model summary:\n \
                                         {nr_of_args_model_summary_str}\n \
                                         {nr_of_args_prediction_summary_str}\n \
                                         tf arg_one model summary:\n \
                                         {self.model_summary_str}\n \
                                         {arg_one_prediction_summary_str}")
       
            self._funcSignLabel.setText(f'{ret_type_biggest_prob_type} \
                 <span style=\"background-color:red;\">({ret_type_biggest_prob_percent:3.1f}%)</span> \
                 {current_func_name} ( \
                 {arg_one_biggest_prob_type} \
                 <span style=\"background-color:red;\">({arg_one_biggest_prob_percent:3.1f}%)</span> \
                 )') 
               
            self.set_stored_radare2_e()
            return
               
              
        ###if more one args
        ###predict now arg_two
#         self._funcSignLabel.setText(f'plugin freeze cutter gui, wait some minutes, or wait longer till threading is implemented.\n \
#                                     Predict argument two now.')
        arg_two_prediction_summary_str = self.get_prediction('arg_two', 
                                                                disasm_caller_str + disasm_callee_str, 
                                                                func_sign_prob_git_path)
           
   
        ## store for later, will be overridden
        arg_two_model_summary_str = self.model_summary_str
        arg_two_biggest_prob = self.biggest_prob
        arg_two_biggest_prob_type = self.biggest_prob_type
        arg_two_biggest_prob_percent = 100 * arg_two_biggest_prob
          
        nr_of_args_biggest_prob_type = 2 
        if nr_of_args_biggest_prob_type == 2:
          
            self._disasTextEdit.setPlainText(f"tf return type model summary:\n \
                                        {ret_type_model_summary_str}\n \
                                        {ret_type_prediction_summary_str}\n \
                                        tf nr_of_args model summary:\n \
                                        {nr_of_args_model_summary_str}\n \
                                        {nr_of_args_prediction_summary_str}\n \
                                        tf arg_one model summary:\n \
                                        {arg_one_model_summary_str}\n \
                                        {arg_one_prediction_summary_str}\n \
                                        tf arg_two model summary:\n \
                                        {arg_two_model_summary_str}\n \
                                        {arg_two_prediction_summary_str}")
  
            self._funcSignLabel.setText(f'{ret_type_biggest_prob_type} \
                <span style=\"background-color:red;\">({ret_type_biggest_prob_percent:3.1f}%)</span> \
                {current_func_name} ( \
                {arg_one_biggest_prob_type} \
                <span style=\"background-color:red;\">({arg_one_biggest_prob_percent:3.1f}%)</span> , \
                {arg_two_biggest_prob_type} \
                <span style=\"background-color:red;\">({arg_two_biggest_prob_percent:3.1f}%)</span> \
                )') 
              
            self.set_stored_radare2_e()
            return
         
         
        ###if more than two args
        ###predict now arg_three
        self._funcSignLabel.setText(f'plugin freeze cutter gui, wait some minutes, or wait longer till threading is implemented.\n \
                                    Predict argument three now.')
        arg_three_prediction_summary_str = self.get_prediction('arg_three', 
                                                                disasm_caller_str + disasm_callee_str, 
                                                                func_sign_prob_git_path)
          
  
        ## store for later, will be overridden
        arg_three_model_summary_str = self.model_summary_str
        arg_three_biggest_prob = self.biggest_prob
        arg_three_biggest_prob_type = self.biggest_prob_type
        arg_three_biggest_prob_percent = 100 * arg_three_biggest_prob
         
         
         
        self._disasTextEdit.setPlainText(f"arg_three_model_summary_str >{arg_three_model_summary_str}< >{arg_three_biggest_prob}< >{arg_three_biggest_prob_type}<")
                                             
        ##if nr_of_args_biggest_prob_type == 3:
        if nr_of_args_biggest_prob_type >= 3:   #hack, if more args
              
            self._disasTextEdit.setPlainText(f"tf return type model summary:\n \
                                        {ret_type_model_summary_str}\n \
                                        {ret_type_prediction_summary_str}\n \
                                        tf nr_of_args model summary:\n \
                                        {nr_of_args_model_summary_str}\n \
                                        {nr_of_args_prediction_summary_str}\n \
                                        tf arg_one model summary:\n \
                                        {arg_one_model_summary_str}\n \
                                        {arg_one_prediction_summary_str}\n \
                                        tf arg_two model summary:\n \
                                        {arg_two_model_summary_str}\n \
                                        {arg_two_prediction_summary_str}\n \
                                        tf arg_three model summary:\n \
                                        {arg_three_model_summary_str}\n \
                                        {arg_three_prediction_summary_str}")
 
            self._funcSignLabel.setText(f'{ret_type_biggest_prob_type} \
                <span style=\"background-color:red;\">({ret_type_biggest_prob_percent:3.1f}%)</span> \
                {current_func_name} ( \
                {arg_one_biggest_prob_type} \
                <span style=\"background-color:red;\">({arg_one_biggest_prob_percent:3.1f}%)</span> , \
                {arg_two_biggest_prob_type} \
                <span style=\"background-color:red;\">({arg_two_biggest_prob_percent:3.1f}%)</span> , \
                {arg_three_biggest_prob_type} \
                <span style=\"background-color:red;\">({arg_three_biggest_prob_percent:3.1f}%)</span> \
                )') 
              
            self.set_stored_radare2_e()
            return
         
         
        #for debug
        print('over')
         
        self.set_stored_radare2_e()
#         /* ... here is the expensive or blocking operation ... */
        self.resultReady.emit()




class FuncSignProbDockWidget(cutter.CutterDockWidget):
    inferenceClass = InferenceClass()
    inferenceThread = QThread()
    startInferenceSignal = Signal()
    counter = 0
    
    def __init__(self, parent, action):
        super(FuncSignProbDockWidget, self).__init__(parent, action)
        self.setObjectName("func_sign_probDockWidget")
        self.setWindowTitle("func_sign_prob DockWidget")

        self._multiWidget = QWidget()
        self._layout = QVBoxLayout()
        
        self._funcSignLabel = QLabel(self)
        self._disasTextEdit = QPlainTextEdit(self)
        
        self._layout.addWidget(self._funcSignLabel)
        self._layout.addWidget(self._disasTextEdit)
        
        self._multiWidget.setLayout(self._layout);
        self.setWidget(self._multiWidget);
        
        self._userHomePath = os.path.expanduser('~')
        #print(f'user-home-path >{self._userHomePath}<')

        #QObject.connect(cutter.core(), SIGNAL("seekChanged(RVA)"), self.update_contents)
        cutter.core().seekChanged.connect(self.update_contents)
        #self.update_contents()
        
        self.inferenceClass.moveToThread(self.inferenceThread)
        self.inferenceClass.resultReady.connect(self.showInferenceResult)
        self.startInferenceSignal.connect(self.inferenceClass.runInference)
        self.inferenceThread.start()
        self.counter = 0
        
    @Slot()
    def showInferenceResult(self):
        print(f'showInferenceResult')
        #time.sleep(5)
        #print(f'after 5 seconds')
        self._disasTextEdit.setPlainText("showInferenceResult-func")    
        
    def update_contents(self):
        print('update-contents func')
        if self.counter > 0:
            print('update-contents func >0')
            self.startInferenceSignal.emit()
        else:
            print('update-contents func else')
            self.counter += 1
            
            
#     def set_new_radare2_e(self):
#         ##store values we modify
#         self.asm_syntax = cutter.cmd("e asm.syntax")
#         self.asm_arch = cutter.cmd("e asm.arch")
#         self.asm_xrefs = cutter.cmd("e asm.xrefs")
#         self.asm_bytes = cutter.cmd("e asm.bytes")
#         self.asm_demangle = cutter.cmd("e asm.demangle")
#         self.asm_var_sub = cutter.cmd("e asm.var.sub")
#         self.asm_var = cutter.cmd("e asm.var")
#         self.asm_sub_rel = cutter.cmd("e asm.sub.rel")
#         self.asm_calls = cutter.cmd("e asm.calls")
#         self.asm_comments = cutter.cmd("e asm.comments")
#         self.asm_reloff = cutter.cmd("e asm.reloff")
#         self.scr_color = cutter.cmd("e scr.color")
#         self.asm_noisy = cutter.cmd("e asm.noisy")
#         self.asm_functions = cutter.cmd("e asm.functions")
#         self.asm_sub_section = cutter.cmd("e asm.sub.section")
#         self.asm_filter = cutter.cmd("e asm.filter") ## replace numeric with sym.
#         self.asm_lines = cutter.cmd("e asm.lines")
#         self.asm_meta = cutter.cmd("e asm.meta")
#         
#         ### setup stuff to get gdb-style disassembly
#         cutter.cmd("e asm.syntax=att")
#         cutter.cmd("e asm.arch=x86")
#         cutter.cmd("e asm.bytes=false")
#         cutter.cmd("e asm.demangle=false")
#         cutter.cmd("e asm.var.sub=false")
#         cutter.cmd("e asm.var=false")     ##vars in head-part
#         cutter.cmd("e asm.sub.rel=false")
#         cutter.cmd("e asm.calls=false")
#         cutter.cmd("e asm.comments=false")
#         cutter.cmd("e asm.reloff=true")
#         cutter.cmd("e scr.color=3")
#         cutter.cmd("e asm.noisy=false")
#         cutter.cmd("e asm.xrefs=false")   ##part in head-part
#         cutter.cmd("e asm.functions=false")   ##part in head-part
#         cutter.cmd("e asm.sub.section=false")
#         cutter.cmd("e asm.filter=false") ## replace numeric with sym.
#         cutter.cmd("e asm.lines=false")
#         cutter.cmd("e asm.meta=false")
#         #cutter.cmd("e asm.tabs=false") and other tabs
#         
#         
#         
#         
#     def set_stored_radare2_e(self):
#         cutter.cmd("e asm.syntax=" + self.asm_syntax)
#         cutter.cmd("e asm.arch=" + self.asm_arch)
#         cutter.cmd("e asm.bytes=" + self.asm_bytes)
#         cutter.cmd("e asm.demangle=" + self.asm_demangle)
#         cutter.cmd("e asm.var.sub=" + self.asm_var_sub)
#         cutter.cmd("e asm.var=" + self.asm_var)     ##vars in head-part
#         cutter.cmd("e asm.sub.rel=" + self.asm_sub_rel)
#         cutter.cmd("e asm.calls=" + self.asm_calls)
#         cutter.cmd("e asm.comments=" + self.asm_comments)
#         cutter.cmd("e asm.reloff=" + self.asm_reloff)
#         cutter.cmd("e scr.color=" + self.scr_color)
#         cutter.cmd("e asm.noisy=" + self.asm_noisy)
#         cutter.cmd("e asm.xrefs=" + self.asm_xrefs)   ##part in head-part
#         cutter.cmd("e asm.functions=" + self.asm_functions)   ##part in head-part
#         cutter.cmd("e asm.sub.section=" + self.asm_sub_section)
#         cutter.cmd("e asm.filter=" + self.asm_filter) ## replace numeric with sym.
#         cutter.cmd("e asm.lines=" + self.asm_lines)
#         cutter.cmd("e asm.meta=" + self.asm_meta)
#         
#         
    
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
     
#     def modify_aflj_output(self, aflj_output):
#         aflj_dict = dict()
#         
#         for elem in aflj_output:
#             sign = elem['signature']
#             
#             if '(' in sign:
#                 idx = sign.index('(')
#                 sign = sign[:idx]
#                 sign = sign.strip()
#             else:
#                 print(f'Error modify')
#                  
#             if ' ' in sign:
#                 idx = sign[::-1].index(' ')
#                 sign = sign[len(sign)-idx:]
#                 
#                 if sign[0] == '*':
#                     sign = sign[1:]
#                     
#                 if sign[0] == '*':
#                     sign = sign[1:]
#                  
#                 #print(f'sign >{sign}<')
#              
#             int_addr = int(elem['offset'])
#             hex_addr = hex(int_addr)
#                  
#             aflj_dict[sign] = hex_addr
# 
#         #print(f'modified aflj_dict >{aflj_dict}<')
#                                         
#         return aflj_dict    
#              
#              
#     def get_disassembly_of(self, address):
#         #disasm_callee = cutter.cmdj("pdrj @ $F")
#         disassembly = cutter.cmdj("pdrj @ " + str(address))
#         disassembly_str = ''
#         offset = ''
#         fcn_addr = ''
#         opcode = ''
#         size = ''
#         oldsize = 0
#         
#         for dis_dict in disassembly:
#             for key in dis_dict:
#                 if key == 'offset':
#                     offset = dis_dict['offset']
#                 elif key == 'fcn_addr':
#                     fcn_addr = dis_dict['fcn_addr']
#                 elif key == 'size':
#                     size = dis_dict['size']
#                 elif key == 'opcode':
#                     opcode = dis_dict['opcode']
#                 elif key == 'disasm':
#                     disasm = dis_dict['disasm']
#                     
#                     
#             ## 0x0000000000001394 <+18>:    callq  0x1289 <my_function(int, char)>
#             ## 0x00001394      call fcn.00001289
#             
#             ##{"offset":5012,"esil":"4745,rip,8,rsp,-=,rsp,=[],rip,=","refptr":false,"fcn_addr":4994,
#             ##"fcn_last":5019,"size":5,"opcode":"call 0x1289","disasm":"call fcn.00001289","bytes":"e8f0feffff",
#             ##"family":"cpu","type":"call","reloc":false,"type_num":3,"type2_num":0,"jump":4745,"fail":5017,
#             ##"refs":[{"addr":4745,"type":"CALL"}]}
#             
#                 
#             if offset and fcn_addr and opcode and size:
#                 #disassembly_str = disassembly_str + f"{offset:#0{18}x}" + ' <+' + str(oldsize) + '>: ' + opcode + '\n'
#                 disassembly_str = disassembly_str + opcode + '\n'
#                 oldsize += size
#             
#             offset = ''
#             fcn_addr = ''
#             opcode = ''
#             size = ''
#             
#         return disassembly_str
#     
#     
#     def predict(self, model_path, vocab_len, max_seq_len, disas):
#                             
#         model = tf.keras.models.load_model(model_path)
# 
#         ##summary_str = str(model.to_json())
#         stringlist = []
#         model.summary(print_fn=lambda x: stringlist.append(x))
#         self.model_summary_str = "\n".join(stringlist)
#         
#         vectorize_layer = TextVectorization(standardize=None,
#                                             max_tokens=vocab_len+2,
#                                             output_mode='int',
#                                             output_sequence_length=max_seq_len)
# 
#         export_model = tf.keras.Sequential([vectorize_layer,
#                                           model,
#                                           tf.keras.layers.Activation('softmax')
#                                         ])
#         
#         example = [disas]
#         ret = export_model.predict(example)
#         #print(f"Prediction: >{ret}<")
#         #print()  ##just a newline 
#         
#         return ret
#     
#     
#     def get_prediction_summary(self, ret_type_dict, ret):
#         
#         reverse_ret_type_dict = dict()
#         counter = 0
#         for key in ret_type_dict:
#             reverse_ret_type_dict[counter] = key
#             counter += 1
#         
#         arg_one_prediction_summary = []
#         arg_one_prediction_summary.append('\n')
#         
#         
#         for item in ret:
#             result = 0
#             biggest = 0
#             biggest_count = 0
#             counter = 0
#             for i in item:
#                 if i > biggest:
#                     biggest = i
#                     biggest_count = counter
#                 
#                 tmp_str = f'Type >{reverse_ret_type_dict[counter] : <{30}}< has a probability of >{i}<\n'
#                 #print(tmp_str)
#                 arg_one_prediction_summary.append(tmp_str)
#                 counter += 1
#                 
#                 result += i
#             for ret in ret_type_dict:
#                 if ret_type_dict[ret] == biggest_count:
#                     #print()
#                     #print(f'argument one is of type >{ret}<')
#                     arg_one_prediction_summary.append(f'\nBiggest Probability type >{ret}< with prob >{biggest}<\n\n')
#                     
#                     self.biggest_prob = biggest
#                     self.biggest_prob_type = ret
#                     
#         arg_one_prediction_summary.append(f'Does last count together to 1 ? Result: >{result}<')
# 
#         arg_one_prediction_summary_str = ''.join(arg_one_prediction_summary)
#         
#         return arg_one_prediction_summary_str
#     
#     
#     
#     def get_prediction(self, model, disasm_caller_callee_str, func_sign_prob_git_path):
#         ### predict now    
#         model_path = func_sign_prob_git_path + \
#                             "ubuntu-20-04-scripts/trained_models/" + model + "/saved_model/"
#                             
#         ###load vocabulary list
#         vocab_file = func_sign_prob_git_path + \
#                             "ubuntu-20-04-scripts/trained_models/" + model + "/" + \
#                             'vocabulary_list.pickle'
#         
#                                                     
#         vocabulary = pickle_lib.get_pickle_file_content(vocab_file)
#         
#         ###load max-sequence-length
#         max_seq_len_file = func_sign_prob_git_path + \
#                             "ubuntu-20-04-scripts/trained_models/" + model + "/" + \
#                             'max_seq_length.pickle'
#                             
#         max_seq_length = pickle_lib.get_pickle_file_content(max_seq_len_file)
#         
#         ret = self.predict(model_path, len(vocabulary), max_seq_length, disasm_caller_callee_str)
#         
#         ## get strings for ints, with ret_type_dict
#         ret_type_dict_file = func_sign_prob_git_path + \
#                                     "ubuntu-20-04-scripts/trained_models/" + model + "/" + \
#                                     'return_type_dict.pickle'
#                             
#         ret_type_dict = pickle_lib.get_pickle_file_content(ret_type_dict_file)
#         
#         ### get human-readable output
#         prediction_summary_str = self.get_prediction_summary(ret_type_dict, ret)
#        
#         ## store for later
# #         nr_of_args_model_summary_str = self.model_summary_str
# #         self._disasTextEdit.setPlainText(f"tf model summary:\n{self.model_summary_str}\n \
# #                                         {nr_of_args_model_summary_str}")
#        
#         return prediction_summary_str
    
#     def test_update_contents(self):
#         self.myWorker = Worker()
#         self.myWorker.start()
        
#     def update_contents(self):
#         ### get actual loaded bin-filename
#         ### cmdj('ij').get('Core').get('file')   or something like that
#         
#         curr_pos = cutter.cmd('s')
#         if curr_pos.strip() == '0x0':
#             return
#         
#         self.set_new_radare2_e()
#         
#         ### get name of current function
#         current_func_name = cutter.cmdj("afdj $F").get('name')
#         
#         print(f'current_func_name >{current_func_name}<')
#         
#         ## find data/code references to this address with $F
#         current_func_header = cutter.cmdj("axtj $F")
#         
#         ## get addr of callee
#         caller_addr = 0
#         for item_dicts in current_func_header:
#             #print(f'item_dicts >{item_dicts}<')
#             for elem in item_dicts:
#                 if elem == 'from':
#                     caller_addr = item_dicts[elem]
#                     #print(f'address of caller >{item_dicts[elem]}<')
#                 
#         
#         ## get disassembly of current/callee function
#         address = cutter.cmd('s').strip()
#         #print(f'address >{address}<')
#         disasm_callee_str = self.get_disassembly_of(address)
#         
#         print(f'disasm_callee_str >{disasm_callee_str}<')
#     
#         ### get disassembly of caller function
#         #print(f'caller-addr >{str(caller_addr)}<')
#         disasm_caller_str = self.get_disassembly_of(caller_addr)
#         
#         print(f'disasm_caller_str >{disasm_caller_str}<')
#         
#         #return
#  
#         ### split disas for the tf-model     
#         disasm_caller_str = disassembly_lib.split_disassembly(disasm_caller_str)
#         disasm_callee_str = disassembly_lib.split_disassembly(disasm_callee_str)
#         
#         #self._disasTextEdit.setPlainText("disasm_caller_callee:\n{}".format(disasm_caller_str + disasm_callee_str))
#         
#         ##check if we got caller and callee disassembly
#         if (len(disasm_caller_str) == 0) or (len(disasm_callee_str) == 0):
#             print(f'Not found callee and caller disassembly.')
#             return
#         
#         ### the path were we cloned git repo to
#         func_sign_prob_git_path = self._userHomePath + "/git/func_sign_prob/"
#         
#         ### predict now ret-type
# #         self._funcSignLabel.setText(f'plugin freeze cutter gui, wait some minutes, or wait longer till threading is implemented.\n \
# #                                     Predict return type now.')
#         ret_type_prediction_summary_str = self.get_prediction('return_type/words_100000', 
#                                                                 disasm_caller_str + disasm_callee_str, 
#                                                                 func_sign_prob_git_path)
#           
#         ## store for later, will be overridden
#         ret_type_model_summary_str = self.model_summary_str
#         ret_type_biggest_prob = self.biggest_prob
#         ret_type_biggest_prob_type = self.biggest_prob_type
#         ret_type_biggest_prob_percent = 100 * ret_type_biggest_prob
#                  
#          ### predict now nr_of_args
#         self._funcSignLabel.setText(f'plugin freeze cutter gui, wait some minutes, or wait longer till threading is implemented.\n \
#                                     Predict number of arguments now.')
#         nr_of_args_prediction_summary_str = self.get_prediction('nr_of_args', 
#                                                                 disasm_caller_str + disasm_callee_str, 
#                                                                 func_sign_prob_git_path)
#                   
#               
#         ## store for later, will be overridden
#         nr_of_args_model_summary_str = self.model_summary_str
#         nr_of_args_biggest_prob = self.biggest_prob
#         nr_of_args_biggest_prob_type = self.biggest_prob_type
#           
#         ###predict now arg_one
#         self._funcSignLabel.setText(f'plugin freeze cutter gui, wait some minutes, or wait longer till threading is implemented.\n \
#                                     Predict argument one now.')
#         arg_one_prediction_summary_str = self.get_prediction('arg_one', 
#                                                                 disasm_caller_str + disasm_callee_str, 
#                                                                 func_sign_prob_git_path)
#            
#    
#         ## store for later, will be overridden
#         arg_one_model_summary_str = self.model_summary_str
#         arg_one_biggest_prob = self.biggest_prob
#         arg_one_biggest_prob_type = self.biggest_prob_type
#         arg_one_biggest_prob_percent = 100 * arg_one_biggest_prob
#            
#         #nr_of_args_biggest_prob_type = 1
#         if nr_of_args_biggest_prob_type == 1:
#              
#             self._disasTextEdit.setPlainText(f"tf return type model summary:\n \
#                                         {ret_type_model_summary_str}\n \
#                                         {ret_type_prediction_summary_str}\n \
#                                         tf nr_of_args model summary:\n \
#                                          {nr_of_args_model_summary_str}\n \
#                                          {nr_of_args_prediction_summary_str}\n \
#                                          tf arg_one model summary:\n \
#                                          {self.model_summary_str}\n \
#                                          {arg_one_prediction_summary_str}")
#       
#             self._funcSignLabel.setText(f'{ret_type_biggest_prob_type} \
#                  <span style=\"background-color:red;\">({ret_type_biggest_prob_percent:3.1f}%)</span> \
#                  {current_func_name} ( \
#                  {arg_one_biggest_prob_type} \
#                  <span style=\"background-color:red;\">({arg_one_biggest_prob_percent:3.1f}%)</span> \
#                  )') 
#               
#             self.set_stored_radare2_e()
#             return
#               
#              
#         ###if more one args
#         ###predict now arg_two
# #         self._funcSignLabel.setText(f'plugin freeze cutter gui, wait some minutes, or wait longer till threading is implemented.\n \
# #                                     Predict argument two now.')
#         arg_two_prediction_summary_str = self.get_prediction('arg_two', 
#                                                                 disasm_caller_str + disasm_callee_str, 
#                                                                 func_sign_prob_git_path)
#           
#   
#         ## store for later, will be overridden
#         arg_two_model_summary_str = self.model_summary_str
#         arg_two_biggest_prob = self.biggest_prob
#         arg_two_biggest_prob_type = self.biggest_prob_type
#         arg_two_biggest_prob_percent = 100 * arg_two_biggest_prob
#          
#         nr_of_args_biggest_prob_type = 2 
#         if nr_of_args_biggest_prob_type == 2:
#          
#             self._disasTextEdit.setPlainText(f"tf return type model summary:\n \
#                                         {ret_type_model_summary_str}\n \
#                                         {ret_type_prediction_summary_str}\n \
#                                         tf nr_of_args model summary:\n \
#                                         {nr_of_args_model_summary_str}\n \
#                                         {nr_of_args_prediction_summary_str}\n \
#                                         tf arg_one model summary:\n \
#                                         {arg_one_model_summary_str}\n \
#                                         {arg_one_prediction_summary_str}\n \
#                                         tf arg_two model summary:\n \
#                                         {arg_two_model_summary_str}\n \
#                                         {arg_two_prediction_summary_str}")
#  
#             self._funcSignLabel.setText(f'{ret_type_biggest_prob_type} \
#                 <span style=\"background-color:red;\">({ret_type_biggest_prob_percent:3.1f}%)</span> \
#                 {current_func_name} ( \
#                 {arg_one_biggest_prob_type} \
#                 <span style=\"background-color:red;\">({arg_one_biggest_prob_percent:3.1f}%)</span> , \
#                 {arg_two_biggest_prob_type} \
#                 <span style=\"background-color:red;\">({arg_two_biggest_prob_percent:3.1f}%)</span> \
#                 )') 
#              
#             self.set_stored_radare2_e()
#             return
#         
#         
#         ###if more than two args
#         ###predict now arg_three
#         self._funcSignLabel.setText(f'plugin freeze cutter gui, wait some minutes, or wait longer till threading is implemented.\n \
#                                     Predict argument three now.')
#         arg_three_prediction_summary_str = self.get_prediction('arg_three', 
#                                                                 disasm_caller_str + disasm_callee_str, 
#                                                                 func_sign_prob_git_path)
#          
#  
#         ## store for later, will be overridden
#         arg_three_model_summary_str = self.model_summary_str
#         arg_three_biggest_prob = self.biggest_prob
#         arg_three_biggest_prob_type = self.biggest_prob_type
#         arg_three_biggest_prob_percent = 100 * arg_three_biggest_prob
#         
#         
#         
#         self._disasTextEdit.setPlainText(f"arg_three_model_summary_str >{arg_three_model_summary_str}< >{arg_three_biggest_prob}< >{arg_three_biggest_prob_type}<")
#                                             
#         ##if nr_of_args_biggest_prob_type == 3:
#         if nr_of_args_biggest_prob_type >= 3:   #hack, if more args
#              
#             self._disasTextEdit.setPlainText(f"tf return type model summary:\n \
#                                         {ret_type_model_summary_str}\n \
#                                         {ret_type_prediction_summary_str}\n \
#                                         tf nr_of_args model summary:\n \
#                                         {nr_of_args_model_summary_str}\n \
#                                         {nr_of_args_prediction_summary_str}\n \
#                                         tf arg_one model summary:\n \
#                                         {arg_one_model_summary_str}\n \
#                                         {arg_one_prediction_summary_str}\n \
#                                         tf arg_two model summary:\n \
#                                         {arg_two_model_summary_str}\n \
#                                         {arg_two_prediction_summary_str}\n \
#                                         tf arg_three model summary:\n \
#                                         {arg_three_model_summary_str}\n \
#                                         {arg_three_prediction_summary_str}")
# 
#             self._funcSignLabel.setText(f'{ret_type_biggest_prob_type} \
#                 <span style=\"background-color:red;\">({ret_type_biggest_prob_percent:3.1f}%)</span> \
#                 {current_func_name} ( \
#                 {arg_one_biggest_prob_type} \
#                 <span style=\"background-color:red;\">({arg_one_biggest_prob_percent:3.1f}%)</span> , \
#                 {arg_two_biggest_prob_type} \
#                 <span style=\"background-color:red;\">({arg_two_biggest_prob_percent:3.1f}%)</span> , \
#                 {arg_three_biggest_prob_type} \
#                 <span style=\"background-color:red;\">({arg_three_biggest_prob_percent:3.1f}%)</span> \
#                 )') 
#              
#             self.set_stored_radare2_e()
#             return
#         
#         
#         #for debug
#         print('over')
#         
#         self.set_stored_radare2_e()
#         
#         
        

class FuncSignProbCutterPlugin(cutter.CutterPlugin):
    name = "func_sign_prob plugin"
    description = "func_sign_prob plugin"
    version = "0.1"
    author = "flo"

    def setupPlugin(self):
        pass

    def setupInterface(self, main):
        action = QAction("func_sign_prob Plugin", main)
        action.setCheckable(True)
        widget = FuncSignProbDockWidget(main, action)
        main.addPluginDockWidget(widget, action)

    def terminate(self):
        pass

# def create_cutter_plugin():
#     return FuncSignProbCutterPlugin()
