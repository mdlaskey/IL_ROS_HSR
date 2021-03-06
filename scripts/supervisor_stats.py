from hsrb_interface import geometry
import hsrb_interface
from geometry_msgs.msg import PoseStamped, Point, WrenchStamped
import geometry_msgs
import controller_manager_msgs.srv
import cv2
from cv_bridge import CvBridge, CvBridgeError
import IPython
from numpy.random import normal
import time
#import listener
import thread

from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy

from il_ros_hsr.core.sensors import  RGBD, Gripper_Torque, Joint_Positions
from il_ros_hsr.core.joystick import  JoyStick

import matplotlib.pyplot as plt

import numpy as np
import numpy.linalg as LA
from tf import TransformListener
import tf
import rospy

from il_ros_hsr.core.grasp_planner import GraspPlanner

from il_ros_hsr.p_pi.bed_making.com import Bed_COM as COM
import sys
sys.path.append('/home/autolab/Workspaces/michael_working/yolo_tensorflow/')
# from yolo.detector import Detector
from online_labeler import QueryLabeler
from image_geometry import PinholeCameraModel as PCM

from il_ros_hsr.p_pi.bed_making.gripper import Bed_Gripper
from il_ros_hsr.p_pi.bed_making.table_top import TableTop
from il_ros_hsr.core.web_labeler import Web_Labeler
from il_ros_hsr.core.python_labeler import Python_Labeler

from il_ros_hsr.p_pi.bed_making.check_success import Success_Check
from il_ros_hsr.p_pi.bed_making.self_supervised import Self_Supervised
import il_ros_hsr.p_pi.bed_making.config_bed as cfg
import cPickle as pickle
import os

from il_ros_hsr.core.rgbd_to_map import RGBD2Map

from data_aug.draw_cross_hair import DrawPrediction

dp = DrawPrediction()
#latest, 46-49 from rollout_dart
sm = 0
for rnum in range(0, 57):
	# path = cfg.STAT_PATH+'stat_' + str(rnum) + '/rollout.p'
	path = cfg.ROLLOUT_PATH+'rollout_' + str(rnum) + '/rollout.p'

	#IPython.embed()

	if os.path.exists(path):
		data = pickle.load(open(path,'rb'))

		count = 0
		
		for datum in data:

			if type(datum) == list: 
				continue

			if datum['type'] == 'success':

				#pose = datum['pose']
				
				sm = sm + datum['class']
				


print "SM ", sm

	


