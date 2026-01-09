#!/bin/bash

# Chat Studio Test Script
# Tests all Chat Studio endpoints with proper error handling

set -e  # Exit on error (can be disabled for continuing tests)

echo "==================================="
echo "Chat Studio API Test Suite"
echo "==================================="
echo ""

BASE_URL="${BASE_URL:-http://localhost:8000}"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Variables to store IDs
CONVERSATION_ID=""
MESSAGE_ID=""

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ PASSED${NC} $1"
}

print_failure() {
    echo -e "${RED}✗ FAILED${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local data=$4
    local expected_code=${5:-200}
    
    echo -n "Testing: $description... "
    
    # Build curl command based on method
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint" 2>&1)
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" 2>&1)
    elif [ "$method" = "DELETE" ]; then
        response=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE_URL$endpoint" 2>&1)
    elif [ "$method" = "PUT" ]; then
        response=$(curl -s -w "\n%{http_code}" -X PUT "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" 2>&1)
    fi
    
    # Extract HTTP code and body
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    # Check if curl succeeded
    if [[ ! "$http_code" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}✗ FAILED${NC} (Connection error)"
        echo "  Error: $response"
        FAILED=$((FAILED + 1))
        return 1
    fi
    
    # Check HTTP status code
    if [ "$http_code" -ge "$expected_code" ] && [ "$http_code" -lt $((expected_code + 100)) ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        PASSED=$((PASSED + 1))
        
        # Pretty print JSON response if available
        if command -v jq &> /dev/null && [ -n "$body" ]; then
            echo "$body" | jq '.' 2>/dev/null | head -n 10
        fi
        
        # Return the body for further processing
        echo "$body"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code, expected $expected_code)"
        echo "  Response: $body"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Function to extract JSON field
extract_json_field() {
    local json=$1
    local field=$2
    
    if command -v jq &> /dev/null; then
        echo "$json" | jq -r ".$field" 2>/dev/null
    else
        # Fallback to grep/sed if jq not available
        echo "$json" | grep -o "\"$field\":\"[^\"]*\"" | cut -d'"' -f4
    fi
}

# Check if server is running
echo "0. Connectivity Check"
echo "---------------------"
if ! curl -s --connect-timeout 5 "$BASE_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}✗ Cannot connect to $BASE_URL${NC}"
    echo "Please ensure the Chat Studio server is running."
    exit 1
fi
print_success "Server is reachable"
echo ""

echo "1. Backend Health Check"
echo "----------------------"
test_endpoint "GET" "/health" "Health endpoint" "" 200
echo ""

echo "2. LLM Connections Check"
echo "-------------------------"
connections_response=$(test_endpoint "GET" "/api/config/llm-connections" "Get LLM connections" "" 200)

# Extract first connection ID if available
if command -v jq &> /dev/null && [ -n "$connections_response" ]; then
    CONNECTION_ID=$(echo "$connections_response" | jq -r '.connections[0].id // empty' 2>/dev/null)
    if [ -n "$CONNECTION_ID" ]; then
        print_info "Found connection ID: $CONNECTION_ID"
        
        # Test fetching models from this connection
        models_from_conn=$(test_endpoint "GET" "/api/config/llm-connections/$CONNECTION_ID/models" \
            "Get models from connection" "" 200)
        
        if [ -n "$models_from_conn" ]; then
            print_info "Available models:"
            echo "$models_from_conn" | jq -r '.models[]? | "  - \(.id): \(.name // .id)"' 2>/dev/null || echo "$models_from_conn"
        fi
    fi
fi
echo ""

echo "3. Model Detection (Ollama)"
echo "---------------------------"
models_response=$(test_endpoint "GET" "/api/chat/ui/models" "Get available models" "" 200)
echo ""

echo "4. Routing Profiles"
echo "-------------------"
test_endpoint "GET" "/api/chat/ui/profiles" "Get routing profiles" "" 200
echo ""

echo "5. Prompt Profiles"
echo "------------------"
test_endpoint "GET" "/api/chat/ui/prompt-profiles" "Get prompt profiles" "" 200
echo ""

echo "6. Conversation Management"
echo "--------------------------"

# Create conversation
create_response=$(test_endpoint "POST" "/api/chat/ui/conversations" "Create new conversation" \
    '{"title":"Test Conversation","model_id":"sqlcoder:7b","routing_profile":"direct_llm"}' 200)

# Extract conversation ID if jq is available
if command -v jq &> /dev/null && [ -n "$create_response" ]; then
    CONVERSATION_ID=$(echo "$create_response" | jq -r '.id // .conversation_id // empty' 2>/dev/null)
    if [ -n "$CONVERSATION_ID" ]; then
        print_info "Created conversation ID: $CONVERSATION_ID"
    fi
fi

# List conversations
test_endpoint "GET" "/api/chat/ui/conversations" "List conversations" "" 200

# Get specific conversation if we have an ID
if [ -n "$CONVERSATION_ID" ]; then
    test_endpoint "GET" "/api/chat/ui/conversations/$CONVERSATION_ID" "Get specific conversation" "" 200
fi

echo ""

echo "7. Chat Functionality"
echo "---------------------"

# Test basic chat message with explicit connection_id and model_id
print_info "Testing with explicit connection_id and model_id (Ollama)"
chat_response=$(test_endpoint "POST" "/api/chat/ui/send" "Send chat message" \
    '{"message":"Hello, this is a test. Please respond briefly.","model_id":"sqlcoder:7b","connection_id":"llm-1767854937489","routing_profile":"direct_llm","use_memory":false}' 200)

# Test streaming endpoint
print_info "Testing streaming endpoint..."
echo -n "Testing: Chat streaming... "
stream_response=$(curl -s -X POST "$BASE_URL/api/chat/ui/send/stream" \
    -H "Content-Type: application/json" \
    -d '{"message":"Say hello in 3 words","model_id":"sqlcoder:7b","connection_id":"llm-1767854937489","routing_profile":"direct_llm","use_memory":false,"stream":true}' 2>&1)

if [ $? -eq 0 ] && [ -n "$stream_response" ]; then
    echo -e "${GREEN}✓ PASSED${NC}"
    echo "  First 200 chars: ${stream_response:0:200}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAILED${NC}"
    echo "  Error: $stream_response"
    FAILED=$((FAILED + 1))
fi

# Test chat with conversation ID if available
if [ -n "$CONVERSATION_ID" ]; then
    test_endpoint "POST" "/api/chat/ui/send" "Send message to specific conversation" \
        "{\"message\":\"Follow up message\",\"conversation_id\":\"$CONVERSATION_ID\",\"model_id\":\"sqlcoder:7b\",\"connection_id\":\"llm-1767854937489\",\"routing_profile\":\"direct_llm\"}" 200
fi

echo ""

echo "7. Message History"
echo "------------------"
if [ -n "$CONVERSATION_ID" ]; then
    test_endpoint "GET" "/api/chat/ui/conversations/$CONVERSATION_ID/messages" "Get conversation messages" "" 200
else
    print_info "Skipping - no conversation ID available"
fi
echo ""

echo "8. Metrics"
echo "----------"
test_endpoint "GET" "/api/chat/ui/metrics" "Get chat metrics" "" 200
echo ""

echo "9. Cleanup (Optional)"
echo "---------------------"
if [ -n "$CONVERSATION_ID" ]; then
    read -p "Delete test conversation? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        test_endpoint "DELETE" "/api/chat/ui/conversations/$CONVERSATION_ID" "Delete test conversation" "" 200
    else
        print_info "Keeping test conversation: $CONVERSATION_ID"
    fi
fi
echo ""

echo "==================================="
echo "Test Summary"
echo "==================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo "Total: $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed! ✗${NC}"
    echo -e "${YELLOW}Review the output above for details.${NC}"
    exit 1
fi