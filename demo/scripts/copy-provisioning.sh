#!/bin/sh
# Copy provisioning files to Grafana volume (macOS Docker Desktop workaround)
# This script copies the datasources.yml file into the Docker volume
# since bind mounts have permission issues on macOS Docker Desktop

TARGET_VOLUME="demo_grafana_provisioning"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Copying Grafana provisioning files to volume ${TARGET_VOLUME}..."

# Copy datasources.yml using stdin to avoid bind mount permission issues
cat "${PROJECT_DIR}/grafana/provisioning/datasources/datasources.yml" | \
  docker run -i --rm -v ${TARGET_VOLUME}:/target alpine:latest sh -c "
    mkdir -p /target/datasources
    cat > /target/datasources/datasources.yml
    chmod 644 /target/datasources/datasources.yml
    echo 'Files copied successfully'
    ls -la /target/datasources/
  "

echo "Done! Restart Grafana to apply changes: docker-compose restart grafana"

