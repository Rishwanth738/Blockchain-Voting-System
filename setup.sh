#!/bin/bash
# ============================================================
# SecureVoting - Startup Setup Script
# Run this ONCE before starting the services each session.
# It auto-detects your local Wi-Fi IP and writes it to .env files.
# ============================================================

echo "🔍 Detecting local Wi-Fi IP..."
IP=$(ipconfig | grep -A 4 "Wi-Fi" | grep "IPv4" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | head -1)

if [ -z "$IP" ]; then
  echo "❌ Could not detect Wi-Fi IP. Make sure you are connected to Wi-Fi."
  exit 1
fi

echo "🌐 Detected IP: $IP"
echo ""

# --- Update face-verification-service/.env ---
FACE_ENV="face-verification-service/.env"
if grep -q "^LOCAL_IP=" "$FACE_ENV"; then
  sed -i "s/^LOCAL_IP=.*/LOCAL_IP=$IP/" "$FACE_ENV"
else
  echo "LOCAL_IP=$IP" >> "$FACE_ENV"
fi
echo "✅ Updated LOCAL_IP in $FACE_ENV"

# --- Update frontend/.env.local ---
FRONTEND_ENV="frontend/.env.local"
if grep -q "^NEXT_PUBLIC_LOCAL_IP=" "$FRONTEND_ENV"; then
  sed -i "s/^NEXT_PUBLIC_LOCAL_IP=.*/NEXT_PUBLIC_LOCAL_IP=$IP/" "$FRONTEND_ENV"
else
  echo "NEXT_PUBLIC_LOCAL_IP=$IP" >> "$FRONTEND_ENV"
fi
echo "✅ Updated NEXT_PUBLIC_LOCAL_IP in $FRONTEND_ENV"

echo ""
echo "🎉 IP setup complete!"
echo "    Now start your 4 services in separate terminals (see README)."
