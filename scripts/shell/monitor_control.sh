#!/bin/bash
# monitor_control.sh
# Control script for email monitoring daemon

BDS_DIR="$HOME/Desktop/BDS_SYSTEM"
SCRIPTS_DIR="$BDS_DIR/02_SCRIPTS/ACTIVE"
PID_FILE="$BDS_DIR/monitor.pid"
LOG_FILE="$BDS_DIR/monitor.log"

start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "❌ Daemon already running (PID: $PID)"
            return 1
        else
            rm "$PID_FILE"
        fi
    fi
    
    echo "🚀 Starting email monitoring daemon..."
    nohup python3 "$SCRIPTS_DIR/email_monitor_daemon.py" > /dev/null 2>&1 &
    echo $! > "$PID_FILE"
    echo "✅ Daemon started (PID: $(cat $PID_FILE))"
    echo "📋 Logs: tail -f $LOG_FILE"
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "❌ Daemon not running (no PID file)"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "🛑 Stopping daemon (PID: $PID)..."
        kill $PID
        rm "$PID_FILE"
        echo "✅ Daemon stopped"
    else
        echo "❌ Daemon not running (stale PID file)"
        rm "$PID_FILE"
    fi
}

status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "✅ Daemon running (PID: $PID)"
            echo "📋 Logs: tail -f $LOG_FILE"
            
            # Show last few log lines
            if [ -f "$LOG_FILE" ]; then
                echo ""
                echo "Recent activity:"
                tail -n 5 "$LOG_FILE"
            fi
        else
            echo "❌ Daemon not running (stale PID file)"
            rm "$PID_FILE"
        fi
    else
        echo "❌ Daemon not running"
    fi
}

logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "❌ No log file found"
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 2
        start
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the monitoring daemon"
        echo "  stop    - Stop the monitoring daemon"
        echo "  restart - Restart the monitoring daemon"
        echo "  status  - Check if daemon is running"
        echo "  logs    - Tail the log file (Ctrl+C to exit)"
        exit 1
        ;;
esac
