import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

# Server Details
SERVER_IP = "192.168.240.204"  # Update with your correct IP
PORT = 12345

# Create a client socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client.connect((SERVER_IP, PORT))
except Exception as e:
    messagebox.showerror("Connection Error", f"Unable to connect to server: {e}")
    exit(1)

def receive_messages():
    """ Continuously receives messages from the server. """
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if not message:  # If empty message, connection might be closed
                break
            chat_box.config(state=tk.NORMAL)
            chat_box.insert(tk.END, message + "\n")
            chat_box.config(state=tk.DISABLED)
        except ConnectionResetError:
            print("Server disconnected!")
            break
        except Exception as e:
            print(f"Error receiving message: {e}")
            break
    client.close()

def send_message():
    """ Sends a message to the server. """
    message = message_input.get().strip()
    if message:  # Avoid sending empty messages
        try:
            client.send(message.encode('utf-8'))
            message_input.delete(0, tk.END)
        except BrokenPipeError:
            messagebox.showerror("Error", "Connection lost! Unable to send message.")
            app.quit()
    else:
        messagebox.showwarning("Warning", "Message cannot be empty!")

def on_closing():
    """ Handles GUI window closing. """
    client.close()
    app.destroy()

# GUI Setup
app = tk.Tk()
app.title("LAN Chat Messenger")

chat_box = scrolledtext.ScrolledText(app, state=tk.DISABLED, width=50, height=20)
chat_box.grid(row=0, column=0, padx=10, pady=10, columnspan=2)

message_input = tk.Entry(app, width=40)
message_input.grid(row=1, column=0, padx=10, pady=10)

send_button = tk.Button(app, text="Send", command=send_message)
send_button.grid(row=1, column=1, padx=10, pady=10)

# Start receiving messages
thread = threading.Thread(target=receive_messages, daemon=True)
thread.start()

app.protocol("WM_DELETE_WINDOW", on_closing)  # Handle window close
app.mainloop()
