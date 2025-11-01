import eel
import os
from queue import Queue

class ChatBot:
    started = False
    userinputQueue = Queue()

    @staticmethod
    def isUserInput():
        return not ChatBot.userinputQueue.empty()

    @staticmethod
    def popUserInput():
        return ChatBot.userinputQueue.get()

    def close_callback(route, websockets):
        exit()

    @eel.expose
    def getUserInput(msg):
        ChatBot.userinputQueue.put(msg)
        print(f"GUI Input: {msg}")
    
    @staticmethod
    def close():
        ChatBot.started = False
    
    @staticmethod
    def addUserMsg(msg):
        try:
            eel.addUserMsg(msg)
        except Exception as e:
            print(f"Eel addUserMsg error: {e}")
    
    @staticmethod
    def addAppMsg(msg):
        try:
            eel.addAppMsg(msg)
        except Exception as e:
            print(f"Eel addAppMsg error: {e}")

    @staticmethod
    def start():
        try:
            # Get the current directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Check if web directory exists
            web_path = os.path.join(current_dir, 'web')
            if not os.path.exists(web_path):
                print(f"❌ Web directory not found: {web_path}")
                print("Creating basic web interface...")
                # Create a basic web directory if it doesn't exist
                os.makedirs(web_path, exist_ok=True)
                
                # Create a basic index.html
                index_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Proton Chat</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
        #chat-container { background: white; padding: 20px; border-radius: 10px; height: 400px; overflow-y: auto; }
        .user-msg { text-align: right; color: blue; margin: 5px 0; }
        .app-msg { text-align: left; color: green; margin: 5px 0; }
        input { width: 70%; padding: 10px; margin-right: 10px; }
        button { padding: 10px 20px; }
    </style>
</head>
<body>
    <h2>Proton Voice Assistant</h2>
    <div id="chat-container"></div>
    <input type="text" id="user-input" placeholder="Type your message...">
    <button onclick="sendMessage()">Send</button>

    <script>
        function sendMessage() {
            var input = document.getElementById('user-input');
            var message = input.value;
            if (message) {
                eel.getUserInput(message);
                addUserMsg(message);
                input.value = '';
            }
        }

        function addUserMsg(msg) {
            var chat = document.getElementById('chat-container');
            var div = document.createElement('div');
            div.className = 'user-msg';
            div.textContent = 'You: ' + msg;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        eel.expose(addAppMsg);
        function addAppMsg(msg) {
            var chat = document.getElementById('chat-container');
            var div = document.createElement('div');
            div.className = 'app-msg';
            div.textContent = 'Proton: ' + msg;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        // Enter key support
        document.getElementById('user-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
"""
                
                with open(os.path.join(web_path, 'index.html'), 'w') as f:
                    f.write(index_html)
                print("✅ Created basic web interface")
            
            # Initialize eel with the web path
            eel.init(web_path, allowed_extensions=['.js', '.html'])
            
            print("🌐 Starting web interface...")
            eel.start('index.html', 
                     mode='chrome',
                     host='localhost',
                     port=27005,
                     block=False,
                     size=(400, 600),
                     position=(100, 100),
                     disable_cache=True,
                     close_callback=ChatBot.close_callback)
            
            ChatBot.started = True
            print("✅ Web interface started successfully")
            
            # Keep the thread alive
            while ChatBot.started:
                try:
                    eel.sleep(5.0)
                except (KeyboardInterrupt, SystemExit):
                    break
                except Exception as e:
                    print(f"Eel sleep error: {e}")
                    break
                    
        except Exception as e:
            print(f"❌ Failed to start web interface: {e}")
            ChatBot.started = False