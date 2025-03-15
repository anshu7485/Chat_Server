from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
import socket
import threading
import json
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # WebSockets enable

clients = set()  # Flask WebSocket clients
tcp_clients = []  # TCP socket clients

CHAT_HISTORY_FILE = "chat_history.json"

def save_message(sender, message):
    """Save message to JSON file"""
    chat_data = []
    
    # Load previous messages if file exists
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r") as file:
            try:
                chat_data = json.load(file)
            except json.JSONDecodeError:
                chat_data = []

    chat_data.append({"sender": sender, "message": message})

    # Save updated chat history
    with open(CHAT_HISTORY_FILE, "w") as file:
        json.dump(chat_data, file, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    clients.add(request.sid)
    print(f"WebSocket Client Connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    clients.discard(request.sid)
    print(f"WebSocket Client Disconnected: {request.sid}")

@socketio.on('message')
def handle_message(msg):
    """Handle message from WebSocket (Browser UI)"""
    print(f"WebSocket Message Received: {msg}")
    save_message("User", msg)  # Save message to JSON

    # Broadcast message to all WebSocket clients
    send(msg, broadcast=True)

    # Send message to all TCP clients
    for client in tcp_clients:
        try:
            client.send(msg.encode('utf-8'))
        except:
            tcp_clients.remove(client)

# TCP Server Code
HOST = '0.0.0.0'
PORT = 12345  

def handle_client(client_socket, address):
    """Handle TCP client connection"""
    print(f"[TCP] New Connection: {address}")
    tcp_clients.append(client_socket)

    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                print(f"[TCP] {address}: {message}")
                save_message(f"Client-{address}", message)  # Save to JSON

                # Send message to all TCP clients
                for client in tcp_clients:
                    if client != client_socket:
                        client.send(message.encode('utf-8'))

                # Send message to Web UI via WebSockets
                socketio.emit('message', message)

        except:
            tcp_clients.remove(client_socket)
            client_socket.close()
            break

def start_socket_server():
    """Start TCP socket server"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[TCP Server] Listening on {HOST}:{PORT}")

    while True:
        client_socket, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.start()

if __name__ == "__main__":
    threading.Thread(target=start_socket_server).start()
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
