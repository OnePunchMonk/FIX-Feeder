import socket
import time
import argparse
from threading import Thread, Barrier

# A sample, valid FIX message
FIX_MESSAGE = "8=FIX.4.2\x019=123\x0135=D\x0149=CLIENT\x0156=SERVER\x0134=1\x0152=20250806-18:00:00\x0111=STRESS1\x0155=AAPL\x0154=1\x0138=100\x0140=2\x0110=161\x01".encode('utf-8')
HOST = 'localhost'
PORT = 9876

def run_client(num_messages, barrier):
    """A single client that sends a burst of messages."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    print(f"Client connected, waiting for barrier...")
    barrier.wait() # Wait for all threads to be ready
    for _ in range(num_messages):
        s.sendall(FIX_MESSAGE)
    s.close()
    print(f"Client finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FixFeeder Stress Test Client")
    parser.add_argument('-m', '--messages', type=int, default=10000, help="Total messages to send.")
    parser.add_argument('-c', '--clients', type=int, default=10, help="Number of concurrent clients.")
    args = parser.parse_args()

    total_messages = args.messages
    num_clients = args.clients
    messages_per_client = total_messages // num_clients

    print(f"Preparing to send {total_messages} messages using {num_clients} concurrent clients...")

    barrier = Barrier(num_clients + 1) # +1 for the main thread
    threads = []

    start_time = time.time()
    for i in range(num_clients):
        thread = Thread(target=run_client, args=(messages_per_client, barrier))
        threads.append(thread)
        thread.start()

    print("All clients started. Triggering barrier to send messages now!")
    barrier.wait() # Unleash all clients at once

    for t in threads:
        t.join() # Wait for all threads to finish

    end_time = time.time()
    duration = end_time - start_time
    msg_per_sec = total_messages / duration

    print("\n--- Stress Test Complete ---")
    print(f"Sent {total_messages} messages in {duration:.2f} seconds.")
    print(f"Average throughput: {msg_per_sec:,.2f} messages/sec.")