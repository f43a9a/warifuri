#!/bin/bash
set -euo pipefail

echo "Setting up demo project..."

# Create output directory
mkdir -p output

# Create configuration file
cat > output/config.json << EOF
{
  "project": "demo",
  "version": "1.0.0",
  "setup_date": "$(date -Iseconds)"
}
EOF

echo "Demo project setup completed successfully."
