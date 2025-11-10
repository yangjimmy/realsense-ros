#!/usr/bin/env python3 

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image as msg_Image

import numpy as np
import ctypes

import cv2
import torch

from ultralytics import YOLO

# Outline:
# Create subscription to rgb topic (type: msg_Image)
# Create subscription to depth topic (type: msg_Image)
# boudning box on image
# predict using YOLO

class PredictNode(Node):

    def __init__(self):
        super().__init__('PredictNode')
        self.model = YOLO('model.pt')
        self.depth_subscriber = self.create_subscription(msg_Image, 'depth', self.depth_received_callback, 10)
        self.img_subscriber = self.create_subscription(msg_Image, 'rgb', self.img_recieved_callback, 10)
        self.conf = 0.2
        self.center = [0, 0]
    
    def img_recieved_callback(self, msg):
        img = msg.data
        output = self.model(img, conf=self.conf)
        bbox = output[0].boxes.xyxy
        
        if bbox.size(0) > 0:
            # get most confident prediction
            max_conf_idx = torch.argmax(output[0].boxes.conf).item()
            x,y,x2,y2 = bbox[max_conf_idx]
            x, y, x2, y2 = [int(x), int(y), int(x2), int(y2)]

            # convert to depth frame coordinates
            self.center = [(x+x2)/2, (y+y2)/2]
        
    
    def depth_received_callback(self, msg):
        depth_img = msg.data
        return depth_img[self.center[0], self.center[1]]


def main(args=None):

    """
    The main function.
    :param args: Not used directly by the user, but used by ROS2 to configure
    certain aspects of the Node.
    """
    try:
        rclpy.init(args=args)
        predict_node = PredictNode()
        rclpy.spin(predict_node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(e)

if __name__ == '__main__':
    main()