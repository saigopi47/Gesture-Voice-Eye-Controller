import tkinter as tk
from PIL import Image, ImageTk
import os
import cv2

print("✅ main.py started")

# First, let's check if camera is accessible
def check_camera():
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, frame = cap.read()
        cap.release()
        if ret:
            print("✅ Camera is accessible")
            return True
        else:
            print("❌ Camera can open but cannot read frames")
            return False
    else:
        print("❌ Cannot open camera")
        return False

# Check camera before importing modules
check_camera()

try:
    # Import corrected function names
    from Gesture_Controller import GestureController  # Use the class directly
    from eye import eye_move as eye_control
    from samvk import vk_keyboard as keyboard_control
    from Proton import proton_chat as voicebot
    print("✅ Imported all modules successfully.")
except Exception as e:
    print("❌ Error importing modules:", e)

# Create window
window = tk.Tk()
window.title("Gesture Controlled Virtual Mouse and Keyboard")
window.geometry("1000x600")

# Load app icon
icon_path = os.path.join(os.path.dirname(__file__), '..', 'mn.png')
if os.path.exists(icon_path):
    window.iconphoto(False, tk.PhotoImage(file=icon_path))
    print("✅ App icon loaded")
else:
    print(f"⚠️ Icon file missing: {icon_path}")

# Helper to load images safely
def load_image(name):
    try:
        path = os.path.join(os.path.dirname(__file__), '..', 'icons', name)
        img = Image.open(path).resize((120, 120))
        print(f"✅ Loaded {name}")
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"❌ Failed to load {name}: {e}")
        return None

# Load images
icons = {
    "voice": load_image("bot.png"),
    "keyboard": load_image("keyboard.png"),
    "gesture": load_image("hand.png"),
    "eye": load_image("eye.jpeg"),
    "exit": load_image("exit.png")
}

# Define button actions
def voicebot_start():
    print("🎙 VoiceBot started")
    voicebot()

def keyboard_start():
    print("⌨ Virtual Keyboard started")
    keyboard_control()

def gesture_start():
    print("🖐 Gesture Control started")
    # Create instance and start gesture controller
    gc = GestureController()
    gc.start()

def eye_start():
    print("👁 Eye Control started")
    eye_control()

def exit_app():
    print("🚪 Exiting")
    window.destroy()

# Create buttons
btn_voice = tk.Button(window, image=icons["voice"], text="VoiceBot", compound="top", command=voicebot_start)
btn_keyboard = tk.Button(window, image=icons["keyboard"], text="Keyboard", compound="top", command=keyboard_start)
btn_gesture = tk.Button(window, image=icons["gesture"], text="Gesture", compound="top", command=gesture_start)
btn_eye = tk.Button(window, image=icons["eye"], text="Eye", compound="top", command=eye_start)
btn_exit = tk.Button(window, image=icons["exit"], text="Exit", compound="top", command=exit_app)

# Place buttons
btn_voice.place(x=100, y=100)
btn_keyboard.place(x=300, y=100)
btn_gesture.place(x=500, y=100)
btn_eye.place(x=700, y=100)
btn_exit.place(x=400, y=350)

print("✅ GUI setup complete, launching window...")
window.mainloop()
print("✅ Window closed")