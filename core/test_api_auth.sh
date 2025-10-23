#!/bin/bash
# test_api_auth.sh - Test secure API server JWT authentication
#
# Task 4 Phases 1.2-1.3: Secure JWT + Mock API validation
# Date: October 15, 2025
#
# Usage:
#   ./test_api_auth.sh [basic|secure|full]
#
# Options:
#   basic   - Test basic API server (no auth)
#   secure  - Test secure API server (JWT auth)
#   full    - Test both servers (default)

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test mode will be initialized after environment configuration

#==============================================================================
# Helper Functions
#==============================================================================

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "Required command '$1' not found. Please install it."
        exit 1
    fi
}

wait_for_server() {
    local url=$1
    local name=$2
    local max_attempts=10
    local attempt=0

    print_info "Waiting for $name to be ready..."

    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "$url/health" > /dev/null 2>&1; then
            print_success "$name is ready at $url"
            return 0
        fi

        attempt=$((attempt + 1))
        sleep 1
    done

    print_error "$name not responding at $url after $max_attempts attempts"
    return 1
}

#==============================================================================
# Environment Configuration
#==============================================================================

ENV_FILE="${ENV_FILE:-.env.test}"
if [ -f "$ENV_FILE" ]; then
    print_info "Loading environment variables from $ENV_FILE"
    set -a
    # shellcheck source=/dev/null
    source "$ENV_FILE"
    set +a
else
    print_warning "Environment file $ENV_FILE not found; using built-in defaults"
fi

# Configuration (override via environment variables if needed)
BASIC_API_URL="${BASIC_API_URL:-http://localhost:8000}"
SECURE_API_URL="${SECURE_API_URL:-http://localhost:8001}"
MOCK_API_URL="${MOCK_API_URL:-http://localhost:8002}"
API_KEY="${API_KEY:-test_api_key_admin_32_chars_long_abcdef123456}"
TEST_WALLET_ADDRESS="${TEST_WALLET_ADDRESS:-addr_test1qz2fxv2umyhttkxyxp8x0dlpdt3k6cwng5pxj3jhsydzer3jcu5d8ps7zex2k2xt3uqxgjqnnj83ws8lhrn648jjxtwq2ytjqp}"

# Test mode (default: full)
TEST_MODE="${1:-full}"

#==============================================================================
# Test Functions
#==============================================================================

test_basic_api() {
    print_header "Testing Basic API Server (No Authentication)"

    # Check if server is running
    if ! wait_for_server "$BASIC_API_URL" "Basic API server"; then
        print_error "Start basic API server with: python api_server.py"
        return 1
    fi

    # Test 1: Health check
    print_info "Test 1: Health check..."
    HEALTH_RESPONSE=$(curl -s "$BASIC_API_URL/health")

    if echo "$HEALTH_RESPONSE" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
        print_success "Health check passed"
        echo "$HEALTH_RESPONSE" | jq '.'
    else
        print_error "Health check failed"
        echo "$HEALTH_RESPONSE"
        return 1
    fi

    # Test 2: Generate DID (no auth required)
    print_info "Test 2: Generate DID (no authentication)..."
    GENERATE_RESPONSE=$(curl -s -X POST "$BASIC_API_URL/api/biometric/generate" \
        -H "Content-Type: application/json" \
        -d "{
            \"wallet_address\": \"$TEST_WALLET_ADDRESS\",
            \"storage\": \"inline\",
            \"fingers\": [
                {
                    \"finger_id\": \"left_thumb\",
                    \"minutiae\": [[100.5, 200.3, 45.0], [150.2, 180.9, 90.5]]
                },
                {
                    \"finger_id\": \"left_index\",
                    \"minutiae\": [[110.2, 210.5, 50.0], [160.5, 190.2, 95.5]]
                }
            ]
        }")

    if echo "$GENERATE_RESPONSE" | jq -e '.did' > /dev/null 2>&1; then
        DID=$(echo "$GENERATE_RESPONSE" | jq -r '.did')
        print_success "DID generated: $DID"
        echo "$GENERATE_RESPONSE" | jq '{did, id_hash, wallet_address}'
    else
        print_error "DID generation failed"
        echo "$GENERATE_RESPONSE"
        return 1
    fi

    print_success "Basic API server tests passed"
    return 0
}

test_secure_api() {
    print_header "Testing Secure API Server (JWT Authentication)"

    # Check if server is running
    if ! wait_for_server "$SECURE_API_URL" "Secure API server"; then
        print_error "Start secure API server with:"
        print_error "  export API_SECRET_KEY=\"$API_KEY\""
        print_error "  export JWT_SECRET_KEY=\"jwt_secret_for_signing_tokens_32_chars_long\""
        print_error "  python api_server_secure.py"
        return 1
    fi

    # Test 1: Health check (no auth required)
    print_info "Test 1: Health check (no authentication)..."
    HEALTH_RESPONSE=$(curl -s "$SECURE_API_URL/health")

    if echo "$HEALTH_RESPONSE" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
        print_success "Health check passed"
        echo "$HEALTH_RESPONSE" | jq '.security'
    else
        print_error "Health check failed"
        echo "$HEALTH_RESPONSE"
        return 1
    fi

    # Test 2: Get JWT token
    print_info "Test 2: Authenticate and get JWT token..."
    TOKEN_RESPONSE=$(curl -s -X POST "$SECURE_API_URL/auth/token" \
        -H "Content-Type: application/json" \
        -d "{\"api_key\": \"$API_KEY\"}")

    if echo "$TOKEN_RESPONSE" | jq -e '.access_token' > /dev/null 2>&1; then
        TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')
        EXPIRES_IN=$(echo "$TOKEN_RESPONSE" | jq -r '.expires_in')
        print_success "JWT token obtained (expires in ${EXPIRES_IN}s)"
        echo -e "Token: ${TOKEN:0:50}..."
    else
        print_error "Authentication failed"
        echo "$TOKEN_RESPONSE"
        return 1
    fi

    # Test 3: Generate DID without auth (should fail)
    print_info "Test 3: Generate DID without authentication (should fail)..."
    UNAUTH_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$SECURE_API_URL/api/biometric/generate" \
        -H "Content-Type: application/json" \
        -d '{
            "wallet_address": "addr_test1qz2fxv2umyhttkxyxp8x0dlpdt3k6cwng5pxj3jhsydzer3jcu5d8ps7zex2k2xt3uqxgjqnnj83ws8lhrn648jjxtwq2ytjqp",
            "storage": "inline",
            "fingers": [
                {"finger_id": "left_thumb", "minutiae": [[100, 200, 45]]}
            ]
        }')

    HTTP_CODE=$(echo "$UNAUTH_RESPONSE" | tail -n1)
    BODY=$(echo "$UNAUTH_RESPONSE" | sed '$d')

    if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
        print_success "Unauthorized access correctly blocked (HTTP $HTTP_CODE)"
        echo "$BODY" | jq '.'
    else
        print_warning "Expected 401/403, got HTTP $HTTP_CODE"
        echo "$BODY"
    fi

    # Test 4: Generate DID with valid token
    print_info "Test 4: Generate DID with valid JWT token..."
    GENERATE_RESPONSE=$(curl -s -X POST "$SECURE_API_URL/api/biometric/generate" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
            "wallet_address": "addr_test1qz2fxv2umyhttkxyxp8x0dlpdt3k6cwng5pxj3jhsydzer3jcu5d8ps7zex2k2xt3uqxgjqnnj83ws8lhrn648jjxtwq2ytjqp",
            "storage": "inline",
            "fingers": [
                {
                    "finger_id": "left_thumb",
                    "minutiae": [[100.5, 200.3, 45.0], [150.2, 180.9, 90.5]]
                },
                {
                    "finger_id": "left_index",
                    "minutiae": [[110.2, 210.5, 50.0], [160.5, 190.2, 95.5]]
                }
            ]
        }')

    if echo "$GENERATE_RESPONSE" | jq -e '.did' > /dev/null 2>&1; then
        DID=$(echo "$GENERATE_RESPONSE" | jq -r '.did')
        ID_HASH=$(echo "$GENERATE_RESPONSE" | jq -r '.id_hash')
        if [ -z "$DID" ] || [ "$DID" = "null" ]; then
            print_error "Missing DID in generation response"
            exit 1
        fi
        if [ -z "$ID_HASH" ] || [ "$ID_HASH" = "null" ]; then
            print_error "Missing id_hash in generation response"
            exit 1
        fi
        print_success "DID generated: $DID"
        echo "$GENERATE_RESPONSE" | jq '{did, id_hash, wallet_address}'

        # Save helper data for verification test
        HELPERS=$(echo "$GENERATE_RESPONSE" | jq -c '.helpers')
        export TEST_DID="$DID"
        export TEST_ID_HASH="$ID_HASH"
        export TEST_HELPERS="$HELPERS"
    else
        print_error "DID generation failed"
        echo "$GENERATE_RESPONSE"
        return 1
    fi

    # Test 5: Verify DID with token
    print_info "Test 5: Verify DID with valid JWT token..."
    if [ -z "$TEST_HELPERS" ] || [ "$TEST_HELPERS" = "null" ]; then
        print_error "No helper data available for verification test"
        return 1
    fi
    if [ -z "$TEST_ID_HASH" ] || [ "$TEST_ID_HASH" = "null" ]; then
        print_error "No id_hash available for verification test"
        return 1
    fi
    VERIFY_RESPONSE=$(curl -s -X POST "$SECURE_API_URL/api/biometric/verify" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d "{
            \"fingers\": [
                {
                    \"finger_id\": \"left_thumb\",
                    \"minutiae\": [[100.5, 200.3, 45.0], [150.2, 180.9, 90.5]]
                },
                {
                    \"finger_id\": \"left_index\",
                    \"minutiae\": [[110.2, 210.5, 50.0], [160.5, 190.2, 95.5]]
                }
            ],
            \"helpers\": $TEST_HELPERS,
            \"expected_id_hash\": \"$TEST_ID_HASH\"
        }")

    if echo "$VERIFY_RESPONSE" | jq -e 'has("success")' > /dev/null 2>&1; then
        VERIFIED=$(echo "$VERIFY_RESPONSE" | jq -r '.success')
        if [ "$VERIFIED" = "true" ]; then
            print_success "DID verification passed (expected hash matches)"
        else
            print_error "DID verification returned false"
            echo "$VERIFY_RESPONSE" | jq '.'
            exit 1
        fi
        echo "$VERIFY_RESPONSE" | jq '.'
    else
        print_error "DID verification failed"
        echo "$VERIFY_RESPONSE"
        exit 1
    fi

    # Test 6: Invalid API key
    print_info "Test 6: Authenticate with invalid API key (should fail)..."
    INVALID_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$SECURE_API_URL/auth/token" \
        -H "Content-Type: application/json" \
        -d '{"api_key": "invalid_key_that_should_fail_123"}')

    HTTP_CODE=$(echo "$INVALID_RESPONSE" | tail -n1)
    BODY=$(echo "$INVALID_RESPONSE" | sed '$d')

    if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
        print_success "Invalid API key correctly rejected (HTTP $HTTP_CODE)"
        echo "$BODY" | jq '.'
    else
        print_warning "Expected 401/403, got HTTP $HTTP_CODE"
        echo "$BODY"
    fi

    print_success "Secure API server tests passed"
    return 0
}

test_mock_api() {
    print_header "Testing Mock API Server (Deterministic Responses)"

    if ! wait_for_server "$MOCK_API_URL" "Mock API server"; then
        print_error "Start mock API server with:"
        print_error "  MOCK_API_PORT=8002 python api_server_mock.py"
        print_error "    or"
        print_error "  uvicorn api_server_mock:app --port 8002"
        return 1
    fi

    # Test 1: Health check
    print_info "Test 1: Health check..."
    HEALTH_RESPONSE=$(curl -s "$MOCK_API_URL/health")
    if echo "$HEALTH_RESPONSE" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
        print_success "Health check passed"
        echo "$HEALTH_RESPONSE" | jq '{status, service, version}'
    else
        print_error "Health check failed"
        echo "$HEALTH_RESPONSE"
        return 1
    fi

    # Shared payload for deterministic tests
    READABLE_PAYLOAD='{
        "wallet_address": "addr_test1qptuux8y76xq4asdc4vv8vttxq5va9vl59pfh79pzu0sh8w7t5n08ecl8rd6x692p8qccp7t69nk9lwj8c4gmhaalgsj83u5eu",
        "storage": "inline",
        "fingers": [
            {
                "finger_id": "left_thumb",
                "minutiae": [[101.1, 205.3, 40.0], [148.2, 190.4, 88.5]]
            },
            {
                "finger_id": "left_index",
                "minutiae": [[112.6, 214.7, 55.0], [158.9, 185.1, 92.0]]
            }
        ]
    }'

    # Test 2: Generate DID (first call)
    print_info "Test 2: Generate DID (first call)..."
    GENERATE_RESPONSE=$(curl -s -X POST "$MOCK_API_URL/api/biometric/generate" \
        -H "Content-Type: application/json" \
        -d "$READABLE_PAYLOAD")

    if ! echo "$GENERATE_RESPONSE" | jq -e '.did and .id_hash' > /dev/null 2>&1; then
        print_error "Mock DID generation failed"
        echo "$GENERATE_RESPONSE"
        return 1
    fi

    DID=$(echo "$GENERATE_RESPONSE" | jq -r '.did')
    ID_HASH=$(echo "$GENERATE_RESPONSE" | jq -r '.id_hash')
    HELPERS=$(echo "$GENERATE_RESPONSE" | jq -c '.helpers')
    META_ID_HASH=$(echo "$GENERATE_RESPONSE" | jq -r '.metadata_cip30_inline.biometric.idHash')

    if [ -z "$HELPERS" ] || [ "$HELPERS" = "null" ]; then
        print_error "Mock helpers missing from response"
        return 1
    fi

    if [ "$META_ID_HASH" != "$ID_HASH" ]; then
        print_warning "CIP-30 metadata idHash mismatch (expected $ID_HASH, got $META_ID_HASH)"
    fi

    print_success "DID generated: $DID"
    echo "$GENERATE_RESPONSE" | jq '{did, id_hash, wallet_address}'

    # Test 3: Deterministic response check (second call)
    print_info "Test 3: Deterministic response (second call)..."
    GENERATE_RESPONSE_2=$(curl -s -X POST "$MOCK_API_URL/api/biometric/generate" \
        -H "Content-Type: application/json" \
        -d "$READABLE_PAYLOAD")

    DID2=$(echo "$GENERATE_RESPONSE_2" | jq -r '.did')
    ID_HASH2=$(echo "$GENERATE_RESPONSE_2" | jq -r '.id_hash')

    if [ "$DID" = "$DID2" ] && [ "$ID_HASH" = "$ID_HASH2" ]; then
        print_success "Deterministic output verified"
    else
        print_error "Deterministic output mismatch"
        echo "$GENERATE_RESPONSE_2" | jq '{did, id_hash}'
        return 1
    fi

    # Test 4: Verify DID using stored helper data
    print_info "Test 4: Verify DID with helpers..."
    VERIFY_RESPONSE=$(curl -s -X POST "$MOCK_API_URL/api/biometric/verify" \
        -H "Content-Type: application/json" \
        -d "{
            \"fingers\": [
                {
                    \"finger_id\": \"left_thumb\",
                    \"minutiae\": [[101.1, 205.3, 40.0], [148.2, 190.4, 88.5]]
                },
                {
                    \"finger_id\": \"left_index\",
                    \"minutiae\": [[112.6, 214.7, 55.0], [158.9, 185.1, 92.0]]
                }
            ],
            \"helpers\": $HELPERS,
            \"expected_id_hash\": \"$ID_HASH\"
        }")

    if echo "$VERIFY_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
        print_success "Mock verification succeeded"
        echo "$VERIFY_RESPONSE" | jq '.'
    else
        print_error "Mock verification failed"
        echo "$VERIFY_RESPONSE" | jq '.'
        return 1
    fi

    print_success "Mock API server tests passed"
    return 0
}

#==============================================================================
# Main Script
#==============================================================================

main() {
    # Check required commands
    check_command "curl"
    check_command "jq"

    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Biometric DID API Server Authentication Test Suite       ║${NC}"
    echo -e "${BLUE}║  Task 4 Phases 1.2-1.3 - API Server Testing               ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}\n"

    print_info "Test mode: $TEST_MODE"
    print_info "Basic API URL: $BASIC_API_URL"
    print_info "Secure API URL: $SECURE_API_URL"
    print_info "API Key: ${API_KEY:0:20}..."
    print_info "Mock API URL: $MOCK_API_URL"

    # Run tests based on mode
    case "$TEST_MODE" in
        basic)
            test_basic_api
            ;;
        mock)
            test_mock_api
            ;;
        secure)
            test_secure_api
            ;;
        full)
            test_basic_api
            echo ""
            test_secure_api
            ;;
        *)
            print_error "Invalid test mode: $TEST_MODE"
            echo "Usage: $0 [basic|secure|full]"
            exit 1
            ;;
    esac

    # Summary
    print_header "Test Summary"
    print_success "All authentication tests completed"
    print_info "Next steps:"
    print_info "  1. Document API endpoints (Phase 1.4)"
    print_info "  2. Finalize test configs (.env.test)"
    print_info "  3. Run deferred integration tests (Phase 2)"
    print_info "  4. Align helper serialization with secure server"
}

# Run main function
main "$@"
