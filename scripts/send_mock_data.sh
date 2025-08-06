#!/bin/bash

# FixFeeder Mock Data Script
# Simple script to send FIX messages to FixFeeder for testing

HOST=${HOST:-localhost}
PORT=${PORT:-9876}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}FixFeeder Mock Data Sender${NC}"
echo "Connecting to $HOST:$PORT"

# Check if netcat is available
if ! command -v nc &> /dev/null; then
    echo -e "${RED}Error: netcat (nc) is required but not installed${NC}"
    echo "Please install netcat: sudo apt-get install netcat (Ubuntu/Debian) or brew install netcat (macOS)"
    exit 1
fi

# Test connection
if ! nc -z "$HOST" "$PORT" 2>/dev/null; then
    echo -e "${RED}Error: Cannot connect to FixFeeder at $HOST:$PORT${NC}"
    echo "Please ensure FixFeeder is running and accessible"
    exit 1
fi

echo -e "${GREEN}✓ Connected to FixFeeder${NC}"

# Function to send a message
send_message() {
    local message="$1"
    local description="$2"
    
    echo -e "${YELLOW}Sending: $description${NC}"
    echo -e "$message" | nc "$HOST" "$PORT"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Message sent successfully${NC}"
    else
        echo -e "${RED}✗ Failed to send message${NC}"
    fi
    echo
}

# Sample FIX messages
NEW_ORDER="8=FIX.4.2\x0135=D\x0155=BASH_TEST\x0111=CMD_123\x0154=1\x0138=100\x0152=20250807-00:30:00\x0110=042\x01"
CANCEL_REQUEST="8=FIX.4.2\x0135=F\x0111=CANCEL_001\x0141=CMD_123\x0155=BASH_TEST\x0154=1\x0152=20250807-00:31:00\x0110=156\x01"
EXECUTION_REPORT="8=FIX.4.2\x0135=8\x0111=CMD_123\x0117=EXEC_001\x0155=BASH_TEST\x0154=1\x0138=100\x0132=100\x0131=150.50\x0152=20250807-00:32:00\x0110=234\x01"
HEARTBEAT="8=FIX.4.2\x0135=0\x0152=20250807-00:33:00\x0110=067\x01"

# Send sample messages
echo "Sending sample FIX messages..."
echo

send_message "$NEW_ORDER" "New Order Single (Buy 100 BASH_TEST)"
sleep 1

send_message "$EXECUTION_REPORT" "Execution Report (Filled)"
sleep 1

send_message "$CANCEL_REQUEST" "Order Cancel Request"
sleep 1

send_message "$HEARTBEAT" "Heartbeat"

echo -e "${GREEN}All sample messages sent!${NC}"
echo
echo "You can also send custom messages using:"
echo "echo -e 'YOUR_FIX_MESSAGE' | nc $HOST $PORT"
echo
echo "Example with the provided test message:"
echo "echo -e '$NEW_ORDER' | nc $HOST $PORT"
