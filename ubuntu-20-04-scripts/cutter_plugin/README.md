ln -s /home/user/git/func_sign_prob/ubuntu-20-04-scripts/cutter_plugin/func_sign_prob_plugin.py  /home/user/.local/share/RadareOrg/Cutter/plugins/python/func_sign_prob_plugin.py


ln -s /home/user/git/func_sign_prob/ubuntu-20-04-scripts/lib/disassembly_lib.py /home/user/.local/share/RadareOrg/Cutter/plugins/python/disassembly_lib.py


/home/user/.local/share/RadareOrg/Cutter/plugins/python/func_sign_prob_plugin.py


// appImage includes no tensorflow, build from source
-->on ubuntu-20.04   https://cutter.re/docs/building.html

// remove python2 if installed
apt list --installed|grep python
apt remove --purge python2.7

//if installed, remove pip3 installed stuff, use ubuntu-stuff
pip3 uninstall pyside2
pip3 uninstall shiboken2


sudo apt-get install python-is-python3
sudo apt install python3-pyside2.qtcore
sudo apt install python3-pyside2.qtwidgets
sudo apt install python3-pyside2.qtqml    ###dont know really, was because qqml.h error
sudo apt install libpyside2-dev
sudo apt install libpyside2-py3-5.14
sudo apt install libshiboken2-dev
sudo apt install libshiboken2-py3-5.14
sudo apt install shiboken2

sudo apt install qtdeclarative5-dev    ###Qtqml/qqml.h no such file or directory

// -DCMAKE_EXE_LINKER_FLAGS="-Wl,--disable-new-dtags"

cmake -DCMAKE_EXE_LINKER_FLAGS="-Wl,--disable-new-dtags" -B build -DCUTTER_ENABLE_PYTHON=ON -DCUTTER_ENABLE_PYTHON_BINDINGS=ON -DCUTTER_USE_BUNDLED_RADARE2=ON  ../src/

cmake --build build