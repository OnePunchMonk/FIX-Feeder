# import pytest
# import time
# from threading import Thread
# from fix_source.socket_listener import SocketListener
# from protocol_parsers.fix_parser import FixParser
# import socket

# class MockProducer:
#     def __init__(self):
#         self.sent_messages = []
#     def send(self, message):
#         self.sent_messages.append(message)
#     def get_last_message(self):
#         return self.sent_messages[-1] if self.sent_messages else None

# class MockDbWriter:
#     def __init__(self):
#         self.written_messages = []
#     def write(self, message):
#         self.written_messages.append(message)
#     def get_last_message(self):
#         return self.written_messages[-1] if self.written_messages else None

# @pytest.fixture
# def test_system():
#     config = {'host': '127.0.0.1', 'port': 9999}
#     parser = FixParser()
#     producer = MockProducer()
#     db_writer = MockDbWriter()
    
#     listener = SocketListener(config, parser, producer, db_writer)
#     listener_thread = Thread(target=listener.start, daemon=True)
#     listener_thread.start()
    
#     # Give the server a moment to start
#     time.sleep(0.1)
    
#     yield config, producer, db_writer
    

# def test_socket_to_downstream_flow(test_system):
#     """
#     Tests the flow from socket ingestion to mock producer and DB writer.
#     """
#     config, producer, db_writer = test_system
    
#     fix_string = "8=FIX.4.2\x0135=A\x0198=0\x01108=30\x0110=037\x01"

#     # Send a message to the listener
#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#         s.connect((config['host'], config['port']))
#         s.sendall(fix_string.encode('utf-8'))
    
#     # Give the system time to process
#     time.sleep(0.1)

#     # Check if the message reached the mock downstream components
#     producer_msg = producer.get_last_message()
#     db_msg = db_writer.get_last_message()

#     assert producer_msg is not None
#     assert db_msg is not None
#     assert producer_msg[35] == 'A'
#     assert db_msg[108] == '30'
import pytest
import time
from threading import Thread, Event # <-- Import Event
from fix_source.socket_listener import SocketListener
from protocol_parsers.fix_parser import FixParser
import socket

# This is a simplified integration test.
# A full-fledged test would use mocks for Kafka and DB or spin up real services.

class MockProducer:
    def __init__(self):
        self.sent_messages = []
    def send(self, message):
        self.sent_messages.append(message)
    def get_last_message(self):
        return self.sent_messages[-1] if self.sent_messages else None

class MockDbWriter:
    def __init__(self):
        self.written_messages = []
    def write(self, message):
        self.written_messages.append(message)
    def get_last_message(self):
        return self.written_messages[-1] if self.written_messages else None

@pytest.fixture
def test_system():
    config = {'host': '127.0.0.1', 'port': 9999}
    parser = FixParser()
    producer = MockProducer()
    db_writer = MockDbWriter()
    
    # --- FIX: Create and pass the shutdown_event ---
    shutdown_event = Event()
    listener = SocketListener(config, parser, producer, db_writer, shutdown_event)
    # -------------------------------------------

    listener_thread = Thread(target=listener.start, daemon=True)
    listener_thread.start()
    
    time.sleep(0.1)
    
    yield config, producer, db_writer, shutdown_event
    
    # Tell the listener to stop
    shutdown_event.set()

def test_socket_to_downstream_flow(test_system):
    """
    Tests the flow from socket ingestion to mock producer and DB writer.
    """
    config, producer, db_writer, shutdown_event = test_system
    
    fix_string = "8=FIX.4.2\x0135=A\x0198=0\x01108=30\x0110=037\x01"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((config['host'], config['port']))
        s.sendall(fix_string.encode('utf-8'))
    
    time.sleep(0.1)

    producer_msg = producer.get_last_message()
    db_msg = db_writer.get_last_message()

    assert producer_msg is not None
    assert db_msg is not None
    # --- FIX: Check inside the 'raw' dictionary ---
    assert producer_msg['raw']['35'] == 'A'
    assert db_msg['raw']['108'] == '30'
    # -------------------------------------------