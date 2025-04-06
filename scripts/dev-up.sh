#!/bin/bash

# Start docker-compose and ensure cleanup on Ctrl+C
trap 'echo -e "\n🧼 Gracefully stopping..."; docker-compose down' INT

docker-compose up --build
