clone the rep into /home/user/git
</br>
Then run these commands, and you got a trained model.
</br>
All done with tf-nightly2.5


<pre><code>
python3 build_nr_of_args_dataset.py -b=/home/user/nr_of_args_basedir
</code></pre>
</br>

<pre><code>
python3 build_ret_type__vocab_seq_len.py -b=/home/user/nr_of_args_basedir
</code></pre>
</br>

<pre><code>
python3 build_balanced_dataset.py -b=/home/user/nr_of_args_basedir
</code></pre>
</br>

<pre><code>
python3 build_balanced_ret_type__vocab_seq_len.py -b=/home/user/nr_of_args_basedir
</code></pre>
</br>

<pre><code>
python3 transform_ret_type_to_int.py -b=/home/user/nr_of_args_basedir
</code></pre>
</br>

<pre><code>
python3 train_nr_of_args_model_lstm.py -b=/home/user/nr_of_args_basedir
</code></pre>
</br>


Epoch 39/40
8/8 [==============================] - 1s 163ms/step - loss: 0.3191 - accuracy: 0.9047 - val_loss: 0.1858 - val_accuracy: 0.9542
Epoch 40/40
8/8 [==============================] - 1s 162ms/step - loss: 0.3405 - accuracy: 0.8764 - val_loss: 0.1587 - val_accuracy: 0.9477
2/2 [==============================] - 0s 53ms/step - loss: 0.2271 - accuracy: 0.9205
Loss:  0.22714632749557495
Accuracy:  0.9205297827720642
Saving trained word embeddings (meta.tsv,vecs.tsv)             (usable in tensorboard->Projector, use chromium-browser to see it correctly,firefox does not always wor
k)
10 vocab words >['', '[UNK]', '%', 'null', ',', 'x', '1', 'mov', ')', '(']<
Building vectors.tsv file, use tensorboard->projector with chromium-browser
Building metadata.tsv file, use tensorboard->projector with chromium-browser


![nr-of-args-scalars](../../pictures/nr_of_args/nr-of-args-scalars.png)