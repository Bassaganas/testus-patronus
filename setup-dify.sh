#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up Dify project...${NC}"

# Check if Dify directory already exists
if [ -d "dify" ]; then
    echo -e "${YELLOW}Dify directory already exists.${NC}"
    echo -e "${YELLOW}If you want to reinstall, please remove the existing 'dify' directory first.${NC}"
    exit 0
fi

# Clone the Dify repository
echo -e "${YELLOW}Cloning Dify repository...${NC}"
if git clone https://github.com/langgenius/dify.git; then
    echo -e "${GREEN}Successfully cloned Dify repository!${NC}"
else
    echo -e "${RED}Failed to clone Dify repository. Please check your internet connection and try again.${NC}"
    exit 1
fi

# Navigate to Dify docker directory
echo -e "${YELLOW}Setting up Dify environment...${NC}"
cd dify/docker || {
    echo -e "${RED}Failed to navigate to dify/docker directory${NC}"
    exit 1
}

# Copy environment configuration file
echo -e "${YELLOW}Copying environment configuration...${NC}"
if [ -f ".env.example" ]; then
    cp .env.example .env
    echo -e "${GREEN}Environment configuration copied successfully!${NC}"
else
    echo -e "${RED}Failed to find .env.example file${NC}"
    exit 1
fi

# Start Docker containers
echo -e "${YELLOW}Starting Docker containers...${NC}"
if command -v docker-compose &> /dev/null; then
    # Using docker-compose v1
    docker-compose up -d
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    # Using docker compose v2
    docker compose up -d
else
    echo -e "${RED}Neither docker-compose nor docker compose is available. Please install Docker and Docker Compose first.${NC}"
    exit 1
fi

# Check if containers are running
echo -e "${YELLOW}Checking container status...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose ps
else
    docker compose ps
fi

echo -e "${GREEN}Dify setup completed!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Access the administrator initialization page at: ${GREEN}http://localhost/install${NC}"
echo -e "2. Set up your admin account"
echo -e "3. Access the Dify web interface at: ${GREEN}http://localhost${NC}"
echo -e "${YELLOW}Note: Make sure Docker Desktop is running and has at least 2 vCPUs and 8GB of memory allocated.${NC}" 