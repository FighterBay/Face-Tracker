import numpy as np
import cv2
import thread
import time
import pigpio
import read_PWM

def find_quadrant(x,y):
    if -15 <= x <= 15:
        if -15 <= y <= 15:
            return 0 #Copter is facing the center.
    if x>0:
        if y>0:
            return 1
        if y<0:
            return 4
    else:
        if y>0:
            return 2
        if y<0:
            return 3
                               

channels = []
channels2 = []
read_pins = [23,24,25,8,5]      #R,P,T,Y and 5th is for the toggle of this program
out_pins = [26,19,13,6]         #R,P,T,Y out

def poll_RC():
    global channels
    channels_obj = []
    for read_pin in read_pins:
        channels_obj.append(read_PWM.reader(pi, read_pin))

    for ch_obj in channels_obj:
        channels.append(0)

    while True:
        ctr = 0
        for ch_obj in channels_obj:
            val = int(ch_obj.pulse_width()+0.5)
            channels[ctr] = val #valmap(val,channels_min[ctr],channels_max[ctr],base_pwm,max_pwm)
            ctr = ctr + 1
        time.sleep(1/50)

thread.start_new_thread(poll_RC,())

def forward_RC():
    global channels
    channels3 = []
    while True:
        ctr = 0
        if channels[4] > 1700 and channels2[2] != 0:
            
            channels3 = channels2
        else:
            channels3 = channels
            
        for out in out_pins:
            pi.set_servo_pulsewidth(out,channels3[ctr])
            ctr = ctr + 1
        time.sleep(1/50)
        
thread.start_new_thread(forward_RC,())

cap = cv2.VideoCapture(0)                            
face_cascade = cv2.CascadeClassifier('/Users/Anand/Desktop/UAV/face_tracker/haarcascade_frontalface_default.xml')
img, frame = cap.read()

height, width, channels = img.shape
cen_x = height/2
cen_y = width/2

#if quadrant is 1 then roll a little right and throttle a little up
#if quadrant is 2 then roll a little left and throttle a little up
#if quadrant is 3 then roll a little left and throttle a little down
#if quadrant is 4 then roll a little right and throttle a little down

prev_toggle_pwm = channels[4]
rough_area = 0
back_forward = 0 # 0 means do nothing, 1 means go back, 2 means go forward
while True:
    img, frame = cap.read()
    if abs(prev_toggle_pwm - channels[4]) > 300 and channels[4] > 1700:
        channels2 = channels
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        if len(faces) == 1:
            for (x,y,w,h) in faces:
                rough_area = w*h


    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    if len(faces) == 1:
        for (x,y,w,h) in faces:
            cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)

            roi_train = img[y:y+h, x:x+w]
            localised_x = (x + (w/2)) - cen_x
            localised_y = (y + (h/2)) - cen_y
            quad = find_quadrant(localised_x,localised_y)
            
            if 0.9*rough_area <= w*h <= 1.1*rough_area:
                back_forward = 0
                
            if 0.9*rough_area > w*h:
                back_forward = 2
                channels2[1] += 5
                
            if w*h > 1.1*rough_area:
                back_forward = 1
                channels2[1] -= 5
                        
            if quad == 1:
                channels2[0] +=  5
                channels2[2] += 5
            elif quad == 2:
                channels2[0] -=  5
                channels2[2] += 5
            elif quad == 3:
                channels2[0] -=  5
                channels2[2] -= 5
            else:
                channels2[0] +=  5
                channels2[2] -= 5    
                        
                
            

