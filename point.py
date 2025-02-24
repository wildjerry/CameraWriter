# https://chuoling.github.io/mediapipe/solutions/hands.html

import numpy as np

import cv2

import matplotlib.pyplot as plt

import mediapipe as mp
drawingModule = mp.solutions.drawing_utils
handsModule = mp.solutions.hands

from time import sleep

hands = handsModule.Hands(static_image_mode=False, min_detection_confidence=0.7, min_tracking_confidence=0.7, max_num_hands=2)

def handle_keypress(event):
    global exit_key_pressed
    if event.key in ('q', 'Q'):
        print('keypress was q or Q')
        exit_key_pressed = True

plt.gcf().canvas.mpl_connect('key_press_event', handle_keypress)

def show_cv2_frame_matplotlib(frame):
    if exit_key_pressed:
        plt.close()
        exit()
    # Convert the frame from BGR (OpenCV format) to RGB (matplotlib format)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    plt.imshow(frame_rgb)
    plt.axis('off')  # Hide the axis for a cleaner view
    plt.show(block=False)  # Show the frame without blocking the main program
    plt.pause(0.001)  # Short pause to allow the figure to refresh

def vector(landmark):
    return np.array([landmark.x, landmark.y, landmark.z])

def finger_up_amount(landmarks):
    '''Return a value from 0 to 1'''
    points = [vector(l) for l in landmarks]
    lower_segment = points[1] - points[0]
    upper_segment = points[-1] - points[-2]
    position = np.dot(lower_segment, upper_segment)/(np.linalg.norm(lower_segment) * np.linalg.norm(upper_segment))
    return (position/2) + 0.5

vs = cv2.VideoCapture(0)

sleep(2.0)

pen_down = False
curves = []

while True:
    plt.clf()

    ret, frame = vs.read()  # Capture a frame
    frame = cv2.flip(frame,1)

    if not ret:
        print('no image; exiting')
        break  # Exit if the frame could not be captured

    results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
 
    if results.multi_hand_landmarks != None:
        #print(results.multi_handedness)
        for handLandmarks, hand in zip(results.multi_hand_landmarks, results.multi_handedness):
            thumb_up_amount = finger_up_amount(handLandmarks.landmark[2:5])
            index_up_amount = finger_up_amount(handLandmarks.landmark[5:9])
            drawingModule.draw_landmarks(frame, handLandmarks, handsModule.HAND_CONNECTIONS)
            height, width, _ = frame.shape
            x_coordinates = [landmark.x for landmark in handLandmarks.landmark]
            y_coordinates = [landmark.y for landmark in handLandmarks.landmark]
            text_x = int(min(x_coordinates) * width)
            text_y = int(min(y_coordinates) * height) - 10
            '''
            cv2.putText(frame, f"{index_up_amount=}",
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
                pass

    for curve in curves:
        for i in range(len(curve)-1):
            cv2.line(frame, curve[i], curve[i+1], (0,200,0), 10)

    cv2.imshow('Test hand', frame)

    if cv2.waitKey(1) == 27:
        break