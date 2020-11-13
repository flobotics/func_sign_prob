1. python3 build_nr_of_args_dataset.py -p=/home/user/nr_test/ -s=/home/user/nr_save_dir/ -w=/home/user/nr_work_dir/

2. python3 build_ret_type__vocab_seq_len.py -s=/home/user/nr_save_dir/

3. python3 build_balanced_dataset.py -s=/home/user/nr_save_dir/

4. python3 train_nr_of_args_model_lstm.py -s=/home/ubu/nr_save_dir/ -m=/home/ubu/nr_save_dir/tfrecord/ -r=/home/ubu/nr_save_dir/tfrecord/ -v=/home/ubu/nr_save_dir/tfrecord/