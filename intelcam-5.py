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

# Create an align object
# rs.align allows us to perform alignment of depth frames to others frames
# The "align_to" is the stream type to which we plan to align depth frames.
align_to = rs.stream.color
align = rs.align(align_to)

# Declaring some temp variables
max_dist = 1.5
dist_record = 0
points = 20
count = 0
record = []
count_frame = 0
current = 0
text = "Room is: Unoccupied"
p = []
black = 0 #153 for grey
temp = 0
x, y = 0, 0
number = str("")

# These values would be configured depending on location/angle of camera
endpoint = 0.4
startpoint = 0.5

backSub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=True)

# Countdown for 30 frames (initial stabilisation) 
stabilize_countdown = 30

# Countdown for inactivity, no activity for 30 minutes
# Approximately 20 frames per second
inactivity_max = 30 * 60 * 20
inactivity_count = 0


# Streaming loop
try:
    while True:

        if stabilize_countdown > 0:
            stabilize_countdown = stabilize_countdown - 1
            continue
            
        change = False

        # Get frameset of color and depth and aligning depth frame to color frame
        frames = pipeline.wait_for_frames()
        frames = align.process(frames)
        
        # frames.get_depth_frame() is a 640x360 depth image
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()

        #depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        frame = color_image

        #cv2.imshow("Original", color_image)

        cv2.putText(frame, text, (150, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Removing background when there is no motion
        fg_mask = backSub.apply(color_image)
        # Filter foreground: Noise removal (not needed)
        #ret,fg_mask = cv2.threshold(fg_mask,127,255,cv2.THRESH_BINARY) #black & white
        #fg_mask = cv2.medianBlur(fg_mask,5) #removes shadow
        cv2.imshow("Background", fg_mask)

        contours, hierarchy = cv2.findContours(fg_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2:] #can try CHAIN_APPROX_TC89_L1, CHAIN_APPROX_TC89_KCOS
        areas = [cv2.contourArea(c) for c in contours]

        # If there are no contours
        if len(areas) < 1:
            # Display the resulting frame (no change)
            cv2.imshow('Video',frame)

            # Starting counting inactivity
            inactivity_count += 1

            # Reset to Unoccupied if there is no activity
            if inactivity_count == inactivity_max:
                text = "Room is: Unoccupied"

            # If "q" is pressed on the keyboard, exit this loop
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Go to the top of the while loop
            continue

        else:
            # Find the largest moving object in the image
            max_index = np.argmax(areas)

            # If too small, ignore
            if areas[max_index] < 2000:
                cv2.imshow('Video',frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue

            # Reset inactivity counter
            inactivity_count = 0

        # Draw the bounding box
        cnt = contours[max_index]
        x2,y2,w,h = cv2.boundingRect(cnt)
        #cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),3)

        # Draw circle in the center of the bounding box
        x = x2 + int(w/2)
        y = y2 + int(h/2)
        #cv2.circle(frame,(x,y),4,(0,255,0),-1)

        # Print the centroid coordinates (we'll use the center of the bounding box) on the image
        #text = "x: " + str(x2) + ", y: " + str(y2)
        #cv2.putText(frame, text, (x2 - 10, y2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        dist = depth_frame.get_distance(x,y)
        #print(dist)

        # if more than 1.5m away, ignore
        if dist > max_dist:
            cv2.imshow('Video',frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue

        # For stability?, getting mean of 3 frames
        if count <= 3:
            dist_record += dist 
            count += 1

        else:
            mean = round (dist_record / count, 2)
            count = 0
            dist_record = 0
            # print("dist: ", mean)
            if mean > 0:
                #record.append(mean)
                #print(record)
                number = str(mean)

            prev = current 
            current = mean
            if current > prev:
                record.append("up")
            elif current < prev:
                record.append("down")
            print(mean)
            print(record)
            
            if (len(record) > 3):

                if (current < endpoint) and (record.count("down") > 3):
                    text = "Room is: Occupied"
                    record.clear()
                    record.append("occu")
                    change = True

                if (current > startpoint) and (record[0] == "occu") and (record.count("up") > 2):
                    text = "Room is: Unoccupied"
                    record.clear()
                    change = True
                
            if (len(record) > 7):
                if record[0] == "occu":
                    del record[1]
                else:
                    del record[0]


        if change:
            print("\nTHERE IS A CHANGE ---->", text)

        cv2.putText(frame, number, (150, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.circle(frame,(x,y),4,(0,0,255),-1)
        cv2.imshow('Video', frame)

        key = cv2.waitKey(1)
        # Press esc or 'q' to close the image window
        if key & 0xFF == ord('q') or key == 27:
            cv2.destroyAllWindows()
            break
        
finally:
    pipeline.stop()