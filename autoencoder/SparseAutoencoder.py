# -*- coding: utf-8 -*-
"""
Created on Tue Apr 26 16:58:49 2016

@author: tyrion
"""

import numpy as np
import tensorflow as tf
import pickle

from utils import read_data

N_HIDDEN = 200
N_INPUT = N_OUTPUT = 64
AHEAD_STEP = 64
BETA = tf.constant(3.)
LAMBDA = tf.constant(.001)
RHO = tf.constant(0.1)


def train():
    data_path = '/home/tyrion/lannister/1024/tyrion.pkl'
#    data_path = '/home/tyrion/Documents/Cloud Computing/python/data/72/tyrion.pkl'
    training_data, _, _, _, load_mean, load_std = read_data(data_path, N_INPUT, N_OUTPUT, AHEAD_STEP)
    NUMSAMPLES = 288 * 26 / N_INPUT
    print(training_data.shape)

    sess = tf.Session()

#    def variable_summaries(var, name):
#        with tf.name_scope('summaries'):
#            mean = tf.reduce_mean(var)
#            tf.scalar_summary('mean/' + name, mean)
#            with tf.name_scope('stddev'):
#                stddev = tf.sqrt(tf.reduce_sum(tf.square(var - mean)))
#                tf.scalar_summary('stddev/' + name, stddev)
#                tf.scalar_summary('max/' + name, tf.reduce_max(var))
#                tf.scalar_summary('min/' + name, tf.reduce_min(var))
#                tf.histogram_summary(name, var)

    # Input placeholders
    with tf.name_scope('input'):
        # Construct the tensor flow model
        x = tf.placeholder("float", [None, N_INPUT], name='x-input')

    def autoencoder(X, weights, biases):
        with tf.name_scope('hidden_layer'):
            hiddenlayer = tf.sigmoid(tf.add(tf.matmul(X, weights['hidden']), biases['hidden']))
        with tf.name_scope('output_layer'):
            out = tf.add(tf.matmul(hiddenlayer, weights['out']), biases['out'])
        return {'out': out, 'hidden': hiddenlayer}

    weights = {'hidden': tf.get_variable("wei_hid", shape=[N_INPUT, N_HIDDEN], dtype=tf.float32,
            initializer=tf.random_uniform_initializer(-tf.sqrt(1./N_INPUT),tf.sqrt(1./N_INPUT))),
               'out': tf.get_variable("wei_out", shape=[N_HIDDEN, N_OUTPUT], dtype=tf.float32,
            initializer=tf.random_uniform_initializer(-tf.sqrt(1./N_HIDDEN),tf.sqrt(1./N_HIDDEN)))}
#    variable_summaries(weights['hidden'], 'hidden_layer' + '/weights')
#    variable_summaries(weights['out'], 'output_layer' + '/weights')

    biases = {'hidden': tf.get_variable("bia_hid", shape=[N_HIDDEN], dtype=tf.float32,
           initializer=tf.constant_initializer(0)),
              'out': tf.get_variable("bia_out", shape=[N_OUTPUT], dtype=tf.float32,
           initializer=tf.constant_initializer(0))}
#    variable_summaries(biases['hidden'], 'hidden_layer' + '/biases')
#    variable_summaries(biases['out'], 'output_layer' + '/biases')
#
    pred = autoencoder(x, weights, biases)
    rho_hat = tf.div(tf.reduce_sum(pred['hidden'], 0), tf.constant(float(NUMSAMPLES)))

    def logfunc(x, x2):
        return tf.mul(x, tf.log(tf.div(x, x2)))

    # Construct cost
    def KL_Div(rho, rho_hat):
        invrho = tf.sub(tf.constant(1.), rho)
        invrhohat = tf.sub(tf.constant(1.), rho_hat)
        logrho = tf.add(logfunc(rho, rho_hat), logfunc(invrho, invrhohat))
        return logrho

    diff = tf.sub(pred['out'], x)

    with tf.name_scope('loss'):
        cost_J = tf.div(tf.nn.l2_loss(diff), tf.constant(float(NUMSAMPLES)))
        tf.scalar_summary('loss', cost_J)

    with tf.name_scope('cost_sparse'):
        cost_sparse = tf.mul(BETA, tf.reduce_sum(KL_Div(RHO, rho_hat)))
        tf.scalar_summary('cost_sparse', cost_sparse)

    with tf.name_scope('cost_reg'):
        cost_reg = tf.mul(LAMBDA, tf.add(tf.nn.l2_loss(weights['hidden']),
                                         tf.nn.l2_loss(weights['out'])))
        tf.scalar_summary('cost_reg', cost_reg)

    with tf.name_scope('cost'):
        cost = tf.add(tf.add(cost_J, cost_reg), cost_sparse)
        tf.scalar_summary('cost', cost)

#    optimizer = tf.train.AdamOptimizer(0.01).minimize(cost)

    tvars = tf.trainable_variables()
    grads, _ = tf.clip_by_global_norm(tf.gradients(cost, tvars), 10)

    lr = tf.placeholder("float", name='learning_rate')
    optimizer = tf.train.AdamOptimizer(lr)
    apply_optimizer = optimizer.apply_gradients(zip(grads, tvars))

#    merged = tf.merge_all_summaries()
#    writer = tf.train.SummaryWriter('./sae_logs', sess.graph)
    # Initilizing the variables
    init = tf.initialize_all_variables()

    # Lauch the graph
    sess.run(init)

#    # Add ops to save and restore all the variables.
#    saver = tf.train.Saver({"model/RNN/ae_weights": weights['hidden'],
#                            "model/RNN/ae_biases": biases['hidden']})

    # Training cycle
    load_num = training_data.shape[0]
    for i in xrange(100):
        Cost = Cost_j = Cost_reg = Cost_sparse = 0.0
        for j in xrange(load_num):
#            summary, _ = sess.run([merged, optimizer], feed_dict={x: training_data[j]})
#            sess.run([apply_optimizer], feed_dict={x: training_data[j]})
            if i < 50:
                lr_assign = 0.01
            else:
                lr_assign = 0.001
            c,j,reg,sparse,_ = sess.run([cost,cost_J,cost_reg,cost_sparse,apply_optimizer],
                                      feed_dict={x: training_data[j], lr: lr_assign})
            Cost += c / load_num
            Cost_j += j / load_num
            Cost_reg += reg / load_num
            Cost_sparse += sparse / load_num
#        a = training_data.shape[0]
#        print(a)
#        Cost /= a
#        Cost_j /= a
#        Cost_reg /= a
#        Cost_sparse /= a
        print("Epoch %d: Cost = %f, Loss = %f, Reg = %f, Sparsity = %f"
                % (i, Cost, Cost_j, Cost_reg, Cost_sparse))
#        writer.add_summary(summary, i)
#        if i == 199:
#            a = sess.run(pred['hidden'], feed_dict={x: training_data[0]})
#            print(a[0])
    print("Optimization Finished!")

    mach1 = 12
    mach2 = 24
    time1 = 10
    time2 = 20
    a = np.asarray(sess.run(pred['out'], feed_dict={x: training_data[mach1]}), dtype=np.float32)
    print(a[time1])
    print(training_data[mach1][time1])
    def save_pkl(data, path):
        output = open(path,'wb')
        pickle.dump(data, output)
        output.close()
    save_pkl(training_data[mach1][time1]*load_std+load_mean, "./compare/1.pkl")
    save_pkl(a[time1]*load_std+load_mean, "./compare/2.pkl")

    b = np.asarray(sess.run(pred['out'], feed_dict={x: training_data[mach2]}), dtype=np.float32)
    save_pkl(training_data[mach2][time2]*load_std+load_mean, "./compare/3.pkl")
    save_pkl(b[time2]*load_std+load_mean, "./compare/4.pkl")

    ae_weights = np.asarray(sess.run(weights['hidden']), dtype=np.float32)
    ae_biases = np.asarray(sess.run(biases['hidden']), dtype=np.float32)
    save_pkl(ae_weights, "./compare/weights.pkl")
    save_pkl(ae_biases, "./compare/biases.pkl")

def main(_):
    train()

if __name__ == '__main__':
    tf.app.run()
