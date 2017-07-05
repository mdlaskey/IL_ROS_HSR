import cPickle as pickle
import sys, os
import IPython
from compile_sup import Compile_Sup
from il_ros_hsr.tensor import inputdata_f
import numpy as np, argparse
from numpy.random import random
import cv2

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
    ITERATIONS = 2000
    BATCH_SIZE = 200
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
    feature_spaces.append({"feature": features.vgg_extract, "run": True, "name": "vgg", "net": Net_VGG})
    feature_spaces.append({"feature": features.pose_0_extract, "run": True, "name": "pose0", "net": Net_Pose_Estimation})
    feature_spaces.append({"feature": features.pose_1_1_extract, "run": True, "name": "pose1_1", "net": Net_Pose_Estimation})
    feature_spaces.append({"feature": features.pose_1_2_extract, "run": True, "name": "pose1_2", "net": Net_Pose_Estimation})

    for feature_space in feature_spaces:
        if feature_space["run"]:
            print("precomputing " + feature_space["name"] + " features")
            data = inputdata_f.IMData(raw_data, state_space = feature_space["feature"] ,precompute= True)

            all_train_losses = []
            all_test_losses = []
            print("running cross-validation trials for " + feature_space["name"])
            for trial in range(10):
                data.shuffle()
                net = feature_space["net"](options)
                save_path, train_loss,test_loss = net.optimize(ITERATIONS,data, batch_size=BATCH_SIZE,save=False)

                all_train_losses.append(train_loss)
                all_test_losses.append(test_loss)

                net.clean_up()

            print("finished cross validation- saving stats")

            avg_train_loss = np.mean(np.array(all_train_losses), axis=0)
            avg_test_loss = np.mean(np.array(all_test_losses), axis=0)

            stat = {}
            stat['type'] = feature_space["name"]
            stat['test_loss'] = avg_test_loss
            stat['train_loss'] = avg_train_loss
            state_stats.append(stat)

            pickle.dump(state_stats,open(options.stats_dir+'cross_validate_stats.p','wb'))

    features.clean_up_nets()