#!/bin/bash

# Create the node_exporter service file
sudo tee /etc/systemd/system/node_exporter.service > /dev/null <<EOF
[Unit]
Description=Node Exporter

[Service]
ExecStart=/home/ubuntu/node_exporter

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd to pick up the new service file
sudo systemctl daemon-reload

# Start the node_exporter service
sudo systemctl start node_exporter.service

# Check the status of the node_exporter service
# sudo systemctl status node_exporter.service

# Enable the node_exporter service to start on boot
sudo systemctl enable node_exporter.service
