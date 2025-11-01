import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector
from time import sleep
import numpy as np
from pynput.keyboard import Controller

class Button():
    def __init__(self, pos, text, size=[85, 85]):
        self.pos = pos
        self.size = size
        self.text = text

def vk_keyboard():
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)
    
    # Increase detection confidence for better accuracy
    detector = HandDetector(detectionCon=0.8, maxHands=1)
    
    keyboard_keys = [
        ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";"],
        ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"],
        ["SPACE", "BACK", "CLEAR", "ENTER"]
    ]
    
    final_text = ""
    keyboard = Controller()
    last_key_pressed = None
    click_cooldown = 0

    def draw(img, buttonList):
        for button in buttonList:
            x, y = button.pos
            w, h = button.size
            
            # Draw key with rounded corners
            cvzone.cornerRect(img, (x, y, w, h), 20, rt=0)
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 144, 30), cv2.FILLED)
            cv2.putText(img, button.text, (x + 15, y + 60), 
                       cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 0), 3)
        return img

    # Create button list
    buttonList = []
    for k in range(len(keyboard_keys)):
        for x, key in enumerate(keyboard_keys[k]):
            if k == 3:  # Bottom row special keys
                if key == "SPACE":
                    buttonList.append(Button([100 * x + 25, 100 * k + 50], key, [300, 85]))
                elif key == "BACK":
                    buttonList.append(Button([100 * x + 25, 100 * k + 50], key, [200, 85]))
                elif key == "CLEAR":
                    buttonList.append(Button([100 * x + 25, 100 * k + 50], key, [200, 85]))
                elif key == "ENTER":
                    buttonList.append(Button([100 * x + 25, 100 * k + 50], key, [200, 85]))
            else:
                buttonList.append(Button([100 * x + 25, 100 * k + 50], key))

    print("🎹 Virtual Keyboard Started - Press 'ESC' or 'q' to close")
    
    while True:
        success, img = cap.read()
        if not success:
            continue
            
        img = cv2.flip(img, 1)
        hands, img = detector.findHands(img, flipType=False)
        
        # Draw keyboard
        img = draw(img, buttonList)
        
        # Update cooldown
        if click_cooldown > 0:
            click_cooldown -= 1
        
        if hands:
            lmList = hands[0]['lmList']
            
            if lmList:
                for button in buttonList:
                    x, y = button.pos
                    w, h = button.size
                    
                    # Check if index finger tip is over button
                    if x < lmList[8][0] < x + w and y < lmList[8][1] < y + h:
                        # Highlight hover
                        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 255), cv2.FILLED)
                        cv2.putText(img, button.text, (x + 15, y + 60), 
                                   cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 0), 3)
                        
                        # Check distance between index and middle finger for click
                        length, info, img = detector.findDistance(lmList[8][:2], lmList[12][:2], img)
                        
                        # More strict distance threshold to prevent accidental clicks
                        if length < 30 and click_cooldown == 0:  # Reduced from 40 to 30
                            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), cv2.FILLED)
                            cv2.putText(img, button.text, (x + 15, y + 60), 
                                       cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 0), 3)
                            
                            # Prevent multiple presses for same key
                            if last_key_pressed != button.text:
                                last_key_pressed = button.text
                                click_cooldown = 15  # Add cooldown
                                
                                if button.text == "SPACE":
                                    keyboard.press(' ')
                                    final_text += " "
                                    print("📝 Space added")
                                elif button.text == "BACK":
                                    if final_text:
                                        final_text = final_text[:-1]
                                        keyboard.press('\b')
                                        print("📝 Backspace pressed")
                                elif button.text == "CLEAR":
                                    final_text = ""
                                    # Clear multiple characters
                                    for _ in range(50):
                                        keyboard.press('\b')
                                    print("📝 Text cleared")
                                elif button.text == "ENTER":
                                    keyboard.press('\n')
                                    final_text += "\n"
                                    print("📝 Enter pressed")
                                else:
                                    keyboard.press(button.text)
                                    final_text += button.text
                                    print(f"📝 Key pressed: {button.text}")
        
        # Display text area
        cv2.rectangle(img, (25, 400), (1250, 500), (255, 255, 255), cv2.FILLED)
        cv2.rectangle(img, (25, 400), (1250, 500), (0, 0, 0), 2)
        
        # Display text with proper formatting
        display_text = final_text[-40:]  # Show last 40 characters
        cv2.putText(img, display_text, (30, 470), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 2)
        
        # Add instructions
        cv2.putText(img, "Bring index & middle fingers VERY close to click", (25, 550), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(img, "Distance < 30px required for click", (25, 580), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(img, "Press ESC or Q to close", (25, 610), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow("Virtual Keyboard", img)
        
        # Close with ESC or Q
        key = cv2.waitKey(1)
        if key == 27 or key == ord('q') or key == ord('Q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()
    print("🎹 Virtual Keyboard Closed")

if __name__ == "__main__":
    vk_keyboard()