# Imports
import cv2
import mediapipe as mp
import pyautogui
import math
from enum import IntEnum
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from google.protobuf.json_format import MessageToDict
import screen_brightness_control as sbcontrol

pyautogui.FAILSAFE = False
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# Gesture Encodings 
class Gest(IntEnum):
    FIST = 0
    PINKY = 1
    RING = 2
    MID = 4
    LAST3 = 7
    INDEX = 8
    FIRST2 = 12
    LAST4 = 15
    THUMB = 16    
    PALM = 31
    # Extra Mappings
    V_GEST = 33
    TWO_FINGER_CLOSED = 34
    PINCH_MAJOR = 35
    PINCH_MINOR = 36

# Multi-handedness Labels
class HLabel(IntEnum):
    MINOR = 0
    MAJOR = 1

# Convert Mediapipe Landmarks to recognizable Gestures
class HandRecog:
    def __init__(self, hand_label):
        self.finger = 0
        self.ori_gesture = Gest.PALM
        self.prev_gesture = Gest.PALM
        self.frame_count = 0
        self.hand_result = None
        self.hand_label = hand_label

    def update_hand_result(self, hand_result):
        self.hand_result = hand_result

    def get_signed_dist(self, point):
        sign = -1
        if self.hand_result.landmark[point[0]].y < self.hand_result.landmark[point[1]].y:
            sign = 1
        dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x)**2
        dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y)**2
        dist = math.sqrt(dist)
        return dist*sign

    def get_dist(self, point):
        dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x)**2
        dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y)**2
        dist = math.sqrt(dist)
        return dist

    def get_dz(self, point):
        return abs(self.hand_result.landmark[point[0]].z - self.hand_result.landmark[point[1]].z)

    # Function to find Gesture Encoding using current finger_state.
    # Finger_state: 1 if finger is open, else 0
    def set_finger_state(self):
        if self.hand_result is None:
            return

        points = [[8,5,0],[12,9,0],[16,13,0],[20,17,0]]
        self.finger = 0
        self.finger = self.finger | 0 #thumb
        for idx, point in enumerate(points):
            dist = self.get_signed_dist(point[:2])
            dist2 = self.get_signed_dist(point[1:])
        
            try:
                ratio = round(dist/dist2, 1)
            except ZeroDivisionError:
                ratio = round(dist/0.01, 1)

            self.finger = self.finger << 1
            if ratio > 0.5:
                self.finger = self.finger | 1

    # Handling Fluctations due to noise
    def get_gesture(self):
        if self.hand_result is None:
            return Gest.PALM

        current_gesture = Gest.PALM
        if self.finger in [Gest.LAST3, Gest.LAST4] and self.get_dist([8,4]) < 0.05:
            if self.hand_label == HLabel.MINOR:
                current_gesture = Gest.PINCH_MINOR
            else:
                current_gesture = Gest.PINCH_MAJOR

        elif Gest.FIRST2 == self.finger:
            point = [[8,12],[5,9]]
            dist1 = self.get_dist(point[0])
            dist2 = self.get_dist(point[1])
            ratio = dist1/dist2
            if ratio > 1.7:
                current_gesture = Gest.V_GEST
            else:
                if self.get_dz([8,12]) < 0.1:
                    current_gesture = Gest.TWO_FINGER_CLOSED
                else:
                    current_gesture = Gest.MID
        
        else:
            current_gesture = self.finger
    
        if current_gesture == self.prev_gesture:
            self.frame_count += 1
        else:
            self.frame_count = 0

        self.prev_gesture = current_gesture

        if self.frame_count > 4:
            self.ori_gesture = current_gesture
        return self.ori_gesture

# Executes commands according to detected gestures
class Controller:
    tx_old = 0
    ty_old = 0
    trial = True
    flag = False
    grabflag = False
    pinchmajorflag = False
    pinchminorflag = False
    pinchstartxcoord = None
    pinchstartycoord = None
    pinchdirectionflag = None
    prevpinchlv = 0
    pinchlv = 0
    framecount = 0
    prev_hand = None
    pinch_threshold = 0.3

    @classmethod
    def getpinchylv(cls, hand_result):
        dist = round((cls.pinchstartycoord - hand_result.landmark[8].y)*10, 1)
        return dist

    @classmethod
    def getpinchxlv(cls, hand_result):
        dist = round((hand_result.landmark[8].x - cls.pinchstartxcoord)*10, 1)
        return dist

    @classmethod
    def changesystembrightness(cls):
        currentBrightnessLv = sbcontrol.get_brightness(display=0)[-1]/100.0 
        currentBrightnessLv += cls.pinchlv/50.0
        if currentBrightnessLv > 1.0:
            currentBrightnessLv = 1.0
        elif currentBrightnessLv < 0.0:
            currentBrightnessLv = 0.0       
        sbcontrol.fade_brightness(int(100*currentBrightnessLv), start=sbcontrol.get_brightness(display=0))

    @classmethod
    def changesystemvolume(cls):
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        currentVolumeLv = volume.GetMasterVolumeLevelScalar()
        currentVolumeLv += cls.pinchlv/50.0
        if currentVolumeLv > 1.0:
            currentVolumeLv = 1.0
        elif currentVolumeLv < 0.0:
            currentVolumeLv = 0.0
        volume.SetMasterVolumeLevelScalar(currentVolumeLv, None)

    @classmethod
    def scrollVertical(cls):
        pyautogui.scroll(120 if cls.pinchlv > 0.0 else -120)

    @classmethod
    def scrollHorizontal(cls):
        pyautogui.keyDown('shift')
        pyautogui.keyDown('ctrl')
        pyautogui.scroll(-120 if cls.pinchlv > 0.0 else 120)
        pyautogui.keyUp('ctrl')
        pyautogui.keyUp('shift')

    # Locate Hand to get Cursor Position
    # Stabilize cursor by Dampening
    @classmethod
    def get_position(cls, hand_result):
        point = 9
        position = [hand_result.landmark[point].x, hand_result.landmark[point].y]
        sx, sy = pyautogui.size()
        x_old, y_old = pyautogui.position()
        x = int(position[0]*sx)
        y = int(position[1]*sy)
        if cls.prev_hand is None:
            cls.prev_hand = x, y
        delta_x = x - cls.prev_hand[0]
        delta_y = y - cls.prev_hand[1]

        distsq = delta_x**2 + delta_y**2
        ratio = 1
        cls.prev_hand = [x, y]

        if distsq <= 25:
            ratio = 0
        elif distsq <= 900:
            ratio = 0.07 * (distsq ** (1/2))
        else:
            ratio = 2.1
        x, y = x_old + delta_x*ratio, y_old + delta_y*ratio
        return (x, y)

    @classmethod
    def pinch_control_init(cls, hand_result):
        cls.pinchstartxcoord = hand_result.landmark[8].x
        cls.pinchstartycoord = hand_result.landmark[8].y
        cls.pinchlv = 0
        cls.prevpinchlv = 0
        cls.framecount = 0

    # Hold final position for 5 frames to change status
    @classmethod
    def pinch_control(cls, hand_result, controlHorizontal, controlVertical):
        if cls.framecount == 5:
            cls.framecount = 0
            cls.pinchlv = cls.prevpinchlv
            
            if cls.pinchdirectionflag == True:
                controlHorizontal() #x
            
            elif cls.pinchdirectionflag == False:
                controlVertical() #y

        lvx = cls.getpinchxlv(hand_result)
        lvy = cls.getpinchylv(hand_result)
        
        if abs(lvy) > abs(lvx) and abs(lvy) > cls.pinch_threshold:
            cls.pinchdirectionflag = False
            if abs(cls.prevpinchlv - lvy) < cls.pinch_threshold:
                cls.framecount += 1
            else:
                cls.prevpinchlv = lvy
                cls.framecount = 0

        elif abs(lvx) > cls.pinch_threshold:
            cls.pinchdirectionflag = True
            if abs(cls.prevpinchlv - lvx) < cls.pinch_threshold:
                cls.framecount += 1
            else:
                cls.prevpinchlv = lvx
                cls.framecount = 0

    @classmethod
    def handle_controls(cls, gesture, hand_result):  
        x, y = None, None
        if gesture != Gest.PALM:
            x, y = cls.get_position(hand_result)
    
        # flag reset
        if gesture != Gest.FIST and cls.grabflag:
            cls.grabflag = False
            pyautogui.mouseUp(button="left")

        if gesture != Gest.PINCH_MAJOR and cls.pinchmajorflag:
            cls.pinchmajorflag = False

        if gesture != Gest.PINCH_MINOR and cls.pinchminorflag:
            cls.pinchminorflag = False

        # implementation
        if gesture == Gest.V_GEST:
            cls.flag = True
            pyautogui.moveTo(x, y, duration=0.1)

        elif gesture == Gest.FIST:
            if not cls.grabflag: 
                cls.grabflag = True
                pyautogui.mouseDown(button="left")
            pyautogui.moveTo(x, y, duration=0.1)

        elif gesture == Gest.MID and cls.flag:
            pyautogui.click()
            cls.flag = False

        elif gesture == Gest.INDEX and cls.flag:
            pyautogui.click(button='right')
            cls.flag = False

        elif gesture == Gest.TWO_FINGER_CLOSED and cls.flag:
            pyautogui.doubleClick()
            cls.flag = False

        elif gesture == Gest.PINCH_MINOR:
            if cls.pinchminorflag == False:
                cls.pinch_control_init(hand_result)
                cls.pinchminorflag = True
            cls.pinch_control(hand_result, cls.scrollHorizontal, cls.scrollVertical)
    
        elif gesture == Gest.PINCH_MAJOR:
            if cls.pinchmajorflag == False:
                cls.pinch_control_init(hand_result)
                cls.pinchmajorflag = True
            cls.pinch_control(hand_result, cls.changesystembrightness, cls.changesystemvolume)

class GestureController:
    gc_mode = 0
    cap = None
    CAM_HEIGHT = None
    CAM_WIDTH = None
    hr_major = None # Right Hand by default
    hr_minor = None # Left hand by default
    dom_hand = True

    def __init__(self):
        GestureController.gc_mode = 1
        GestureController.cap = cv2.VideoCapture(0 + cv2.CAP_DSHOW) 
        GestureController.CAM_HEIGHT = GestureController.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        GestureController.CAM_WIDTH = GestureController.cap.get(cv2.CAP_PROP_FRAME_WIDTH)

    @classmethod
    def classify_hands(cls, results):
        left, right = None, None
        try:
            handedness_dict = MessageToDict(results.multi_handedness[0])
            if handedness_dict['classification'][0]['label'] == 'Right':
                right = results.multi_hand_landmarks[0]
            else:
                left = results.multi_hand_landmarks[0]
        except:
            pass

        try:
            handedness_dict = MessageToDict(results.multi_handedness[1])
            if handedness_dict['classification'][0]['label'] == 'Right':
                right = results.multi_hand_landmarks[1]
            else:
                left = results.multi_hand_landmarks[1]
        except:
            pass
    
        if GestureController.dom_hand == True:
            GestureController.hr_major = right
            GestureController.hr_minor = left
        else:
            GestureController.hr_major = left
            GestureController.hr_minor = right

    def start(self):
        handmajor = HandRecog(HLabel.MAJOR)
        handminor = HandRecog(HLabel.MINOR)

        with mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
            while GestureController.cap.isOpened() and GestureController.gc_mode:
                success, image = GestureController.cap.read()

                if not success:
                    print("Ignoring empty camera frame.")
                    continue
            
                image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
                image.flags.writeable = False
                results = hands.process(image)
            
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                if results.multi_hand_landmarks:                   
                    GestureController.classify_hands(results)
                    handmajor.update_hand_result(GestureController.hr_major)
                    handminor.update_hand_result(GestureController.hr_minor)

                    handmajor.set_finger_state()
                    handminor.set_finger_state()
                    gest_name = handminor.get_gesture()

                    if gest_name == Gest.PINCH_MINOR:
                        Controller.handle_controls(gest_name, handminor.hand_result)
                    else:
                        gest_name = handmajor.get_gesture()
                        Controller.handle_controls(gest_name, handmajor.hand_result)
                
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                else:
                    Controller.prev_hand = None
                cv2.imshow('Gesture Controller', image)
                if cv2.waitKey(5) & 0xFF == 13:  # 13 is Enter key
                    break
        GestureController.cap.release()
        cv2.destroyAllWindows()

# uncomment to run directly
if __name__ == "__main__":
    gc1 = GestureController()
    gc1.start()