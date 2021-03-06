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
sys.path.append('/home/autolab/Workspaces/michael_working/fast_grasp_detect/')

from online_labeler import QueryLabeler
from image_geometry import PinholeCameraModel as PCM

sys.path.append('/home/autolab/Workspaces/michael_working/RCNN-Obj-Dectect/')
from rgbd_object_dectector import Depth_Object 

from il_ros_hsr.p_pi.tpc.gripper import Lego_Gripper
from il_ros_hsr.p_pi.tpc.TPC_singulate import run_connected_components, draw
from il_ros_hsr.p_pi.bed_making.table_top import TableTop
from il_ros_hsr.core.web_labeler import Web_Labeler
from il_ros_hsr.core.python_labeler import Python_Labeler

from il_ros_hsr.p_pi.bed_making.check_success import Success_Check
from il_ros_hsr.p_pi.bed_making.get_success import get_success
from il_ros_hsr.p_pi.bed_making.self_supervised import Self_Supervised
import il_ros_hsr.p_pi.bed_making.config_bed as cfg


from il_ros_hsr.core.rgbd_to_map import RGBD2Map

from il_ros_hsr.p_pi.bed_making.initial_state_sampler import InitialSampler
class BottlePicker():

    def __init__(self):
        '''
        Initialization class for a Policy

        Parameters
        ----------
        yumi : An instianted yumi robot 
        com : The common class for the robot
        cam : An open bincam class

        debug : bool 

            A bool to indicate whether or not to display a training set point for 
            debuging. 

        '''

        self.robot = hsrb_interface.Robot()
        self.rgbd_map = RGBD2Map()

        self.omni_base = self.robot.get('omni_base')
        self.whole_body = self.robot.get('whole_body')

        
        self.side = 'BOTTOM'

        self.cam = RGBD()
        self.com = COM()



        # if cfg.USE_WEB_INTERFACE:
        #     self.wl = Web_Labeler()
        # else:
        #     self.wl = Python_Labeler(cam = self.cam)


        self.com.go_to_initial_state(self.whole_body)
        
        self.tt = TableTop()
        self.tt.find_table(self.robot)
        
    
        self.grasp_count = 0
      

        self.br = tf.TransformBroadcaster()
        self.tl = TransformListener()



        self.gp = GraspPlanner()

        self.gripper = Lego_Gripper(self.gp,self.cam,self.com.Options,self.robot.get('gripper'))

        self.RCNN = Depth_Object("bottle")
        #self.test_current_point()
       
        #thread.start_new_thread(self.ql.run,())
        print "after thread"

       


    def find_mean_depth(self,d_img):
        '''
        Evaluates the current policy and then executes the motion 
        specified in the the common class
        '''

        indx = np.nonzero(d_img)

        mean = np.mean(d_img[indx])

        return

    def move_to_top_side(self):
        self.tt.move_to_pose(self.omni_base, 'right_down')
        self.tt.move_to_pose(self.omni_base, 'right_up')

    def bottle_pick(self):

        # self.rollout_data = []
        self.position_head()

        self.move_to_top_side()
        print("ARRIVED AT TOP SIDE")
        time.sleep(2)

        #cycle through positions for a long time (30)
        pose_num = 0
        pose_sequence = ['top_mid_far', 'top_left_far', 'top_mid']
        while pose_num < 30:
            pose_name = pose_sequence[pose_num % len(pose_sequence)]
            self.tt.move_to_pose(self.omni_base, pose_name)
            print("ARRIVED AT POSE " + pose_name)
            pose_num += 1

            c_img = self.cam.read_color_data()
            d_img = self.cam.read_depth_data()
            if(not c_img == None and not d_img == None):
                centers, out_img = self.RCNN.detect(c_img)

                # if self.get_new_grasp:
                #     c_m, dirs = run_connected_components(c_img)
                #     draw(c_img,c_m,dirs)
                    
                #     c_img = self.cam.read_color_data()
                #     d_img = self.cam.read_depth_data()

                #     self.gripper.find_pick_region_cc(c_m[0],dirs[0],c_img,d_img,self.grasp_count)
                
                # pick_found,bed_pick = self.check_card_found()

                # self.gripper.execute_grasp(bed_pick,self.whole_body,'head_down')
                
                # self.grasp_count += 1
                # self.whole_body.move_to_go()
                # self.tt.move_to_pose(self.omni_base,'lower_start')
                # time.sleep(1)
                # self.whole_body.move_to_joint_positions({'head_tilt_joint':-0.8})
                
                print("DETECTED: " + str(centers))
                cv2.imwrite("debug_imgs/debug" + str(pose_num) + ".png", out_img)
            timer.sleep(5)
    

    def check_card_found(self):

        # try:
        transforms = self.tl.getFrameStrings()
    
        cards = []

        try:
        
            for transform in transforms:
                print transform
                current_grasp = 'bed_'+str(self.grasp_count)
                if current_grasp in transform:
                    print 'got here'
                    f_p = self.tl.lookupTransform('map',transform, rospy.Time(0))
                    cards.append(transform)

        except: 
            rospy.logerr('bed pick not found yet')
                

        return True, cards
    
    def position_head(self):

        self.tt.move_to_pose(self.omni_base,'lower_start')
        self.whole_body.move_to_joint_positions({'head_tilt_joint':-0.8})

        




if __name__ == "__main__":
   
    
    cp = BottlePicker()

    cp.bottle_pick()

