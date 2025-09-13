#!/bin/bash
# Send test webhook notification to diun-dash for development testing

set -e

# Default values
WEBHOOK_URL="http://localhost:8554/webhook"
WEBHOOK_TOKEN="${DIUN_WEBHOOK_TOKEN:-dev-webhook-token}"

# Random defaults
DEFAULT_HOSTNAME="test-server-$(( RANDOM % 100 ))"
DEFAULT_STATUS="new"
DEFAULT_PROVIDER="docker"
DEFAULT_IMAGE="nginx:$(( RANDOM % 10 + 1 ))"
DEFAULT_DIGEST="sha256:$(openssl rand -hex 32)"
DEFAULT_CREATED=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
DEFAULT_HUB_LINK="https://hub.docker.com/_/nginx"

# Parse command line arguments
HOSTNAME="$DEFAULT_HOSTNAME"
STATUS="$DEFAULT_STATUS"
PROVIDER="$DEFAULT_PROVIDER"
IMAGE="$DEFAULT_IMAGE"
DIGEST="$DEFAULT_DIGEST"
CREATED="$DEFAULT_CREATED"
HUB_LINK="$DEFAULT_HUB_LINK"

while [[ $# -gt 0 ]]; do
    case $1 in
        --server|--hostname)
            HOSTNAME="$2"
            shift 2
            ;;
        --image)
            IMAGE="$2"
            shift 2
            ;;
        --status)
            STATUS="$2"
            shift 2
            ;;
        --provider)
            PROVIDER="$2"
            shift 2
            ;;
        --digest)
            DIGEST="$2"
            shift 2
            ;;
        --created)
            CREATED="$2"
            shift 2
            ;;
        --hub-link)
            HUB_LINK="$2"
            shift 2
            ;;
        --url)
            WEBHOOK_URL="$2"
            shift 2
            ;;
        --token)
            WEBHOOK_TOKEN="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Send a test webhook notification to diun-dash for development testing"
            echo ""
            echo "Options:"
            echo "  --server, --hostname NAME    Server hostname (default: random test-server-XX)"
            echo "  --image IMAGE                Docker image with tag (default: random nginx:X)" 
            echo "  --status STATUS              Update status (default: new)"
            echo "  --provider PROVIDER          Provider type (default: docker)"
            echo "  --digest DIGEST              SHA256 digest (default: random)"
            echo "  --created TIMESTAMP          ISO 8601 timestamp (default: current time)"
            echo "  --hub-link URL               Registry link (default: nginx hub link)"
            echo "  --url URL                    Webhook URL (default: http://localhost:8554/webhook)"
            echo "  --token TOKEN                Auth token (default: \$DIUN_WEBHOOK_TOKEN or dev-webhook-token)"
            echo "  --help, -h                   Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                          # Send random notification"
            echo "  $0 --server prod-web --image nginx:alpine  # Specific server and image"
            echo "  $0 --status updated --provider kubernetes  # Different status and provider"
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Create the JSON payload
PAYLOAD=$(cat <<EOF
{
    "hostname": "$HOSTNAME",
    "status": "$STATUS", 
    "provider": "$PROVIDER",
    "image": "$IMAGE",
    "digest": "$DIGEST",
    "created": "$CREATED",
    "hub_link": "$HUB_LINK",
    "diun_version": "4.24.0",
    "mime_type": "application/vnd.docker.distribution.manifest.list.v2+json",
    "platform": "linux/amd64",
    "metadata": {
        "test": true,
        "sent_by": "send-test-notification.sh"
    }
}
EOF
)

echo "🚀 Sending test webhook notification..."
echo "📡 URL: $WEBHOOK_URL" 
echo "🔑 Token: $WEBHOOK_TOKEN"
echo "🖥️  Server: $HOSTNAME"
echo "🐳 Image: $IMAGE"
echo "📊 Status: $STATUS"
echo ""

# Send the webhook
if command -v curl >/dev/null 2>&1; then
    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: $WEBHOOK_TOKEN" \
        -d "$PAYLOAD" \
        "$WEBHOOK_URL")
    
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1 2>/dev/null || echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        echo "✅ Success! Webhook sent successfully"
        echo "📝 Response: $body"
    else
        echo "❌ Failed! HTTP $http_code"
        echo "📝 Response: $body"
        exit 1
    fi
elif command -v httpie >/dev/null 2>&1; then
    http POST "$WEBHOOK_URL" \
        Authorization:"$WEBHOOK_TOKEN" \
        Content-Type:application/json \
        hostname="$HOSTNAME" \
        status="$STATUS" \
        provider="$PROVIDER" \
        image="$IMAGE" \
        digest="$DIGEST" \
        created="$CREATED" \
        hub_link="$HUB_LINK" \
        diun_version="4.24.0" \
        mime_type="application/vnd.docker.distribution.manifest.list.v2+json" \
        platform="linux/amd64" \
        metadata:='{"test":true,"sent_by":"send-test-notification.sh"}'
else
    echo "❌ Error: Neither curl nor httpie is available"
    echo "Please install curl or httpie to send HTTP requests"
    exit 1
fi

echo ""
echo "🎯 You can now check the dashboard at http://localhost:8554"