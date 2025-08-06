#!/usr/bin/env python3
"""
FixFeeder Mock Data Sender

This script sends sample FIX messages to FixFeeder for testing purposes.
Supports various message types and can simulate realistic trading scenarios.
"""

import socket
import time
import random
import argparse
import sys
from datetime import datetime, timedelta
from typing import List, Dict

class FixMessageGenerator:
    """Generates realistic FIX messages for testing."""
    
    SYMBOLS = ['AAPL', 'GOOG', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']
    SIDES = ['1', '2']  # 1=Buy, 2=Sell
    ORDER_TYPES = ['1', '2', '3', '4']  # 1=Market, 2=Limit, 3=Stop, 4=StopLimit
    
    def __init__(self):
        self.seq_num = 1
        self.order_id = 1
        
    def _calculate_checksum(self, message: str) -> str:
        """Calculate FIX checksum for message validation."""
        checksum = sum(ord(c) for c in message) % 256
        return f"{checksum:03d}"
    
    def _format_timestamp(self, dt: datetime = None) -> str:
        """Format timestamp in FIX format (YYYYMMDD-HH:MM:SS)."""
        if dt is None:
            dt = datetime.utcnow()
        return dt.strftime("%Y%m%d-%H:%M:%S")
    
    def _build_message(self, fields: Dict[str, str]) -> str:
        """Build complete FIX message with proper formatting."""
        # Standard header fields
        message_parts = [
            "8=FIX.4.2",  # BeginString
            f"35={fields.get('35', 'D')}",  # MsgType
            f"49={fields.get('49', 'CLIENT')}",  # SenderCompID
            f"56={fields.get('56', 'SERVER')}",  # TargetCompID
            f"34={self.seq_num}",  # MsgSeqNum
            f"52={self._format_timestamp()}"  # SendingTime
        ]
        
        # Add custom fields (excluding header fields)
        for tag, value in fields.items():
            if tag not in ['8', '35', '49', '56', '34', '52', '10']:
                message_parts.append(f"{tag}={value}")
        
        # Join with SOH delimiter (excluding checksum)
        message_body = '\x01'.join(message_parts) + '\x01'
        
        # Calculate and add checksum
        checksum = self._calculate_checksum(message_body)
        complete_message = message_body + f"10={checksum}\x01"
        
        self.seq_num += 1
        return complete_message
    
    def new_order_single(self, symbol: str = None, side: str = None, 
                        quantity: int = None, price: float = None) -> str:
        """Generate New Order Single (35=D) message."""
        symbol = symbol or random.choice(self.SYMBOLS)
        side = side or random.choice(self.SIDES)
        quantity = quantity or random.randint(100, 10000)
        order_type = random.choice(self.ORDER_TYPES)
        
        fields = {
            '35': 'D',  # NewOrderSingle
            '11': f"ORD_{self.order_id:06d}",  # ClOrdID
            '55': symbol,  # Symbol
            '54': side,    # Side
            '38': str(quantity),  # OrderQty
            '40': order_type      # OrdType
        }
        
        # Add price for limit orders
        if order_type in ['2', '4'] and price:
            fields['44'] = f"{price:.2f}"
        elif order_type in ['2', '4']:
            fields['44'] = f"{random.uniform(100, 300):.2f}"
        
        self.order_id += 1
        return self._build_message(fields)
    
    def order_cancel_request(self, orig_order_id: str = None, 
                           symbol: str = None) -> str:
        """Generate Order Cancel Request (35=F) message."""
        orig_order_id = orig_order_id or f"ORD_{random.randint(1, self.order_id):06d}"
        symbol = symbol or random.choice(self.SYMBOLS)
        
        fields = {
            '35': 'F',  # OrderCancelRequest
            '11': f"CANCEL_{self.order_id:06d}",  # ClOrdID
            '41': orig_order_id,  # OrigClOrdID
            '55': symbol,  # Symbol
            '54': random.choice(self.SIDES)  # Side
        }
        
        self.order_id += 1
        return self._build_message(fields)
    
    def execution_report(self, order_id: str = None, symbol: str = None,
                        exec_type: str = '0') -> str:
        """Generate Execution Report (35=8) message."""
        order_id = order_id or f"ORD_{random.randint(1, self.order_id):06d}"
        symbol = symbol or random.choice(self.SYMBOLS)
        
        fields = {
            '35': '8',  # ExecutionReport
            '11': order_id,  # ClOrdID
            '17': f"EXEC_{random.randint(1000, 9999)}",  # ExecID
            '150': exec_type,  # ExecType (0=New, 1=PartialFill, 2=Fill, 4=Canceled)
            '39': '0',  # OrdStatus (0=New, 1=PartiallyFilled, 2=Filled, 4=Canceled)
            '55': symbol,  # Symbol
            '54': random.choice(self.SIDES),  # Side
            '38': str(random.randint(100, 10000)),  # OrderQty
            '31': f"{random.uniform(100, 300):.2f}",  # LastPx
            '32': str(random.randint(100, 1000))  # LastQty
        }
        
        return self._build_message(fields)
    
    def heartbeat(self) -> str:
        """Generate Heartbeat (35=0) message."""
        fields = {'35': '0'}  # Heartbeat
        return self._build_message(fields)
    
    def test_request(self, test_req_id: str = None) -> str:
        """Generate Test Request (35=1) message."""
        test_req_id = test_req_id or f"TEST_{int(time.time())}"
        fields = {
            '35': '1',  # TestRequest
            '112': test_req_id  # TestReqID
        }
        return self._build_message(fields)

class FixFeederClient:
    """Client for sending messages to FixFeeder."""
    
    def __init__(self, host: str = 'localhost', port: int = 9876):
        self.host = host
        self.port = port
        self.generator = FixMessageGenerator()
    
    def send_message(self, message: str, verbose: bool = False) -> bool:
        """Send a single message to FixFeeder."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5.0)  # 5-second timeout
                sock.connect((self.host, self.port))
                sock.sendall(message.encode('utf-8'))
                
                if verbose:
                    # Replace SOH with | for readable output
                    readable_msg = message.replace('\x01', '|')
                    print(f"✓ Sent: {readable_msg}")
                
                return True
        except socket.error as e:
            print(f"✗ Failed to send message: {e}")
            return False
    
    def send_multiple_messages(self, messages: List[str], 
                             delay: float = 0.1, verbose: bool = False) -> int:
        """Send multiple messages with optional delay between sends."""
        success_count = 0
        
        for i, message in enumerate(messages, 1):
            if self.send_message(message, verbose):
                success_count += 1
            else:
                print(f"Failed to send message {i}/{len(messages)}")
            
            if delay > 0 and i < len(messages):
                time.sleep(delay)
        
        return success_count
    
    def simulate_trading_session(self, duration_seconds: int = 60, 
                               messages_per_second: float = 10.0,
                               verbose: bool = False) -> int:
        """Simulate a realistic trading session with mixed message types."""
        print(f"Starting {duration_seconds}s trading simulation...")
        print(f"Target rate: {messages_per_second} messages/second")
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        message_interval = 1.0 / messages_per_second
        messages_sent = 0
        
        # Message type distribution (realistic proportions)
        message_types = [
            ('new_order', 0.4),      # 40% new orders
            ('execution_report', 0.3), # 30% execution reports
            ('cancel_request', 0.15),  # 15% cancellations
            ('heartbeat', 0.15)        # 15% heartbeats
        ]
        
        while time.time() < end_time:
            # Select message type based on distribution
            rand = random.random()
            cumulative = 0
            selected_type = 'new_order'
            
            for msg_type, probability in message_types:
                cumulative += probability
                if rand <= cumulative:
                    selected_type = msg_type
                    break
            
            # Generate appropriate message
            if selected_type == 'new_order':
                message = self.generator.new_order_single()
            elif selected_type == 'execution_report':
                message = self.generator.execution_report()
            elif selected_type == 'cancel_request':
                message = self.generator.order_cancel_request()
            else:  # heartbeat
                message = self.generator.heartbeat()
            
            # Send message
            if self.send_message(message, verbose):
                messages_sent += 1
            
            # Wait for next message
            time.sleep(message_interval)
        
        actual_duration = time.time() - start_time
        actual_rate = messages_sent / actual_duration
        
        print(f"Simulation complete:")
        print(f"  Duration: {actual_duration:.1f}s")
        print(f"  Messages sent: {messages_sent}")
        print(f"  Actual rate: {actual_rate:.1f} messages/second")
        
        return messages_sent

def main():
    """Main CLI interface for the mock data sender."""
    parser = argparse.ArgumentParser(
        description="Send mock FIX messages to FixFeeder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Send a single new order
  python mock_data_sender.py --single new_order --symbol AAPL
  
  # Send 100 random messages
  python mock_data_sender.py --count 100 --delay 0.1
  
  # Run trading simulation for 5 minutes
  python mock_data_sender.py --simulate 300 --rate 20
  
  # Send specific message types
  python mock_data_sender.py --messages new_order,cancel_request --count 50
        """)
    
    parser.add_argument('--host', default='localhost',
                       help='FixFeeder host (default: localhost)')
    parser.add_argument('--port', type=int, default=9876,
                       help='FixFeeder port (default: 9876)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output showing sent messages')
    
    # Message sending modes
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--single', choices=['new_order', 'cancel_request', 
                                          'execution_report', 'heartbeat', 'test_request'],
                      help='Send a single message of specified type')
    group.add_argument('--count', type=int, 
                      help='Send specified number of random messages')
    group.add_argument('--simulate', type=int,
                      help='Run trading simulation for specified seconds')
    
    # Additional options
    parser.add_argument('--symbol', default=None,
                       help='Specific symbol to use (default: random)')
    parser.add_argument('--delay', type=float, default=0.1,
                       help='Delay between messages in seconds (default: 0.1)')
    parser.add_argument('--rate', type=float, default=10.0,
                       help='Messages per second for simulation (default: 10.0)')
    parser.add_argument('--messages', 
                       help='Comma-separated list of message types to send')
    
    args = parser.parse_args()
    
    # Create client
    client = FixFeederClient(args.host, args.port)
    
    # Test connection first
    print(f"Connecting to FixFeeder at {args.host}:{args.port}...")
    test_message = client.generator.heartbeat()
    if not client.send_message(test_message, False):
        print("Failed to connect to FixFeeder. Please check:")
        print("1. FixFeeder is running")
        print("2. Host and port are correct")
        print("3. No firewall blocking the connection")
        sys.exit(1)
    
    print("✓ Connected successfully")
    
    try:
        if args.single:
            # Send single message
            print(f"Sending single {args.single} message...")
            
            if args.single == 'new_order':
                message = client.generator.new_order_single(symbol=args.symbol)
            elif args.single == 'cancel_request':
                message = client.generator.order_cancel_request(symbol=args.symbol)
            elif args.single == 'execution_report':
                message = client.generator.execution_report(symbol=args.symbol)
            elif args.single == 'heartbeat':
                message = client.generator.heartbeat()
            elif args.single == 'test_request':
                message = client.generator.test_request()
            
            success = client.send_message(message, args.verbose)
            print(f"{'✓ Success' if success else '✗ Failed'}")
        
        elif args.count:
            # Send multiple random messages
            print(f"Sending {args.count} random messages...")
            
            messages = []
            for _ in range(args.count):
                msg_type = random.choice(['new_order', 'execution_report', 
                                        'cancel_request', 'heartbeat'])
                if msg_type == 'new_order':
                    message = client.generator.new_order_single(symbol=args.symbol)
                elif msg_type == 'execution_report':
                    message = client.generator.execution_report(symbol=args.symbol)
                elif msg_type == 'cancel_request':
                    message = client.generator.order_cancel_request(symbol=args.symbol)
                else:
                    message = client.generator.heartbeat()
                messages.append(message)
            
            success_count = client.send_multiple_messages(messages, args.delay, args.verbose)
            print(f"✓ Sent {success_count}/{args.count} messages successfully")
        
        elif args.simulate:
            # Run trading simulation
            messages_sent = client.simulate_trading_session(
                args.simulate, args.rate, args.verbose)
            print(f"✓ Trading simulation completed ({messages_sent} messages)")
    
    except KeyboardInterrupt:
        print("\n✗ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
