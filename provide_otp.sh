#!/bin/bash

# Helper script to provide OTP codes to debbit Docker container
# Usage: ./provide_otp.sh [merchant_id] [otp_code]

CONTAINER_NAME=${1:-"debbit"}
MERCHANT_ID=${2:-"default"}
OTP_CODE=${3}

if [ -z "$OTP_CODE" ]; then
    echo "Usage: $0 [container_name] [merchant_id] [otp_code]"
    echo ""
    echo "Examples:"
    echo "  $0 debbit example_card_description_example_merchant 123456"
    echo "  $0 debbit amazon_gift_card_reload 654321"
    echo ""
    echo "Or run interactively:"
    echo "  $0 debbit example_card_description_example_merchant"
    echo ""
    
    # Interactive mode
    if [ -n "$MERCHANT_ID" ] && [ "$MERCHANT_ID" != "default" ]; then
        echo -n "Enter OTP for $MERCHANT_ID: "
        read OTP_CODE
    else
        echo -n "Enter OTP: "
        read OTP_CODE
    fi
fi

if [ -z "$OTP_CODE" ]; then
    echo "Error: No OTP code provided"
    exit 1
fi

# Find the container
CONTAINER_ID=$(docker ps -q --filter "name=$CONTAINER_NAME" --filter "ancestor=debbit")

if [ -z "$CONTAINER_ID" ]; then
    echo "Error: No debbit container found with name '$CONTAINER_NAME'"
    echo "Available debbit containers:"
    docker ps --filter "ancestor=debbit" --format "table {{.Names}}\t{{.Status}}"
    exit 1
fi

echo "Providing OTP '$OTP_CODE' to container $CONTAINER_ID for merchant $MERCHANT_ID..."

# Execute the OTP provision command
docker exec -it "$CONTAINER_ID" python3 -c "import debbit; debbit.provide_otp('$MERCHANT_ID', '$OTP_CODE')"

if [ $? -eq 0 ]; then
    echo "✅ OTP provided successfully!"
else
    echo "❌ Failed to provide OTP"
    exit 1
fi 