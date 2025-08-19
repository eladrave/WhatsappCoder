#!/bin/bash
# Fix Secret Manager permissions for Cloud Run service account

set -e

echo "🔧 Fixing Secret Manager permissions for Cloud Run service account..."

# Variables
PROJECT_ID="autocoder-443421"
SERVICE_ACCOUNT="724942100863-compute@developer.gserviceaccount.com"

# Grant Secret Manager Secret Accessor role to the service account
echo "Granting Secret Manager Secret Accessor role to ${SERVICE_ACCOUNT}..."

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

echo "✅ Permissions granted successfully!"
echo ""
echo "The Cloud Run service account now has access to read secrets from Secret Manager."
echo "You can re-run the GitHub Actions workflow to deploy the service."
