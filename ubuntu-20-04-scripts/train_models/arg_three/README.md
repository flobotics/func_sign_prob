This model is trained with text=caller-callee-disassembly and label=function-argument-three

clone the rep into /home/user/git
</br>
Then run these commands, and you got a trained model.
</br>
All done with tf-nightly2.5
</br>

The "/home/user/arg_three_basedir" directory you can choose by yourself, it will be
created if not exist.

<pre><code>
-l=1000   The output text will be maximum this value, bigger ones will be discarded. <br/>
			This option is for smaller GPU setups. If you got e.g. CPU-only use ~300-1000,  for e.g. 8xV100 use 200000.</br>
			Default is 200000</br>
-e=2	  The number of epochs it should train. Default: 1
</code></pre>
</br>


<pre><code>
python3 build_arg_three_dataset.py -b=/home/user/arg_three_basedir -l=1000
</code></pre>
</br>

<pre><code>
python3 build_ret_type__vocab_seq_len.py -b=/home/user/arg_three_basedir
</code></pre>
</br>

<pre><code>
python3 build_balanced_dataset.py -b=/home/user/arg_three_basedir
</code></pre>
</br>

<pre><code>
python3 build_balanced_ret_type__vocab_seq_len.py -b=/home/user/arg_three_basedir
</code></pre>
</br>

<pre><code>
python3 transform_ret_type_to_int.py -b=/home/user/arg_three_basedir
</code></pre>
</br>

<pre><code>
python3 train_arg_three_model_lstm.py -b=/home/user/arg_three_basedir -e=2
</code></pre>
</br>
