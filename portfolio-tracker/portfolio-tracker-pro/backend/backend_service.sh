#!/bin/bash
# Helper script to manage backend LaunchAgent service

PLIST_FILE="$HOME/Library/LaunchAgents/com.portfolio-tracker.backend.plist"
SERVICE_NAME="com.portfolio-tracker.backend"
BACKEND_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$BACKEND_DIR/backend.log"
ERROR_LOG="$BACKEND_DIR/backend.error.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

function print_error() {
    echo -e "${RED}✗${NC} $1"
}

function print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

function check_plist_exists() {
    if [ ! -f "$PLIST_FILE" ]; then
        print_error "LaunchAgent plist not found: $PLIST_FILE"
        echo "Please create the plist file first."
        exit 1
    fi
}

function start_service() {
    check_plist_exists
    
    # Check if already loaded (using bootstrap domain)
    if launchctl list | grep -q "$SERVICE_NAME" || launchctl print "gui/$(id -u)/$SERVICE_NAME" >/dev/null 2>&1; then
        print_warning "Service is already running"
        return
    fi
    
    # Use bootstrap for newer macOS (10.13+), fallback to load for older versions
    if launchctl bootstrap --help >/dev/null 2>&1; then
        # Newer macOS: use bootstrap
        launchctl bootstrap "gui/$(id -u)" "$PLIST_FILE" 2>/dev/null
        if [ $? -eq 0 ]; then
            print_status "Service started successfully (bootstrap)"
            echo "Service will start automatically on login"
        else
            print_error "Failed to start service (bootstrap)"
            echo "Trying to check if service is already running..."
            launchctl list | grep "$SERVICE_NAME" || echo "Service not found in list"
            exit 1
        fi
    else
        # Older macOS: use load
        launchctl load "$PLIST_FILE" 2>/dev/null
        if [ $? -eq 0 ]; then
            print_status "Service started successfully (load)"
            echo "Service will start automatically on login"
        else
            print_error "Failed to start service (load)"
            exit 1
        fi
    fi
}

function stop_service() {
    check_plist_exists
    
    # Check if loaded (using bootstrap domain)
    local is_running=false
    if launchctl list | grep -q "$SERVICE_NAME" || launchctl print "gui/$(id -u)/$SERVICE_NAME" >/dev/null 2>&1; then
        is_running=true
    fi
    
    if [ "$is_running" = false ]; then
        print_warning "Service is not running"
        return
    fi
    
    # Use bootout for newer macOS (10.13+), fallback to unload for older versions
    if launchctl bootout --help >/dev/null 2>&1; then
        # Newer macOS: use bootout
        launchctl bootout "gui/$(id -u)/$SERVICE_NAME" 2>/dev/null
        if [ $? -eq 0 ]; then
            print_status "Service stopped successfully (bootout)"
        else
            # Fallback: try to unload the plist file
            launchctl unload "$PLIST_FILE" 2>/dev/null
            if [ $? -eq 0 ]; then
                print_status "Service stopped successfully (unload fallback)"
            else
                print_error "Failed to stop service"
                exit 1
            fi
        fi
    else
        # Older macOS: use unload
        launchctl unload "$PLIST_FILE" 2>/dev/null
        if [ $? -eq 0 ]; then
            print_status "Service stopped successfully (unload)"
        else
            print_error "Failed to stop service"
            exit 1
        fi
    fi
}

function restart_service() {
    print_warning "Restarting service..."
    stop_service
    sleep 2
    start_service
}

function status_service() {
    check_plist_exists
    
    echo "Service Status:"
    echo "==============="
    
    # Check if running (try both methods)
    local is_running=false
    if launchctl list | grep -q "$SERVICE_NAME"; then
        is_running=true
    elif launchctl print "gui/$(id -u)/$SERVICE_NAME" >/dev/null 2>&1; then
        is_running=true
    fi
    
    if [ "$is_running" = true ]; then
        print_status "Service is RUNNING"
        echo ""
        echo "Service details:"
        # Try to get service info
        if launchctl print "gui/$(id -u)/$SERVICE_NAME" >/dev/null 2>&1; then
            launchctl print "gui/$(id -u)/$SERVICE_NAME" 2>/dev/null | head -20
        else
            launchctl list "$SERVICE_NAME" 2>/dev/null | grep -v "com.apple" || echo "Service running but details not available"
        fi
    else
        print_warning "Service is NOT RUNNING"
    fi
    
    echo ""
    echo "Plist file: $PLIST_FILE"
    echo "Backend directory: $BACKEND_DIR"
    echo "Log file: $LOG_FILE"
    echo "Error log: $ERROR_LOG"
}

function show_logs() {
    local lines=${1:-50}
    
    if [ -f "$LOG_FILE" ]; then
        echo "=== Backend Log (last $lines lines) ==="
        tail -n "$lines" "$LOG_FILE"
    else
        print_warning "Log file not found: $LOG_FILE"
    fi
    
    echo ""
    
    if [ -f "$ERROR_LOG" ]; then
        echo "=== Error Log (last $lines lines) ==="
        tail -n "$lines" "$ERROR_LOG"
    else
        print_warning "Error log not found: $ERROR_LOG"
    fi
}

function show_help() {
    echo "Backend Service Manager"
    echo "======================"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start    - Start the backend service"
    echo "  stop     - Stop the backend service"
    echo "  restart  - Restart the backend service"
    echo "  status   - Show service status"
    echo "  logs     - Show service logs (default: last 50 lines)"
    echo "  logs N   - Show last N lines of logs"
    echo "  help     - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 status"
    echo "  $0 logs 100"
}

# Main command dispatcher
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        status_service
        ;;
    logs)
        show_logs "$2"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        if [ -z "$1" ]; then
            show_help
        else
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
        fi
        ;;
esac

