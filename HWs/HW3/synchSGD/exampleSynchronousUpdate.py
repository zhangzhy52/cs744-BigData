import tensorflow as tf
import os

# number of features in the criteo dataset after one-hot encoding
num_features = 33762578
s_batch = 2
eta = .1

iterations = 20

s_test = 4;

file_dict = {0:["00","01","02","03","04"],
             1:["05","06","07","08","09"],
             2:["10","11","12","13","14"],
             3:["15","16","17","18","19"],
             4:["20","21"],
            -1:["22"]}


g = tf.Graph()

with g.as_default():

    def get_datapoint_iter(file_idx=[],batch_size = s_batch):
        fileNames = map(lambda s: "/home/ubuntu/criteo-tfr-tiny/tfrecords"+s,file_idx)
        # We first define a filename queue comprising 5 files.
        filename_queue = tf.train.string_input_producer(fileNames, num_epochs=None)


        # TFRecordReader creates an operator in the graph that reads data from queue
        reader = tf.TFRecordReader()

        # Include a read operator with the filenae queue to use. The output is a string
        # Tensor called serialized_example
        _, serialized_example = reader.read(filename_queue)


        # The string tensors is essentially a Protobuf serialized string. With the
        # following fields: label, index, value. We provide the protobuf fields we are
        # interested in to parse the data. Note, feature here is a dict of tensors
        features = tf.parse_single_example(serialized_example,
                                           features={
                                            'label': tf.FixedLenFeature([1], dtype=tf.int64),
                                            'index' : tf.VarLenFeature(dtype=tf.int64),
                                            'value' : tf.VarLenFeature(dtype=tf.float32),
                                           }
                                          )

        label = features['label']
        index = features['index']
        value = features['value']

        # These print statements are there for you see the type of the following
        # variables
        print label
        print index
        print value

        # since we parsed a VarLenFeatures, they are returned as SparseTensors.
        # To run operations on then, we first convert them to dense Tensors as below.
        dense_feature = tf.sparse_to_dense(tf.sparse_tensor_to_dense(index),
                                       [33762578,],
        #                               tf.constant([33762578, 1], dtype=tf.int64),
                                       tf.sparse_tensor_to_dense(value))


        label_flt = tf.cast(label, tf.float32)
        # min_after_dequeue defines how big a buffer we will randomly sample
        #   from -- bigger means better shuffling but slower start up and more
        #   memory used.
        # capacity must be larger than min_after_dequeue and the amount larger
        #   determines the maximum we will prefetch.  Recommendation:
        #   min_after_dequeue + (num_threads + a small safety margin) * batch_size
        min_after_dequeue = 10
        capacity = min_after_dequeue + 3 * batch_size
        example_batch, label_batch = tf.train.shuffle_batch(
          [dense_feature[0:num_features], label_flt], batch_size=batch_size, capacity=capacity,
          min_after_dequeue=min_after_dequeue)

        return example_batch, label_batch



    def calc_gradient(X,W,Y):
        error = tf.sigmoid(tf.mul(Y,tf.matmul(X,W)))
        error_m1 = error-1
        gradient = tf.matmul(tf.transpose(X),tf.mul(Y,error_m1))
        return tf.reduce_sum(gradient,1)

    # creating a model variable on task 0. This is a process running on node vm-32-1
    with tf.device("/job:worker/task:0"):
        w = tf.Variable(tf.ones([num_features, 1]), name="model")

    # creating 5 reader operators to be placed on different operators
    # here, they emit predefined tensors. however, they can be defined as reader
    # operators as done in "exampleReadCriteoData.py"
    gradients = []
    for i in range(0, 5):
        with tf.device("/job:worker/task:%d" % i):
            # read the data
            X,Y = get_datapoint_iter(file_dict[i],batch_size=s_batch)
            # calculate the gradient
            local_gradient = calc_gradient(X,w,Y)
            # multiple the gradient with the learning rate and submit it to update the model
            gradients.append(tf.mul(local_gradient, eta))


    # we create an operator to aggregate the local gradients
    with tf.device("/job:worker/task:0"):
        aggregator = tf.add_n(gradients)
        agg_shape = tf.reshape(aggregator,[num_features, 1])
        #
        assign_op = w.assign_add(agg_shape)

    ###########################################################
    def calc_precision(W,X,Y):
        diffs = tf.sign(tf.mul(tf.matmul(X,W),Y))
        precision = tf.reduce_sum((diffs+1)/2)/s_test
        return precision

    with tf.device("/job:worker/task:0"):
        test_X,test_Y = get_datapoint_iter(file_dict[-1],batch_size = s_test)
        precision = calc_precision(w,test_X,test_Y)

    ###########################################################
    with tf.Session("grpc://vm-32-1:2222") as sess:
        sess.run(tf.initialize_all_variables())
        # this is new command and is used to initialize the queue based readers.
        # Effectively, it spins up separate threads to read from the files
        tf.train.start_queue_runners(sess=sess)
        for i in range(iterations):
            print "Step ",i
            sess.run(assign_op)

            if i>1 and i%2 == 0:
                print "precision: ",precision.eval()
            # print w.eval()

        sess.close()
