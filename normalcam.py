import cv2
import numpy as np

# Default, using realsense
#import realsense

# To open default camera using default backend
#cap = cv2.VideoCapture(0)

# To open video file instead
cap = cv2.VideoCapture('test_new.avi')

# To know the width and height of video file
x_max = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
y_max = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print("x: {0}, y: {1}".format(x_max, y_max))

# Background Subtraction = using MOG2 algorithm
backSub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=True)

# Kernel for Filters
kernel = np.ones((5,5),np.uint8)

# Capture first frame
# ret: Returns true if succesfully grabs the next frame from video file or capturing device, frame: Returns the grabbed video frame
ret, frame = cap.read()

# Initialise Room as Not Occupied
text = "Room is: Unoccupied"

# Record Coordinates
coord = []

# Inclusion Zone: define area of box to detect one person
# Drawing: cv2.rectangle(img, pt1, pt2, color, thickness)
# (0,0) is top left corner
# Create black image
# np.full_like(a, fill_value, dtype=None, order='K', subok=True, shape=None)
black = np.full_like(frame, (0,0,0))
    
# Create white image as base
white = np.full_like(frame, (1,1,1),dtype=np.float32)
    
# Define rectangle as "hole" and draw as black filled on the white base mask
pt1 = (5,260)
pt2 = (400,470) #can try (395,295)
mask = cv2.rectangle(white, pt1, pt2, (0, 0, 0), -1)
cv2.imshow("Mask", mask)
stabilize_countdown = 30

record = []
current = 0
p = []
startpoint = y_max - 50
endpoint = y_max - 20

frame_no = 0

while True:
#while(cap.isOpened()):

    frame_no += 1

    if stabilize_countdown > 0:
 	    stabilize_countdown = stabilize_countdown - 1
 	    continue
    
    ret, frame = cap.read()

    if ret == False:
        break
    
    # UI
    # Adding a timestamp (frame) on video
    # cv2.rectangle(image, start_point, end_point, color, thickness)
    cv2.rectangle(frame, (10, 2), (100, 20), (255, 255, 255), -1)
    # cv2.putText(image, text, org, font, fontScale, color[, thickness[, lineType[, bottomLeftOrigin]]])
    cv2.putText(frame, str(cap.get(cv2.CAP_PROP_POS_FRAMES)), (15, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0))
    # Adding a "Occupied" or "Unoccupied" message
    cv2.putText(frame, text, (150, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    # Blue Inclusion Zone rectangle
    cv2.rectangle(frame, pt1, pt2, (255, 0, 0), 2)

    # Combine black and white images
    #cv.add(src1, src2[, dst[, mask[, dtype]]])
    new_frame = cv2.add(frame*(1-mask),black*mask).astype(np.uint8)

    # Apply background subtraction to frame
    fg_mask = backSub.apply(new_frame)

    # Filter foreground: Noise removal
    # Threshold: Black & White
    ret,fg_mask = cv2.threshold(fg_mask,127,255,cv2.THRESH_BINARY)
    # Median Blur: Removes Shadow
    fg_mask = cv2.medianBlur(fg_mask,5)
    # Erosion: fg_mask = cv2.erode(fg_mask,kernel,iterations = 1)
    # Dilation: fg_mask = cv2.dilate(fg_mask,kernel,iterations = 1)

    # 1. Object Detection and Tracking
    # Find the index of the largest contour and draw bounding box
    # Contours = curve joining all the continuous points (along the boundary), having same color or intensity
    # cv.findContours(image, mode, method[, contours[, hierarchy[, offset]]])
    # Lookup "Contours Features"
    fg_mask_box = fg_mask
    print(fg_mask_box)
    contours, hierarchy = cv2.findContours(fg_mask_box, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2:] #can try CHAIN_APPROX_TC89_L1, CHAIN_APPROX_TC89_KCOS
    areas = [cv2.contourArea(c) for c in contours]

    # If there are no contours
    if len(areas) < 1:
        # Display the resulting frame
        cv2.imshow('Video',frame)
 
        # If "q" is pressed on the keyboard, 
        # exit this loop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
 
        # Go to the top of the while loop
        continue
 
    else:
        # Find the largest moving object in the image
        max_index = np.argmax(areas)

    # Draw the bounding box
    cnt = contours[max_index]
    x,y,w,h = cv2.boundingRect(cnt)
    #cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),3)

    # Draw circle in the center of the bounding box
    x2 = x + int(w/2)
    y2 = y + int(h/2)
    cv2.circle(frame,(x2,y2),4,(0,255,0),-1)
 
    # Print the centroid coordinates (we'll use the center of the bounding box) on the image
    #text = "x: " + str(x2) + ", y: " + str(y2)
    #cv2.putText(frame, text, (x2 - 10, y2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    prev = current 
    current = y2 
    if current > prev:
        record.append("increase")
    elif current < prev:
        record.append("decrease")
    
    if (len(record) > 4):
        for i in range (5):
            p.append(record[len(record)-(i+1)]) #last to 5th last
        # if now is near the door, and most of the previous few points are decreasing (coming nearer)
        if (current > endpoint):
            if (p.count("decrease") > 3):
                #print("in")
                text = "Room is: Occupied"
                record.clear()
                record.append("occu")
        if (current < startpoint):
            if record[0] == "occu" and (p.count("increase") > 3):
                #print ("out")
                text = "Room is: Unoccupied"
                record.clear()

    # Displaying videos
    cv2.imshow("Video", frame)
    cv2.imshow("BG Sub", fg_mask)

    # waitKey(0) will display the window infinitely until any keypress (it is suitable for image display).
    # waitKey(1) will display a frame for 1 ms, after which display will be automatically closed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print(frame_no)
        break

# When everything is done, release the capture
cap.release()
cv2.destroyAllWindows()