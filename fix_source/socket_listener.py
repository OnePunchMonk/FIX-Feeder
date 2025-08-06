import socket
import logging

class SocketListener:
    def __init__(self, config, parser, producer, db_writer, shutdown_event):
        self.host = config['host']
        self.port = config['port']
        self.parser = parser
        self.producer = producer
        self.db_writer = db_writer
        self.logger = logging.getLogger(__name__)
        self.shutdown_event = shutdown_event

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Set a timeout so the accept() call doesn't block forever
        server_socket.settimeout(1.0)
        server_socket.bind((self.host, self.port))
        server_socket.listen()
        self.logger.info(f"Socket listener started on {self.host}:{self.port}, waiting for connections...")

        while not self.shutdown_event.is_set():
            try:
                conn, addr = server_socket.accept()
                with conn:
                    self.logger.info(f"Connected by {addr}")
                    while not self.shutdown_event.is_set():
                        data = conn.recv(1024)
                        if not data:
                            break # Client disconnected
                        
                        message = data.decode('utf-8').strip()
                        if message:
                            self.logger.debug(f"Received raw message: {message}")
                            parsed_message = self.parser.parse(message)
                            if parsed_message:
                                self.producer.send(parsed_message)
                                self.db_writer.write(parsed_message)
                self.logger.info(f"Connection from {addr} closed.")
            except socket.timeout:
                # This is expected, just loop again to check the shutdown_event
                continue
            except Exception as e:
                self.logger.error(f"An error occurred in the socket listener loop: {e}")
        
        server_socket.close()
        self.logger.info("Socket listener has shut down.")