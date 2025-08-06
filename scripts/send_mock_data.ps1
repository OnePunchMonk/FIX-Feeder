# FixFeeder Mock Data Script - PowerShell Version
# Simple script to send FIX messages to FixFeeder for testing

param(
    [string]$Host = "localhost",
    [int]$Port = 9876,
    [switch]$Help
)

if ($Help) {
    Write-Host "FixFeeder Mock Data Sender - PowerShell"
    Write-Host ""
    Write-Host "Usage: .\send_mock_data.ps1 [-Host hostname] [-Port port] [-Help]"
    Write-Host ""
    Write-Host "Parameters:"
    Write-Host "  -Host    Target hostname (default: localhost)"
    Write-Host "  -Port    Target port (default: 9876)"
    Write-Host "  -Help    Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\send_mock_data.ps1"
    Write-Host "  .\send_mock_data.ps1 -Host 192.168.1.100 -Port 9876"
    exit 0
}

Write-Host "FixFeeder Mock Data Sender" -ForegroundColor Yellow
Write-Host "Connecting to $Host`:$Port"

# Function to send a message
function Send-FixMessage {
    param(
        [string]$Message,
        [string]$Description,
        [string]$TargetHost,
        [int]$TargetPort
    )
    
    Write-Host "Sending: $Description" -ForegroundColor Yellow
    
    try {
        # Create TCP client
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.Connect($TargetHost, $TargetPort)
        
        # Get stream and send message
        $stream = $tcpClient.GetStream()
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Message)
        $stream.Write($bytes, 0, $bytes.Length)
        
        # Close connection
        $stream.Close()
        $tcpClient.Close()
        
        Write-Host "✓ Message sent successfully" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "✗ Failed to send message: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    finally {
        if ($tcpClient) { $tcpClient.Dispose() }
    }
}

# Test connection first
Write-Host "Testing connection..." -ForegroundColor Yellow

try {
    $testClient = New-Object System.Net.Sockets.TcpClient
    $testClient.Connect($Host, $Port)
    $testClient.Close()
    Write-Host "✓ Connected to FixFeeder" -ForegroundColor Green
}
catch {
    Write-Host "✗ Cannot connect to FixFeeder at $Host`:$Port" -ForegroundColor Red
    Write-Host "Please ensure FixFeeder is running and accessible" -ForegroundColor Red
    exit 1
}
finally {
    if ($testClient) { $testClient.Dispose() }
}

# Sample FIX messages (using backticks for escape sequences in PowerShell)
$NEW_ORDER = "8=FIX.4.2`0135=D`0155=PS_TEST`0111=CMD_123`0154=1`0138=100`0152=20250807-00:30:00`0110=042`01"
$CANCEL_REQUEST = "8=FIX.4.2`0135=F`0111=CANCEL_001`0141=CMD_123`0155=PS_TEST`0154=1`0152=20250807-00:31:00`0110=156`01"
$EXECUTION_REPORT = "8=FIX.4.2`0135=8`0111=CMD_123`0117=EXEC_001`0155=PS_TEST`0154=1`0138=100`0132=100`0131=150.50`0152=20250807-00:32:00`0110=234`01"
$HEARTBEAT = "8=FIX.4.2`0135=0`0152=20250807-00:33:00`0110=067`01"

# Send sample messages
Write-Host ""
Write-Host "Sending sample FIX messages..." -ForegroundColor Cyan
Write-Host ""

$success = 0
$total = 4

if (Send-FixMessage -Message $NEW_ORDER -Description "New Order Single (Buy 100 PS_TEST)" -TargetHost $Host -TargetPort $Port) {
    $success++
}
Start-Sleep -Seconds 1

if (Send-FixMessage -Message $EXECUTION_REPORT -Description "Execution Report (Filled)" -TargetHost $Host -TargetPort $Port) {
    $success++
}
Start-Sleep -Seconds 1

if (Send-FixMessage -Message $CANCEL_REQUEST -Description "Order Cancel Request" -TargetHost $Host -TargetPort $Port) {
    $success++
}
Start-Sleep -Seconds 1

if (Send-FixMessage -Message $HEARTBEAT -Description "Heartbeat" -TargetHost $Host -TargetPort $Port) {
    $success++
}

Write-Host ""
Write-Host "Summary: $success/$total messages sent successfully" -ForegroundColor $(if ($success -eq $total) { "Green" } else { "Yellow" })
Write-Host ""

if ($success -eq $total) {
    Write-Host "All sample messages sent!" -ForegroundColor Green
} else {
    Write-Host "Some messages failed to send. Check FixFeeder logs for details." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "You can also use the Python mock data sender for more advanced testing:" -ForegroundColor Cyan
Write-Host "python scripts\mock_data_sender.py --help"
Write-Host ""
Write-Host "Or send individual messages using PowerShell:" -ForegroundColor Cyan
Write-Host "`$tcpClient = New-Object System.Net.Sockets.TcpClient('$Host', $Port)"
Write-Host "`$stream = `$tcpClient.GetStream()"
Write-Host "`$bytes = [System.Text.Encoding]::UTF8.GetBytes('YOUR_FIX_MESSAGE')"
Write-Host "`$stream.Write(`$bytes, 0, `$bytes.Length)"
Write-Host "`$tcpClient.Close()"
