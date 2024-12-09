import socket
import ssl
import selectors
import signal
from threading import Thread

# Signal handler for ignoring broken pipe signals
signal.signal(signal.SIGPIPE, signal.SIG_IGN)

# Create SSL context
def create_context():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
    return context

# Accept a new client and wrap with SSL
def accept_connection(sock, context, selector):
    client_sock, addr = sock.accept()
    print(f"Connection from {addr}")
    try:
        ssl_client_sock = context.wrap_socket(client_sock, server_side=True)
        selector.register(ssl_client_sock, selectors.EVENT_READ, handle_client)
    except ssl.SSLError as e:
        print(f"SSL Error: {e}")
        client_sock.close()

# Handle client connection
def handle_client(sock, selector):
    try:
        data = sock.recv(1024)  # Receive data
        if data:
            print(f"Received: {data.decode()}")
            response = "To God be the Glory!"
            sock.sendall(response.encode())  # Send response
        else:
            print("Closing connection")
            selector.unregister(sock)
            sock.close()
    except Exception as e:
        print(f"Error handling client: {e}")
        selector.unregister(sock)
        sock.close()

# Main server function
def run_server():
    host = "0.0.0.0"
    port = 44333
    backlog = 10

    # Create and bind the socket
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, port))
    server_sock.listen(backlog)
    print(f"Server listening on {host}:{port}")

    # Create SSL context
    context = create_context()

    # Initialize selector for handling multiple connections
    selector = selectors.DefaultSelector()
    selector.register(server_sock, selectors.EVENT_READ, lambda s: accept_connection(s, context, selector))

    try:
        while True:
            events = selector.select(timeout=2.5)
            for key, _ in events:
                callback = key.data
                callback(key.fileobj, selector)
    except KeyboardInterrupt:
        print("Shutting down server")
    finally:
        selector.close()
        server_sock.close()

# Entry point
if __name__ == "__main__":
    run_server()
