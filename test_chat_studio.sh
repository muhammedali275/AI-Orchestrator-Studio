#!/bin/bash

# Chat Studio Test Script
# Tests all Chat Studio endpoints

echo "==================================="
echo "Chat Studio API Test Suite"
echo "==================================="
echo ""

BASE_URL="http://localhost:8000"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local data=$4
    
    echo -n "Testing: $description... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    elif [ "$method" = "DELETE" ]; then
        response=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE_URL$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
        echo "  Response: $body"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo "1. Backend Health Check"
echo "----------------------"
test_endpoint "GET" "/health" "Health endpoint"
echo ""

echo "2. Model Detection (Ollama)"
echo "---------------------------"
test_endpoint "GET" "/api/chat/ui/models" "Get available models"
echo ""

echo "3. Routing Profiles"
echo "-------------------"
test_endpoint "GET" "/api/chat/ui/profiles" "Get routing profiles"
echo ""

echo "4. Conversation Management"
echo "--------------------------"
# Create conversation
test_endpoint "POST" "/api/chat/ui/conversations" "Create new conversation" \
    '{"title":"Test Conversation","model_id":"llama3:8b","routing_profile":"direct_llm"}'

# List conversations
test_endpoint "GET" "/api/chat/ui/conversations" "List conversations"
echo ""

echo "5. Chat Functionality"
echo "---------------------"
test_endpoint "POST" "/api/chat/ui/send" "Send chat message" \
    '{"message":"Hello, this is a test","model_id":"llama3:8b","routing_profile":"direct_llm","use_memory":false}'
echo ""

echo "6. Prompt Profiles"
echo "------------------"
test_endpoint "GET" "/api/chat/ui/prompt-profiles" "Get prompt profiles"
echo ""

echo "7. Metrics"
echo "----------"
test_endpoint "GET" "/api/chat/ui/metrics" "Get chat metrics"
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
    exit 1
fi
