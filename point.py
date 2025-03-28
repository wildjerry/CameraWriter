# https://chuoling.github.io/mediapipe/solutions/hands.html

import numpy as np

import cv2

import mediapipe as mp
drawingModule = mp.solutions.drawing_utils
handsModule = mp.solutions.hands

from time import sleep

import shapely

from threading import Thread
from _thread import interrupt_main

import queue

import cloud

db_con = cloud.db_connection()
hands = handsModule.Hands(static_image_mode=False, min_detection_confidence=0.7, min_tracking_confidence=0.7, max_num_hands=2)

def handle_keypress(event):
    global exit_key_pressed
    if event.key in ('q', 'Q'):
        print('keypress was q or Q')
        exit_key_pressed = True

def vector(landmark):
    return np.array([landmark.x, landmark.y, landmark.z])

def finger_alignment_amount(landmarks):
    '''Return a value from 0 to 1'''
    points = [vector(l) for l in landmarks]
    lower_segment = points[1] - points[0]
    upper_segment = points[-1] - points[-2]
    position = np.dot(lower_segment, upper_segment)/(np.linalg.norm(lower_segment) * np.linalg.norm(upper_segment))
    return (position/2) + 0.5

def in_bounds(point, bounds):
    sP = shapely.Point(point[0],point[1])
    shape = shapely.Polygon(bounds)
    return shape.contains(sP)

frameQueue = queue.Queue(maxsize=2)

def frame_shower():
    while True:
        frame = frameQueue.get(block=True)
        cv2.imshow('Test hand', frame)

        if cv2.waitKey(1) == 27:
            break

    interrupt_main()

frame_show_thread = Thread(target=frame_shower)
frame_show_thread.daemon = True
frame_show_thread.start()

vs = cv2.VideoCapture(0)

sleep(2.0)

pen_down = False
curves = []

def debug_t():
    while True:
        print(f'{type(curves)=}')
        print(f'{curves=}')
        sleep(1)
debug_thread = Thread(target=debug_t)
debug_thread.daemon = True
#debug_thread.start()

while True:

    ret, frame = vs.read()  # Capture a frame
    frame = cv2.flip(frame,1)

    if not ret:
        print('no image; exiting')
        break  # Exit if the frame could not be captured

    results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    #https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker
    if results.multi_hand_landmarks != None:
        #print(results.multi_handedness)
        for handLandmarks, hand in zip(results.multi_hand_landmarks, results.multi_handedness):
            thumb_up_amount = finger_alignment_amount(handLandmarks.landmark[2:5])
            index_up_amount = finger_alignment_amount(handLandmarks.landmark[5:9])
            middle_up_amount = finger_alignment_amount(handLandmarks.landmark[9:13])
            ring_up_amount = finger_alignment_amount(handLandmarks.landmark[13:17])
            pinkie_up_amount = finger_alignment_amount(handLandmarks.landmark[17:21])

            thumb_hand_alignment = finger_alignment_amount(handLandmarks.landmark[3:5]+handLandmarks.landmark[7:9])

            drawingModule.draw_landmarks(frame, handLandmarks, handsModule.HAND_CONNECTIONS)
            height, width, _ = frame.shape
            x_coordinates = [landmark.x for landmark in handLandmarks.landmark]
            y_coordinates = [landmark.y for landmark in handLandmarks.landmark]
            text_x = int(min(x_coordinates) * width)
            text_y = int(min(y_coordinates) * height) - 10
            '''
            cv2.putText(frame, f"{thumb_hand_alignment=}",
                (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX,
                1, (88, 205, 54), 1, cv2.LINE_AA)
            '''
            if hand.classification[0].label == "Right" and hand.classification[0].score >= 0.9:
                pen_was_down = pen_down
    
                if index_up_amount > 0.95:
                    pen_down = True
                if index_up_amount < 0.85:
                    pen_down = False
                
                index_tip_coords = (
                    int(handLandmarks.landmark[8].x * width), int(handLandmarks.landmark[8].y * height)
                )

                if pen_down and pen_was_down:
                    curves[-1].append( index_tip_coords )
                
                if pen_down and not pen_was_down:
                    curves.append( [ index_tip_coords ] )

            if hand.classification[0].label == "Left" and hand.classification[0].score >= 0.9:
                full_up = min(thumb_up_amount, index_up_amount, middle_up_amount, ring_up_amount, pinkie_up_amount)

                if full_up > 0.85 and thumb_hand_alignment > 0.95:
                    boundary = [ ( int(handLandmarks.landmark[i].x*width), int(handLandmarks.landmark[i].y*height) ) for i in [0,1,2,3,4,8,12,16,20,19,18,17]]

                    for i in range(len(boundary)-1):
                        cv2.line(frame, boundary[i], boundary[i+1], (200, 0, 200), 5)
                    cv2.line(frame, boundary[0], boundary[-1], (200, 0, 200), 5) #to close the curve
                    old_curves = curves
                    curves = [ [] ]
                    for i in range(len(old_curves)):
                        current_curve = []
                        for j in range(len(old_curves[i])):
                            if not in_bounds(old_curves[i][j], boundary):
                                current_curve.append(old_curves[i][j])
                            else:
                                if len(current_curve) > 1:
                                    curves.append(current_curve)
                                current_curve = []

                        if len(current_curve)>1:
                            curves.append(current_curve)
    #curve_count = 0
    for curve in curves:
        #curve_count+=1
        for i in range(len(curve)-1):
            cv2.line(frame, curve[i], curve[i+1], (200,15,15), 10)
    
    for curve_set in db_con.otherPaths:
        for curve in curve_set:
            for i in range(len(curve)-1):
                cv2.line(frame, curve[i], curve[i+1], (15,15,200), 10)
            
    #cv2.putText(frame, f"{curve_count=}", (30,30),cv2.FONT_HERSHEY_DUPLEX, 1, (88, 205, 54), 1, cv2.LINE_AA)
    db_con.push_updated_paths(curves)
    frameQueue.put(frame, block=True)