This model is trained with text=caller-callee-disassembly and label=function-argument-two

clone the rep into /home/user/git
</br>
Then run these commands, and you got a trained model.
</br>
All done with tf-nightly2.5
</br>

The "/home/user/arg_two_basedir" directory you can choose by yourself, it will be
created if not exist.


<pre><code>
python3 build_arg_two_dataset.py -b=/home/user/arg_two_basedir
</code></pre>
</br>

<pre><code>
python3 build_ret_type__vocab_seq_len.py -b=/home/user/arg_two_basedir
</code></pre>
</br>

<pre><code>
python3 build_balanced_dataset.py -b=/home/user/arg_two_basedir
</code></pre>
</br>

<pre><code>
python3 build_balanced_ret_type__vocab_seq_len.py -b=/home/user/arg_two_basedir
</code></pre>
</br>

<pre><code>
python3 transform_ret_type_to_int.py -b=/home/user/arg_two_basedir
</code></pre>
</br>

<pre><code>
python3 train_arg_two_model_lstm.py -b=/home/user/arg_two_basedir
</code></pre>
</br>
