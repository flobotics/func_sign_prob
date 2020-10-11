# func_sign_prob

user => your username in the system

Create directory /home/user/git
mkdir -p /home/user/git

Switch into the new directory
cd /home/user/git

Clone this repo
git clone https://github.com/flobotics/func_sign_prob.git

Switch into func_sign_prob/ubuntu-20-04-scripts directory
cd unc_sign_prob/ubuntu-20-04-scripts



Build pickle files from ubuntu packages. Pickle files contain disassembly (att and intel)
for functions of binaries in ubuntu packages. And more info.
--> ds-builder-raw.py

Older files.
--> ds-builder.py and ds-builder-raw-host.py and ds-builder-2-Copy1.ipynb


-------------
After building ds-builder-raw.py go into ubuntu-20-04-scripts/build_tf_dataset/second directory.

First run "python3 tokenize_att_disassembly.py" .Perhaps you need to create the directory /tmp/testtars and copy all/some pickle files from ubuntu-20-04-pickles/ directory into /tmp/testtars, then run again.


Second run "python3 get_vocab_size_and_seq_length.py"

Third run "python3 build_return_type_dict.py"

Then switch into ubuntu-20-04-scripts/build_tf_model/second and run
"python3 build_tf_tokenize_model.py"


