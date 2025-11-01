import pyttsx3
import speech_recognition as sr
from datetime import date
import time
import webbrowser
import datetime
from pynput.keyboard import Key, Controller
import pyautogui
import sys
import os
from os import listdir
from os.path import isfile, join
import smtplib
import wikipedia
import Gesture_Controller
from threading import Thread

today = date.today()
keyboard = Controller()

# Initialize TTS engine properly
try:
    engine = pyttsx3.init('sapi5')
except:
    engine = pyttsx3.init()

voices = engine.getProperty('voices')
if voices:
    engine.setProperty('voice', voices[0].id)

# Set speech properties
engine.setProperty('rate', 150)  # Speed percent
engine.setProperty('volume', 0.8)  # Volume 0-1

print("Testing TTS...")
engine.say("Testing system audio. Voice assistant is ready.")
engine.runAndWait()
print("TTS test done.")

file_exp_status = False
files = []
path = ''
is_awake = True  # Bot status

# Initialize speech recognizer
try:
    r = sr.Recognizer()
    speech_recognition_available = True
    print("✅ Speech recognition available")
except Exception as e:
    speech_recognition_available = False
    print(f"❌ Speech recognition failed: {e}")

# Try to import app module but handle errors gracefully
app_available = False
ChatBot = None

try:
    import app
    from app import ChatBot
    app_available = True
    print("✅ App module available")
except ImportError as e:
    print(f"❌ App module import failed: {e}")
    app_available = False
except Exception as e:
    print(f"❌ App module error: {e}")
    app_available = False

def proton_chat():
    print("🎙️ Starting Voice Assistant...")
    
    def reply(audio):
        try:
            print(f"Proton: {audio}")
            # Only try to use app.ChatBot if it's available and working
            if app_available and hasattr(app, 'ChatBot') and hasattr(app.ChatBot, 'addAppMsg'):
                try:
                    app.ChatBot.addAppMsg(audio)
                except Exception as e:
                    print(f"GUI update failed: {e}")
            engine.say(audio)
            engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")

    def wish():
        hour = datetime.datetime.now().hour
        if 0 <= hour < 12:
            reply("Good Morning!")
        elif 12 <= hour < 18:
            reply("Good Afternoon!")
        else:
            reply("Good Evening!")  
        reply("I am Proton, your voice assistant. How may I help you?")

    def record_audio():
        if not speech_recognition_available:
            print("Speech recognition not available")
            return ""
            
        try:
            with sr.Microphone() as source:
                print("🔊 Adjusting for ambient noise...")
                r.adjust_for_ambient_noise(source, duration=1)
                print("🎤 Listening...")
                audio = r.listen(source, timeout=10, phrase_time_limit=8)
                
            print("🔍 Recognizing...")
            voice_data = r.recognize_google(audio).lower()
            print(f"You said: {voice_data}")
            return voice_data
        except sr.WaitTimeoutError:
            print("Listening timeout")
            return ""
        except sr.UnknownValueError:
            print("Could not understand audio")
            return ""
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            reply("Sorry, there's an issue with the speech recognition service.")
            return ""
        except Exception as e:
            print(f"Microphone error: {e}")
            return ""

    def respond(voice_data):
        global file_exp_status, files, is_awake, path
        
        if not voice_data:
            return
            
        print(f"Processing: {voice_data}")
        voice_data = voice_data.lower().replace('proton', '')
        
        # Only try to use eel if app is available and working
        if app_available:
            try:
                if hasattr(app, 'eel') and hasattr(app.eel, 'addUserMsg'):
                    app.eel.addUserMsg(voice_data)
            except Exception as e:
                print(f"Eel GUI update failed: {e}")
        
        if not is_awake:
            if 'wake up' in voice_data or 'hello' in voice_data:
                is_awake = True
                wish()
            return

        # STATIC CONTROLS
        if 'hello' in voice_data or 'hi' in voice_data:
            wish()

        elif 'what is your name' in voice_data:
            reply('My name is Proton! I am your voice assistant.')

        elif 'date' in voice_data:
            reply(today.strftime("%B %d, %Y"))

        elif 'time' in voice_data:
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            reply(f"The current time is {current_time}")

        elif 'search' in voice_data:
            query = voice_data.replace('search', '').strip()
            if query:
                reply(f'Searching for {query}')
                url = f'https://google.com/search?q={query.replace(" ", "+")}'
                try:
                    webbrowser.open(url)
                    reply('Search completed')
                except:
                    reply('Please check your internet connection')

        elif 'location' in voice_data:
            reply('Which place are you looking for?')
            temp_audio = record_audio()
            if temp_audio:
                reply(f'Locating {temp_audio}...')
                url = f'https://google.com/maps/place/{temp_audio.replace(" ", "+")}'
                try:
                    webbrowser.open(url)
                    reply('Location found')
                except:
                    reply('Please check your internet connection')

        elif any(word in voice_data for word in ['bye', 'goodbye', 'exit', 'quit']):
            reply("Goodbye! Have a great day!")
            is_awake = False
            return "exit"

        # DYNAMIC CONTROLS
        elif 'launch gesture' in voice_data or 'start gesture' in voice_data:
            if getattr(Gesture_Controller.GestureController, 'gc_mode', False):
                reply('Gesture recognition is already active')
            else:
                try:
                    gc = Gesture_Controller.GestureController()
                    t = Thread(target=gc.start, daemon=True)
                    t.start()
                    reply('Gesture control launched successfully')
                except Exception as e:
                    reply(f'Failed to launch gesture control: {e}')

        elif 'stop gesture' in voice_data or 'close gesture' in voice_data:
            if getattr(Gesture_Controller.GestureController, 'gc_mode', False):
                Gesture_Controller.GestureController.gc_mode = 0
                reply('Gesture recognition stopped')
            else:
                reply('Gesture recognition is not active')

        elif 'copy' in voice_data:
            with keyboard.pressed(Key.ctrl):
                keyboard.press('c')
                keyboard.release('c')
            reply('Text copied')

        elif 'paste' in voice_data:
            with keyboard.pressed(Key.ctrl):
                keyboard.press('v')
                keyboard.release('v')
            reply('Text pasted')

        # File Navigation
        elif 'list files' in voice_data or 'show files' in voice_data:
            try:
                path = 'C://'
                files = listdir(path)
                file_list = ", ".join(files[:5])  # Show first 5 files
                reply(f'Found {len(files)} files. First few files: {file_list}')
                file_exp_status = True
            except Exception as e:
                reply(f'Error accessing files: {e}')

        # APPLICATION CONTROLS
        elif 'open' in voice_data:
            if 'chrome' in voice_data or 'browser' in voice_data:
                try:
                    os.system('start chrome')
                    reply('Opening Google Chrome')
                except:
                    reply('Failed to open Chrome')
            elif 'notepad' in voice_data:
                try:
                    os.system('notepad')
                    reply('Opening Notepad')
                except:
                    reply('Failed to open Notepad')
            elif 'calculator' in voice_data or 'calc' in voice_data:
                try:
                    os.system('calc')
                    reply('Opening Calculator')
                except:
                    reply('Failed to open Calculator')

        else:
            reply('I did not understand that command. Try saying: hello, search, time, open chrome, or launch gesture control.')

    # Start the application
    try:
        if app_available and hasattr(app, 'ChatBot'):
            t1 = Thread(target=app.ChatBot.start, daemon=True)
            t1.start()

            # Wait for chatbot to start (but don't block forever)
            timeout = 5
            start_time = time.time()
            while not getattr(app.ChatBot, 'started', False):
                if time.time() - start_time > timeout:
                    print("Chatbot startup timeout - continuing without GUI")
                    break
                time.sleep(0.5)
    except Exception as e:
        print(f"Chatbot initialization failed: {e}")

    # Main loop
    wish()
    
    while True:
        try:
            # Check for GUI input first (only if app is working)
            voice_data = ""
            if app_available and hasattr(app, 'ChatBot') and hasattr(app.ChatBot, 'isUserInput'):
                try:
                    if app.ChatBot.isUserInput():
                        voice_data = app.ChatBot.popUserInput()
                        print(f"GUI input: {voice_data}")
                except Exception as e:
                    print(f"GUI input error: {e}")
            
            # If no GUI input, get voice input
            if not voice_data:
                voice_data = record_audio()

            if voice_data:
                result = respond(voice_data)
                if result == "exit":
                    break
                    
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(1)

    print("Voice assistant closed")

# Make sure this runs
if __name__ == "__main__":
    proton_chat()