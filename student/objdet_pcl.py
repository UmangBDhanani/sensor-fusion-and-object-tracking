# ---------------------------------------------------------------------
# Project "Track 3D-Objects Over Time"
# Copyright (C) 2020, Dr. Antje Muntzinger / Dr. Andreas Haja.
#
# Purpose of this file : Process the point-cloud and prepare it for object detection
#
# You should have received a copy of the Udacity license together with this program.
#
# https://www.udacity.com/course/self-driving-car-engineer-nanodegree--nd013
# ----------------------------------------------------------------------
#The code is reference from udacity's mian repository and the steps are performed accoidng to the project requirements in individual student tasks.

# general package imports
import cv2
import numpy as np
import torch
import zlib
import open3d as o3d
from PIL import Image
import io

# add project directory to python path to enable relative imports
import os
import sys
PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

# waymo open dataset reader
from tools.waymo_reader.simple_waymo_open_dataset_reader import utils as waymo_utils
from tools.waymo_reader.simple_waymo_open_dataset_reader import dataset_pb2, label_pb2

# object detection tools and helper functions
import misc.objdet_tools as tools


# visualize lidar point-cloud
def show_pcl(pcl):

    ####### ID_S1_EX2 START #######     
    #######

    # initialize open3d with key callback and create window
    vis = o3d.visualization.VisualizerWithKeyCallback()
    vis.create_window()

    # create instance of open3d point-cloud class
    pcd = o3d.geometry.PointCloud()

    # set points in pcd instance by converting the point-cloud into 3d vectors
    pcd.points = o3d.utility.Vector3dVector(pcl[:, :3])

    # adding and updating the point cloud for consecutive frames
    vis.add_geometry(pcd)
    vis.update_renderer()
    vis.update_geometry(pcd)

    #visualize point cloud
    right_key_call_back = 262
    vis.register_key_callback(right_key_call_back, lambda: None)

    vis.run()

    #######
    ####### ID_S1_EX2 END #######     
       

# visualize range image
def show_range_image(frame, lidar_name):

    ####### ID_S1_EX1 START #######     
    #######
    # extract lidar data and range image for the roof-mounted lidar
    lidar = [obj for obj in frame.lasers if obj.name == lidar_name][0]
    ri = []
    if len(lidar.ri_return1.range_image_compressed) > 0:
        ri = dataset_pb2.MatrixFloat()
        ri.ParseFromString(zlib.decompress(lidar.ri_return1.range_image_compressed))
        ri = np.array(ri.data).reshape(ri.shape.dims)
    
    # extract the range and the intensity channel from the range image
    ri_range = ri[:,:,0]
    ri_intensity = ri[:,:,1]

    # set values <0 to zero
    ri_range[ri_range<0] = 0.0
    ri_intensity[ri_intensity<0] = 0.0
    
    # map the range channel onto an 8-bit scale and make sure that the full range of values is appropriately considered
    ri_range = ri_range * 255 / np.abs((np.amax(ri_range) - np.amin(ri_range)))
    img_range = ri_range.astype(np.uint8)

    # map the intensity channel onto an 8-bit scale and normalize to mitigate the influence of outliers
    ri_intensity = (np.amax(ri_intensity) * 2) * ri_intensity * 255 / np.abs((np.amax(ri_intensity) - np.amin(ri_intensity)))
    img_intensity = ri_intensity.astype(np.uint8)

    # stack the range and intensity image vertically and convert the result to an unsigned 8-bit integer
    img_range_intensity = np.vstack((img_range, img_intensity))
    img_range_intensity = img_range_intensity.astype(np.uint8)

    #######
    ####### ID_S1_EX1 END #######     
    
    return img_range_intensity

# front camera image to associate the point cloud data with camera data and justify the identification in point cloud.
def frame_camera_image(frame, camera_name):
    image = [obj for obj in frame.images if obj.name == camera_name][0]
    image = np.array(Image.open(io.BytesIO(image.image)))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    dimensions = (int(image.shape[1] * 0.5), int(image.shape[0] * 0.5))
    resized = cv2.resize(image, dimensions)
    return cv2.imshow('FRONT-CAMERA_IMAGE', resized)



# create birds-eye view of lidar data
def bev_from_pcl(lidar_pcl, configs):

    # remove lidar points outside detection area and with too low reflectivity
    mask = np.where((lidar_pcl[:, 0] >= configs.lim_x[0]) & (lidar_pcl[:, 0] <= configs.lim_x[1]) &
                    (lidar_pcl[:, 1] >= configs.lim_y[0]) & (lidar_pcl[:, 1] <= configs.lim_y[1]) &
                    (lidar_pcl[:, 2] >= configs.lim_z[0]) & (lidar_pcl[:, 2] <= configs.lim_z[1]))
    lidar_pcl = lidar_pcl[mask]

    # shift level of ground plane to avoid flipping from 0 to 255 for neighboring pixels
    lidar_pcl[:, 2] = lidar_pcl[:, 2] - configs.lim_z[0]

    # convert sensor coordinates to bev-map coordinates (center is bottom-middle)
    ####### ID_S2_EX1 START #######
    #######

    # bev-map discretization by dividing x-range by the bev-image height (see configs)
    bev_discret = (configs.lim_x[1] - configs.lim_x[0]) / configs.bev_height
    # Tansform all metrix x-coordinates into bev-image coordinates
    lidar_pcl_cpy = np.copy(lidar_pcl)
    lidar_pcl_cpy[:, 0] = np.int_(np.floor(lidar_pcl_cpy[:, 0] / bev_discret))

    # perform the same operation as in step 2 for the y-coordinates but make sure that no negative bev-coordinates occur
    lidar_pcl_cpy[:, 1] = np.int_(np.floor(lidar_pcl_cpy[:, 1] / bev_discret) + (configs.bev_width + 1) / 2)
    lidar_pcl_cpy[:, 1] = np.where(lidar_pcl_cpy[:, 1] < 0, 0, lidar_pcl_cpy[:, 1])
    lidar_pcl_cpy[:, 2] = lidar_pcl_cpy[:, 2] - configs.lim_z[0]

    # visualize point-cloud
    show_pcl(lidar_pcl_cpy)

    #######
    ####### ID_S2_EX1 END #######     
    
    # Compute intensity layer of the BEV map
    ####### ID_S2_EX2 START #######     
    #######

    # create a numpy array filled with zeros which has the same dimensions as the BEV map
    intensity_map = np.zeros((configs.bev_height + 1, configs.bev_width + 1))

    # re-arrange elements in lidar_pcl_cpy by sorting first by x, then y, then -z
    lidar_pcl_cpy[lidar_pcl_cpy[:, 3] > 1.0, 3] = 1.0
    intensity_idx = np.lexsort((-lidar_pcl_cpy[:, 2], lidar_pcl_cpy[:, 1], lidar_pcl_cpy[:, 0]))
    lidar_pcl_intensity = lidar_pcl_cpy[intensity_idx]

    # extract all points with identical x and y such that only the top-most z-coordinate is kept
    ## also, store the number of points per x,y-cell in a variable named "counts" for use in the next task
    _, indices = np.unique(lidar_pcl_intensity[:, 0:2], axis=0, return_index=True)
    lidar_intensity_channel = lidar_pcl_intensity[indices]

    # assign the intensity value of each unique entry in lidar_top_pcl to the intensity map
    ## make sure that the intensity is scaled in such a way that objects of interest (e.g. vehicles) are clearly visible
    ## also, make sure that the influence of outliers is mitigated by normalizing intensity on the difference between the max. and min. value within the point cloud
    intensity_map[np.int_(lidar_intensity_channel[:, 0]), np.int_(lidar_intensity_channel[:, 1])] = lidar_intensity_channel[:,3] / (np.amax(lidar_intensity_channel[:, 3]) - np.amin(lidar_intensity_channel[:, 3])) + 0.0001

    # visualize the intensity map using OpenCV to make sure that vehicles separate well from the background
    img_intensity = intensity_map * 256
    img_intensity = img_intensity.astype(np.uint8)

    ''' 
    while True:
        cv2.imshow('img_intensity', img_intensity)
        if cv2.waitKey(10) & 0xff == 27:
            break
    cv2.destroyAllWindows()
    '''

    #######
    ####### ID_S2_EX2 END #######

    # Compute height layer of the BEV map
    ####### ID_S2_EX3 START #######
    #######

    lidar_pcl_top = lidar_intensity_channel

    height_map = np.zeros((configs.bev_height + 1, configs.bev_width + 1))

    # assign the height value of each unique entry in lidar_top_pcl to the height map
    ## make sure that each entry is normalized on the difference between the upper and lower height defined in the config file
    ## use the lidar_pcl_top data structure from the previous task to access the pixels of the height_map
    height_idx = np.lexsort((-lidar_pcl_cpy[:, 2], lidar_pcl_cpy[:, 1], lidar_pcl_cpy[:, 0]))
    lidar_pcl_height = lidar_pcl_cpy[height_idx]

    _, idx_height_unique = np.unique(lidar_pcl_height[:, 0:2], axis=0, return_index=True)
    lidar_pcl_height = lidar_pcl_height[idx_height_unique]

    height_map[np.int_(lidar_pcl_height[:, 0]), np.int_(lidar_pcl_height[:, 1])] = lidar_pcl_height[:, 2] / float(np.abs(configs.lim_z[1] - configs.lim_z[0]))

    # visualize the height map using OpenCV to make sure that vehicles separate well from the background
    img_height = height_map * 256
    img_height = img_height.astype(np.uint8)
    '''
    while True:
        cv2.imshow('img_height', img_height)
        if cv2.waitKey(10) & 0xff == 27:
            break
    cv2.destroyAllWindows()
    '''

    #######
    ####### ID_S2_EX3 END #######

    # Compute density layer of the BEV map
    density_map = np.zeros((configs.bev_height + 1, configs.bev_width + 1))
    _, _, counts = np.unique(lidar_pcl_cpy[:, 0:2], axis=0, return_index=True, return_counts=True)
    normalizedCounts = np.minimum(1.0, np.log(counts + 1) / np.log(64))
    density_map[np.int_(lidar_pcl_top[:, 0]), np.int_(lidar_pcl_top[:, 1])] = normalizedCounts

    img_density = density_map * 256
    img_density = img_density.astype(np.uint8)
    '''    
    while True:
        cv2.imshow('density_channels', img_density)
        if cv2.waitKey(10) & 0xff == 27:
            break
    cv2.destroyAllWindows()
    '''
    # assemble 3-channel bev-map from individual maps
    bev_map = np.zeros((3, configs.bev_height, configs.bev_width))
    bev_map[2, :, :] = density_map[:configs.bev_height, :configs.bev_width]  # r_map
    bev_map[1, :, :] = height_map[:configs.bev_height, :configs.bev_width]  # g_map
    bev_map[0, :, :] = intensity_map[:configs.bev_height, :configs.bev_width]  # b_map

    # expand dimension of bev_map before converting into a tensor
    s1, s2, s3 = bev_map.shape
    bev_maps = np.zeros((1, s1, s2, s3))
    bev_maps[0] = bev_map

    bev_maps = torch.from_numpy(bev_maps)  # create tensor from birds-eye view
    input_bev_maps = bev_maps.to(configs.device, non_blocking=True).float()

    return input_bev_maps


