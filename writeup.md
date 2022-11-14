# Project Description and Overview
Under this project the main aim is to detect the object in the lidar point cloud. Conventionally the object detection is done on image data through computer vision techniques but also that must be confirmed with the use of other sensor data as well. The environmental condition and the camera limited range capabilities has to be countered with the help of sensor fusion. The lidar sensor generates a high dimensional point cloud through the reflected rays from the objects and provides a reliable data to work on. 

Two different object detection models fpn-resnet  and darknet (YOLOv4) are used in this project and are compared through performance evaluation method called mean average precision(mAP). The results shows that the darknet architecture performs better in terms of average loss. 

## Range image in dataset
-  lidar data is stored in the form of range image in waymo open dataset. Figure shows the range based on intensity of pixels of the image. The brighter pixels are the objects nearer and darker refers to distant objects.
 
##### Range Image
![range image](https://user-images.githubusercontent.com/84092636/201634641-33971eec-1fcd-48c0-8259-69d491c2d850.png)


The dataset is taken from real-world dataset by waymo open dataset that has the lidar data in the form of range images. This range image data is converted into a high dimensional point cloud and the objects are easily visible inside the point cloud. The figure below has a highlight that shows the appearance of the various parts of the vehicle the lidar was able to detect such as wheels, side mirrors, windshield, roofs and hood contours. It is clearly seen that the near range vehicles are visible completely and as the range increases the parts of the vehicles in detection are obstructed from the vehicle in front.
- Image on top is the point cloud view when visualizing the data in open3d and also the image below shows zoomed view showing vehicle contours and other object such as pedestrain and light poles.

![combined view photo](https://user-images.githubusercontent.com/84092636/201635785-e5721e57-6d64-4a02-b61e-330fceb38d6e.jpg)

The images below show the birds eye view of the point cloud after converting the point cloud into 2d. It consists of 3 channels – intensity, height and density. The first image is density channel. The second image shows the height channel and most rays reflected from the vehicle roofs showing roof contours. The third image shows the intensity channel of the processed 2d image from range images.

![channels top view](https://user-images.githubusercontent.com/84092636/201637735-9b546d9d-9687-437c-ac90-24d868451014.jpg)

The video shows the combined image of the camera data and lidar bev maps. The green boxes are the detected boxes in the camera image and the red boxes are the detection in lidar point cloud. The detections are performed through two pre trained network s - darknet and resnet.

https://user-images.githubusercontent.com/84092636/201655748-92396a10-0b13-4121-9317-e861c9553c1c.mp4

The model is then evaluated using precision- recall matrix and mean PR value is calculated for 200 frames of data. The average mAP for the darknet is seen better compared to the resnet architecture. The figure shows the mAP values for darknet architecture with precision of 0.98 and recall value of 0.88.

![PR graphs](https://user-images.githubusercontent.com/84092636/201658198-7229c21c-d1d3-4a48-8b35-fb734625b213.png)
