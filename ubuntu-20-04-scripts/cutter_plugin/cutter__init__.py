import sys
import os
sys.path.append(os.path.dirname(__file__))

import func_sign_prob_plugin

print(f'sys-path >{sys.path}<')

def create_cutter_plugin():
    return func_sign_prob_plugin.MyCutterPlugin()