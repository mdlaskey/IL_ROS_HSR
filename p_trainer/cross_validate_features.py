import cPickle as pickle
import sys, os
import IPython
from compile_sup import Compile_Sup
from il_ros_hsr.tensor import inputdata_f
import numpy as np, argparse
from numpy.random import random
import cv2
import time

os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"   # see issue #152
os.environ["CUDA_VISIBLE_DEVICES"]="0"

#######NETWORK FILES TO BE CHANGED#####################
#specific: imports options from specific options file
from il_ros_hsr.p_pi.vgg_options import VGG_Options as Options
from il_ros_hsr.p_pi.com import Safe_COM as COM
from il_ros_hsr.p_pi.features import Features

#specific: fetches specific net file
from il_ros_hsr.tensor.nets.net_vgg import VggNet as Net_VGG
from il_ros_hsr.tensor.nets.net_pose_estimation import PoseEstimationNet as Net_Pose_Estimation
########################################################

if __name__ == '__main__':
    ITERATIONS = 1000
    BATCH_SIZE = 100
    options = Options()

    f = []

    for (dirpath, dirnames, filenames) in os.walk(options.rollouts_dir):
        f.extend(dirnames)

    raw_data = []
    labels = []

    for filename in f:
        rollout_data = pickle.load(open(options.rollouts_dir+filename+'/rollout.p','r'))

        raw_data.append(rollout_data)
        labels.append(filename)

    state_stats = []
    com = COM()
    features = Features()

    feature_spaces = []
    #control- no featurization
    feature_spaces.append({"feature": features.identity_flatten, "run": True, "name": "control", "net": Net_VGG, "sdim": 50176})
    #VGG
    feature_spaces.append({"feature": features.vgg_extract, "run": True, "name": "vgg", "net": Net_VGG, "sdim": 25088})
    #pose branch 0
    func0 = lambda state: features.pose_extract(state, 0, -1)
    feature_spaces.append({"feature": func0, "run": True, "name": "pose0", "net": Net_Pose_Estimation, "sdim": 100352})
    #pose branch1/2
    for step in range(1, 7):
        for branch in range(1, 3):
            func = lambda state, theBranch=branch, theStep=step: features.pose_extract(state, theBranch, theStep)
            name = "pose" + str(step) + "_" + str(branch)
            if branch == 1:
                feature_spaces.append({"feature": func, "run": True, "name": name, "net": Net_Pose_Estimation, "sdim": 29792})
            elif branch == 2:
                feature_spaces.append({"feature": func, "run": True, "name": name, "net": Net_Pose_Estimation, "sdim": 14896})

    for feature_space in feature_spaces:
        if feature_space["run"]:
            print("precomputing " + feature_space["name"] + " features")
            data = inputdata_f.IMData(raw_data, state_space = feature_space["feature"] ,precompute= True)

            all_train_losses = []
            all_test_losses = []
            train_times = []

            print("running cross-validation trials for " + feature_space["name"])
            for trial in range(10):
                print("starting trial " + str(trial))
                data.shuffle()
                net = feature_space["net"](options, state_dim = feature_space["sdim"])

                start = time.time()
                save_path, train_loss,test_loss = net.optimize(ITERATIONS,data, batch_size=BATCH_SIZE,save=False)
                end = time.time()
                train_times.append(end - start)

                all_train_losses.append(train_loss)
                all_test_losses.append(test_loss)

                net.clean_up()

            print("finished cross validation for" + feature_space["name"] + "- saving stats")

            avg_train_loss = np.mean(np.array(all_train_losses), axis=0)
            avg_test_loss = np.mean(np.array(all_test_losses), axis=0)
            avg_train_time = np.mean(train_times)

            stat = {}
            stat['type'] = feature_space["name"]
            stat['path'] = save_path
            stat['all_train_time'] = train_times
            stat['avg_train_time'] = avg_train_time
            stat['all_test_loss'] = all_test_losses
            stat['all_train_loss'] = all_train_losses
            stat['avg_test_loss'] = avg_test_loss
            stat['avg_train_loss'] = avg_train_loss

            state_stats.append(stat)

            pickle.dump(state_stats,open(options.stats_dir+'all_cross_validate_stats.p','wb'))

    features.clean_up_nets()
