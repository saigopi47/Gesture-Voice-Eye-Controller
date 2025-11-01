import cv2
import mediapipe as mp
import pyautogui
import time

class EyeController:
    def __init__(self):
        self.cam = cv2.VideoCapture(0)
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
        self.screen_w, self.screen_h = pyautogui.size()
        
        # Blink detection variables
        self.left_eye_closed = False
        self.right_eye_closed = False
        self.last_blink_time = 0
        self.blink_cooldown = 0.5  # seconds
        self.double_blink_threshold = 0.3  # seconds for double blink
        self.last_blink_end_time = 0
        
        # Gaze holding variables
        self.gaze_start_time = 0
        self.gaze_hold_threshold = 1.5  # seconds to trigger drag
        self.is_dragging = False
        self.last_gaze_point = None
        
        # Click cooldown
        self.click_cooldown = 0

    def get_eye_aspect_ratio(self, eye_landmarks):
        # Calculate eye aspect ratio for blink detection
        # Vertical points
        v1 = abs(eye_landmarks[1].y - eye_landmarks[5].y)
        v2 = abs(eye_landmarks[2].y - eye_landmarks[4].y)
        # Horizontal points
        h = abs(eye_landmarks[0].x - eye_landmarks[3].x)
        
        ear = (v1 + v2) / (2.0 * h)
        return ear

    def detect_blinks(self, landmarks):
        # Left eye landmarks (indices from MediaPipe)
        left_eye_indices = [33, 160, 158, 133, 153, 144]
        right_eye_indices = [362, 385, 387, 263, 373, 380]
        
        left_eye = [landmarks[i] for i in left_eye_indices]
        right_eye = [landmarks[i] for i in right_eye_indices]
        
        left_ear = self.get_eye_aspect_ratio(left_eye)
        right_ear = self.get_eye_aspect_ratio(right_eye)
        
        # Blink threshold (adjust based on testing)
        blink_threshold = 0.2
        
        current_time = time.time()
        
        # Detect left wink
        if left_ear < blink_threshold and right_ear > blink_threshold:
            if not self.left_eye_closed and current_time - self.last_blink_time > self.blink_cooldown:
                self.left_eye_closed = True
                self.last_blink_time = current_time
                return "left_wink"
        
        # Detect right wink  
        elif right_ear < blink_threshold and left_ear > blink_threshold:
            if not self.right_eye_closed and current_time - self.last_blink_time > self.blink_cooldown:
                self.right_eye_closed = True
                self.last_blink_time = current_time
                return "right_wink"
        
        # Detect double blink (both eyes)
        elif left_ear < blink_threshold and right_ear < blink_threshold:
            if not self.left_eye_closed and not self.right_eye_closed:
                self.left_eye_closed = True
                self.right_eye_closed = True
                current_time = time.time()
                
                # Check for double blink
                if current_time - self.last_blink_end_time < self.double_blink_threshold:
                    self.last_blink_end_time = 0
                    return "double_blink"
                self.last_blink_time = current_time
        
        # Reset eye states when eyes open
        else:
            if self.left_eye_closed or self.right_eye_closed:
                self.last_blink_end_time = time.time()
            self.left_eye_closed = False
            self.right_eye_closed = False
            
        return None

    def check_gaze_holding(self, gaze_point):
        current_time = time.time()
        
        if self.last_gaze_point is None:
            self.last_gaze_point = gaze_point
            self.gaze_start_time = current_time
            return False
            
        # Check if gaze is stable (within small movement threshold)
        movement = abs(gaze_point[0] - self.last_gaze_point[0]) + abs(gaze_point[1] - self.last_gaze_point[1])
        
        if movement < 0.01:  # Small movement threshold
            if current_time - self.gaze_start_time > self.gaze_hold_threshold:
                if not self.is_dragging:
                    self.is_dragging = True
                    pyautogui.mouseDown()
                    return "drag_start"
        else:
            self.gaze_start_time = current_time
            if self.is_dragging:
                self.is_dragging = False
                pyautogui.mouseUp()
                return "drag_end"
                
        self.last_gaze_point = gaze_point
        return None

    def eye_move(self):
        print("👁 Starting Eye Controlled Mouse...")
        print("Controls:")
        print("😉 Left Wink - Left click")
        print("😉 Right Wink - Right click") 
        print("😑 Double Blink - Double click")
        print("👁️ Stare/Hold Gaze (1.5s) - Click and drag")
        print("Press 'Q' to quit")
        
        while True:
            success, frame = self.cam.read()
            if not success:
                continue
                
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            output = self.face_mesh.process(rgb_frame)
            landmark_points = output.multi_face_landmarks
            frame_h, frame_w, _ = frame.shape
            
            if landmark_points:
                landmarks = landmark_points[0].landmark
                
                # Cursor movement with right eye
                for id, landmark in enumerate(landmarks[474:478]):
                    x = int(landmark.x * frame_w)
                    y = int(landmark.y * frame_h)
                    cv2.circle(frame, (x, y), 3, (0, 255, 0))
                    
                    if id == 1:
                        screen_x = self.screen_w * landmark.x
                        screen_y = self.screen_h * landmark.y
                        pyautogui.moveTo(screen_x, screen_y)
                        
                        # Check gaze holding for drag
                        gaze_action = self.check_gaze_holding((landmark.x, landmark.y))
                        if gaze_action == "drag_start":
                            cv2.putText(frame, "DRAGGING", (50, 100), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # Blink detection
                if self.click_cooldown <= 0:
                    blink_action = self.detect_blinks(landmarks)
                    
                    if blink_action == "left_wink":
                        pyautogui.click()
                        self.click_cooldown = 20
                        cv2.putText(frame, "LEFT CLICK", (50, 50), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        
                    elif blink_action == "right_wink":
                        pyautogui.click(button='right')
                        self.click_cooldown = 20
                        cv2.putText(frame, "RIGHT CLICK", (50, 50), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        
                    elif blink_action == "double_blink":
                        pyautogui.doubleClick()
                        self.click_cooldown = 30
                        cv2.putText(frame, "DOUBLE CLICK", (50, 50), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                
                # Visual feedback for eye states
                left_color = (0, 0, 255) if self.left_eye_closed else (0, 255, 0)
                right_color = (0, 0, 255) if self.right_eye_closed else (0, 255, 0)
                
                cv2.putText(frame, "L", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 
                          1, left_color, 2)
                cv2.putText(frame, "R", (100, 150), cv2.FONT_HERSHEY_SIMPLEX, 
                          1, right_color, 2)
                
                # Draw eye landmarks for visualization
                for landmark in [landmarks[145], landmarks[159]]:  # Left eye
                    x = int(landmark.x * frame_w)
                    y = int(landmark.y * frame_h)
                    cv2.circle(frame, (x, y), 3, (0, 255, 255), -1)
                
                for landmark in [landmarks[374], landmarks[386]]:  # Right eye
                    x = int(landmark.x * frame_w)
                    y = int(landmark.y * frame_h)
                    cv2.circle(frame, (x, y), 3, (0, 255, 255), -1)
            
            # Update cooldown
            if self.click_cooldown > 0:
                self.click_cooldown -= 1
            
            # Display instructions
            cv2.putText(frame, "Left Wink: Left Click", (10, frame_h - 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "Right Wink: Right Click", (10, frame_h - 80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "Double Blink: Double Click", (10, frame_h - 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "Hold Gaze: Drag", (10, frame_h - 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "Press 'Q' to quit", (10, frame_h - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            cv2.imshow('Eye Controlled Mouse', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.cam.release()
        cv2.destroyAllWindows()
        print("✅ Eye Controller Closed")

def eye_move():
    controller = EyeController()
    controller.eye_move()

if __name__ == "__main__":
    eye_move()