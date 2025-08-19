#!/bin/bash

# WhatsApp-AutoCoder Google Cloud Setup Script
# This script sets up the necessary Google Cloud resources for deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo -e "${GREEN}WhatsApp-AutoCoder Google Cloud Setup${NC}"
echo "======================================"
echo ""

# Step 1: Select existing project
echo -e "${GREEN}Step 1: Select Google Cloud Project${NC}"
echo ""

# List available projects
echo -e "${YELLOW}Available Google Cloud Projects:${NC}"
gcloud projects list --format="table(projectId,name,projectNumber)" 2>/dev/null || {
    echo -e "${RED}No projects found or not authenticated${NC}"
    echo "Please run: gcloud auth login"
    exit 1
}

echo ""
read -p "Enter your existing project ID (or press Enter to use current): " USER_PROJECT_ID

# Use current project if none specified
if [ -z "$USER_PROJECT_ID" ]; then
    GCP_PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$GCP_PROJECT_ID" ]; then
        echo -e "${RED}No project set and none provided${NC}"
        echo "Please specify a project ID"
        exit 1
    fi
    echo -e "${GREEN}Using current project: $GCP_PROJECT_ID${NC}"
else
    GCP_PROJECT_ID="$USER_PROJECT_ID"
    echo -e "${GREEN}Using project: $GCP_PROJECT_ID${NC}"
fi

# Verify project exists
if ! gcloud projects describe $GCP_PROJECT_ID &>/dev/null; then
    echo -e "${RED}Error: Project $GCP_PROJECT_ID not found${NC}"
    exit 1
fi

gcloud config set project $GCP_PROJECT_ID

# Configuration
export GCP_PROJECT_ID
export GCP_REGION="${GCP_REGION:-us-central1}"
export GCP_ARTIFACT_REGISTRY="${GCP_ARTIFACT_REGISTRY:-autocoder}"
export SA_NAME="github-actions-whatsapp"
export SA_EMAIL="$SA_NAME@$GCP_PROJECT_ID.iam.gserviceaccount.com"

echo ""
echo -e "${YELLOW}Project: $GCP_PROJECT_ID${NC}"
echo -e "${YELLOW}Region: $GCP_REGION${NC}"
echo ""

# Step 2: Enable required APIs
echo -e "${GREEN}Step 2: Enabling Required APIs${NC}"
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com \
    iam.googleapis.com \
    cloudresourcemanager.googleapis.com

echo "APIs enabled successfully"

# Step 3: Create or Select Artifact Registry repository
echo -e "${GREEN}Step 3: Setting up Artifact Registry${NC}"
echo ""

# List existing repositories
echo -e "${YELLOW}Existing Artifact Registries in $GCP_REGION:${NC}"
EXISTING_REPOS=$(gcloud artifacts repositories list --location=$GCP_REGION --format="value(name)" 2>/dev/null)

if [ -n "$EXISTING_REPOS" ]; then
    echo "$EXISTING_REPOS"
    echo ""
    read -p "Enter repository name to use (or press Enter to create new 'autocoder'): " USER_REPO
    
    if [ -n "$USER_REPO" ]; then
        GCP_ARTIFACT_REGISTRY="$USER_REPO"
        echo -e "${GREEN}Using existing repository: $GCP_ARTIFACT_REGISTRY${NC}"
    else
        GCP_ARTIFACT_REGISTRY="autocoder"
        if ! gcloud artifacts repositories describe $GCP_ARTIFACT_REGISTRY --location=$GCP_REGION &>/dev/null; then
            gcloud artifacts repositories create $GCP_ARTIFACT_REGISTRY \
                --repository-format=docker \
                --location=$GCP_REGION \
                --description="Docker images for WhatsApp-AutoCoder"
            echo -e "${GREEN}Created new repository: $GCP_ARTIFACT_REGISTRY${NC}"
        else
            echo -e "${GREEN}Using existing repository: $GCP_ARTIFACT_REGISTRY${NC}"
        fi
    fi
else
    GCP_ARTIFACT_REGISTRY="autocoder"
    echo "No existing repositories found. Creating new one..."
    gcloud artifacts repositories create $GCP_ARTIFACT_REGISTRY \
        --repository-format=docker \
        --location=$GCP_REGION \
        --description="Docker images for WhatsApp-AutoCoder"
    echo -e "${GREEN}Created new repository: $GCP_ARTIFACT_REGISTRY${NC}"
fi

export GCP_ARTIFACT_REGISTRY

# Step 4: Create Service Account
echo -e "${GREEN}Step 4: Creating Service Account${NC}"
if ! gcloud iam service-accounts describe $SA_EMAIL &>/dev/null; then
    gcloud iam service-accounts create $SA_NAME \
        --display-name="GitHub Actions Deploy"
    
    # Wait for propagation
    echo "Waiting for service account to propagate..."
    sleep 15
    
    # Verify creation with retries
    for i in {1..5}; do
        if gcloud iam service-accounts describe $SA_EMAIL &>/dev/null; then
            echo "✅ Service account created"
            break
        fi
        echo "Waiting... (attempt $i/5)"
        sleep 5
    done
else
    echo "Service account already exists"
fi

# Step 5: Grant permissions
echo -e "${GREEN}Step 5: Granting IAM Permissions${NC}"
ROLES=(
    "roles/run.admin"
    "roles/artifactregistry.admin"
    "roles/iam.serviceAccountUser"
    "roles/cloudbuild.builds.editor"
    "roles/storage.admin"
    "roles/secretmanager.admin"
)

for role in "${ROLES[@]}"; do
    echo "Adding role: $role"
    for attempt in {1..3}; do
        if gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
            --member="serviceAccount:$SA_EMAIL" \
            --role="$role" \
            --quiet 2>/dev/null; then
            echo "  ✓ Role added"
            break
        fi
        echo "  Retrying... (attempt $attempt/3)"
        sleep 5
    done
done

# Step 6: Create secrets
echo -e "${GREEN}Step 6: Creating Secret Manager Secrets${NC}"
echo ""
echo -e "${YELLOW}Please prepare the following values:${NC}"
echo "1. Twilio Account SID"
echo "2. Twilio Auth Token"
echo "3. Allowed Phone Numbers (comma-separated)"
echo ""

read -p "Do you want to create secrets now? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Create Twilio Account SID secret
    read -p "Enter Twilio Account SID: " TWILIO_SID
    echo -n "$TWILIO_SID" | gcloud secrets create TWILIO_ACCOUNT_SID --data-file=- 2>/dev/null || \
        echo "Secret TWILIO_ACCOUNT_SID already exists"
    
    # Create Twilio Auth Token secret
    read -s -p "Enter Twilio Auth Token: " TWILIO_TOKEN
    echo ""
    echo -n "$TWILIO_TOKEN" | gcloud secrets create TWILIO_AUTH_TOKEN --data-file=- 2>/dev/null || \
        echo "Secret TWILIO_AUTH_TOKEN already exists"
    
    # Create Allowed Phone Numbers secret
    read -p "Enter Allowed Phone Numbers (comma-separated): " PHONE_NUMBERS
    echo -n "$PHONE_NUMBERS" | gcloud secrets create ALLOWED_PHONE_NUMBERS --data-file=- 2>/dev/null || \
        echo "Secret ALLOWED_PHONE_NUMBERS already exists"
    
    # Grant access to secrets
    for secret in TWILIO_ACCOUNT_SID TWILIO_AUTH_TOKEN ALLOWED_PHONE_NUMBERS; do
        gcloud secrets add-iam-policy-binding $secret \
            --member="serviceAccount:$SA_EMAIL" \
            --role="roles/secretmanager.secretAccessor" --quiet 2>/dev/null || true
    done
fi

# Step 7: Generate service account key
echo -e "${GREEN}Step 7: Generating Service Account Key${NC}"
KEY_FILE="gcp-key.json"

if [ ! -f "$KEY_FILE" ]; then
    gcloud iam service-accounts keys create $KEY_FILE \
        --iam-account=$SA_EMAIL
    
    echo ""
    echo -e "${GREEN}✅ Setup Complete!${NC}"
    echo ""
    echo -e "${YELLOW}IMPORTANT: Add the following GitHub Secrets:${NC}"
    echo "1. GCP_PROJECT_ID: $GCP_PROJECT_ID"
    echo "2. GCP_SA_KEY: (contents of $KEY_FILE)"
    echo ""
    echo "To copy the service account key to clipboard (macOS):"
    echo "  cat $KEY_FILE | pbcopy"
    echo ""
    echo "To copy the service account key to clipboard (Linux):"
    echo "  cat $KEY_FILE | xclip -selection clipboard"
    echo ""
    echo -e "${RED}⚠️  Delete $KEY_FILE after adding to GitHub Secrets!${NC}"
else
    echo "Service account key already exists at $KEY_FILE"
fi

echo ""
echo -e "${GREEN}🎉 Google Cloud setup is complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Add the GitHub secrets mentioned above"
echo "2. Push code to GitHub: git push origin main"
echo "3. The CI/CD pipeline will automatically deploy to Cloud Run"
echo "4. Update Twilio webhook URL with the Cloud Run service URL"
