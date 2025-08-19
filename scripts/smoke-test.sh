#!/bin/bash

# WhatsApp-AutoCoder Smoke Test Script
# This script verifies that the deployed service is healthy and responding.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get service URL as first argument
SERVICE_URL=$1

if [ -z "$SERVICE_URL" ]; then
    echo -e "${RED}Error: Service URL not provided${NC}"
    echo "Usage: ./scripts/smoke-test.sh <service_url>"
    exit 1
fi

HEALTH_ENDPOINT="${SERVICE_URL}/health"

echo -e "${GREEN}Running Smoke Tests for: $SERVICE_URL${NC}"
echo "=========================================="

# Test 1: Health Check
echo -e "${YELLOW}Test 1: Verifying health endpoint...${NC}"

STATUS_CODE=$(curl -o /dev/null -s -w "%{http_code}" $HEALTH_ENDPOINT)

if [ "$STATUS_CODE" -eq 200 ]; then
    echo -e "${GREEN}✅ Health check passed (Status: $STATUS_CODE)${NC}"
else
    echo -e "${RED}❌ Health check failed (Status: $STATUS_CODE)${NC}"
    exit 1
fi

# Test 2: Check health response body
echo -e "${YELLOW}Test 2: Verifying health response body...${NC}"

RESPONSE=$(curl -s $HEALTH_ENDPOINT)

if [[ "$RESPONSE" == *'"status":"ok"'* ]]; then
    echo -e "${GREEN}✅ Health response body is correct${NC}"
else
    echo -e "${RED}❌ Health response body is incorrect: $RESPONSE${NC}"
    exit 1
fi

# Test 3: Check API Docs (Swagger UI)
echo -e "${YELLOW}Test 3: Verifying API docs (Swagger UI)...${NC}"
DOCS_URL="${SERVICE_URL}/docs"

STATUS_CODE_DOCS=$(curl -o /dev/null -s -w "%{http_code}" $DOCS_URL)

if [ "$STATUS_CODE_DOCS" -eq 200 ]; then
    echo -e "${GREEN}✅ Swagger UI is accessible (Status: $STATUS_CODE_DOCS)${NC}"
else
    echo -e "${RED}❌ Swagger UI is not accessible (Status: $STATUS_CODE_DOCS)${NC}"
    exit 1
fi

# Test 4: Check Webhook Endpoint (HEAD request)
echo -e "${YELLOW}Test 4: Verifying webhook endpoint...${NC}"
WEBHOOK_URL="${SERVICE_URL}/webhook/whatsapp"

# Use HEAD request to avoid Twilio signature verification failure
STATUS_CODE_WEBHOOK=$(curl -o /dev/null -s -w "%{http_code}" -X HEAD $WEBHOOK_URL)

# Expect 405 Method Not Allowed (since we're not POSTing with signature)
if [ "$STATUS_CODE_WEBHOOK" -eq 405 ]; then
    echo -e "${GREEN}✅ Webhook endpoint is correctly configured (Status: $STATUS_CODE_WEBHOOK)${NC}"
else
    echo -e "${RED}❌ Webhook endpoint is not correctly configured (Status: $STATUS_CODE_WEBHOOK)${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 All smoke tests passed successfully!${NC}"

