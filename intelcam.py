import pyrealsense2 as rs
import numpy as np
import cv2

# Create a pipeline
pipeline = rs.pipeline()

# Create a config and configure the pipeline to stream different resolutions of color and depth streams
config = rs.config()

# Get device product line for setting a supporting resolution
pipeline_wrapper = rs.pipeline_wrapper(pipeline)
pipeline_profile = config.resolve(pipeline_wrapper)
device = pipeline_profile.get_device()
device_product_line = str(device.get_info(rs.camera_info.product_line))

config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

if device_product_line == 'L500':
    config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 30)
else:
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Start streaming
profile = pipeline.start(config)

# Getting the depth sensor's depth scale (see rs-align example for explanation)
depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()
print("Depth Scale is: " , depth_scale)

# We will be removing the background of objects more than clipping_distance_in_meters meters away
max_dist = 1 #1 meter
#max_dist = clipping_distance_in_meters / depth_scale
#print(max_dist)

# Create an align object
# rs.align allows us to perform alignment of depth frames to others frames
# The "align_to" is the stream type to which we plan to align depth frames.
align_to = rs.stream.color
align = rs.align(align_to)

# Declaring some temp variables
dist_record = 0
points = 20
count = 0
record = []
count_frame = 0
endpoint = 0.5
startpoint = 0.7
current = 0
text = "Room is: Unoccupied"
p = [] 

# Streaming loop
try:
    while True:
        # Get frameset of color and depth
        frames = pipeline.wait_for_frames()
        
        # frames.get_depth_frame() is a 640x360 depth image
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()
        x = int(depth_frame.get_width()/5) ##########################
        y = int(depth_frame.get_height()/2)
        #print(x, y)
        #x_point = [x, x*2, x*3] if x is divided by 4

        dist_center = depth_frame.get_distance(x,y)
        #print("center: ", dist_center)

        # To get a a few points near the fixed point to find a mean (for stability?)
        for j in range(points):
            dist_temp = depth_frame.get_distance(x+j, y)
            if (dist_temp != 0) and (dist_temp < max_dist):
                dist_record += dist_temp
                count += 1
            dist_temp = depth_frame.get_distance(x+j, y+j)
            if (dist_temp != 0) and (dist_temp < max_dist):
                dist_record += dist_temp
                count += 1
            dist_temp = depth_frame.get_distance(x, y+j)
            if (dist_temp != 0) and (dist_temp < max_dist):
                dist_record += dist_temp
                count += 1

        if count != 0:
            mean = dist_record / count
            count = 0
            dist_record = 0
            print("mean dist: ", mean)
            #record.append(mean)

            prev = current 
            current = mean
            if current > prev:
                record.append("further")
            elif current < prev:
                record.append("nearer")
            
            if (len(record) > 4):
                for i in range (5):
                    p.append(record[len(record)-(i+1)]) #last to 5th last
                # if now is near the door, and most of the previous few points are decreasing (coming nearer)
                if (current < endpoint):
                    if (p.count("nearer") > 3):
                        #print("in")
                        text = "Room is: Occupied"
                        record.clear()
                        record.append("occu")
                if (current > startpoint):
                    if record[0] == "occu" and (p.count("further") > 3):
                        #print ("out")
                        text = "Room is: Unoccupied"
                        record.clear()
        
        #depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        
        cv2.circle(color_image,(x,y),4,(0,0,255),-1)
        cv2.putText(color_image, text, (150, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow("Camera", color_image)

        key = cv2.waitKey(1)
        # Press esc or 'q' to close the image window
        if key & 0xFF == ord('q') or key == 27:
            cv2.destroyAllWindows()
            break
        
finally:
    pipeline.stop()