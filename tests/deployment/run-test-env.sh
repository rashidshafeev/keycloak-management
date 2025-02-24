#!/bin/bash

# Default values
REBUILD=false
REBUILD_ALL=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --rebuild)
            REBUILD=true
            shift
            ;;
        --rebuild-all)
            REBUILD_ALL=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo
            echo "Options:"
            echo "  --rebuild      Rebuild the container"
            echo "  --rebuild-all  Clean everything and rebuild from scratch"
            echo "  --help         Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to check container status
check_container_status() {
    if ! docker-compose -f docker-compose.test.yml ps | grep -q "Up"; then
        echo "Error: Containers failed to start. Checking logs..."
        docker-compose -f docker-compose.test.yml logs
        exit 1
    fi
}

# Function to display available commands
show_available_commands() {
    echo
    echo "Test environment is ready!"
    echo "Available commands:"
    echo "- View logs: docker-compose -f docker-compose.test.yml logs -f"
    echo "- Enter container: docker-compose -f docker-compose.test.yml exec vps-test bash"
    echo "- Stop environment: docker-compose -f docker-compose.test.yml down"
    echo "- Rebuild: $0 --rebuild"
    echo "- Full rebuild: $0 --rebuild-all"
}

# Handle different scenarios
if [ "$REBUILD_ALL" = true ]; then
    echo "Performing full rebuild..."
    
    # Clean up everything
    docker-compose -f docker-compose.test.yml down -v
    docker system prune -f
    
    # Build and start from scratch
    docker-compose -f docker-compose.test.yml build --no-cache --progress=plain
    docker-compose -f docker-compose.test.yml up -d
elif [ "$REBUILD" = true ]; then
    echo "Rebuilding container..."
    
    # Stop containers but keep volumes
    docker-compose -f docker-compose.test.yml down
    
    # Rebuild and start
    docker-compose -f docker-compose.test.yml build --progress=plain
    docker-compose -f docker-compose.test.yml up -d
else
    echo "Starting existing container..."
    
    # Try to start existing container
    if ! docker-compose -f docker-compose.test.yml up -d; then
        echo "No existing container found. Building..."
        docker-compose -f docker-compose.test.yml build --progress=plain
        docker-compose -f docker-compose.test.yml up -d
    fi
fi

echo "Test environment is starting..."
echo "Waiting for services to be ready..."
sleep 10

# Check container status
check_container_status

# Show available commands
show_available_commands
