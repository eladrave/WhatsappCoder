# WhatsApp-AutoCoder Deployment Guide

## 🚀 Quick Deployment to Google Cloud Run

This guide will help you deploy the WhatsApp-AutoCoder service to Google Cloud Run using GitHub Actions CI/CD.

## Prerequisites

- Google Cloud Account with billing enabled
- GitHub repository (already set up at https://github.com/eladrave/WhatsappCoder)
- Twilio account with WhatsApp sandbox configured
- `gcloud` CLI installed locally

## Step 1: Set up Google Cloud Resources

Run the setup script to configure Google Cloud:

```bash
# Make sure you're in the project directory
cd WhatsappCoder

# Run the setup script
./scripts/setup-gcp.sh
```

The script will:
1. Create/configure your Google Cloud project
2. Enable required APIs (Cloud Run, Artifact Registry, etc.)
3. Create a service account for GitHub Actions
4. Set up Secret Manager for sensitive data
5. Generate a service account key

## Step 2: Configure GitHub Secrets

After running the setup script, add these secrets to your GitHub repository:

### Required GitHub Secrets

1. Go to your repository: https://github.com/eladrave/WhatsappCoder
2. Navigate to Settings → Secrets and variables → Actions
3. Add the following secrets:

| Secret Name | Description | How to Get |
|------------|-------------|------------|
| `GCP_PROJECT_ID` | Your Google Cloud Project ID | Shown by setup script |
| `GCP_SA_KEY` | Service Account JSON key | Content of `gcp-key.json` file |
| `CODECOV_TOKEN` | (Optional) Codecov token for coverage reports | From codecov.io |

### Adding the Service Account Key

```bash
# Copy the key to clipboard (macOS)
cat gcp-key.json | pbcopy

# Copy the key to clipboard (Linux)
cat gcp-key.json | xclip -selection clipboard

# IMPORTANT: Delete the key file after adding to GitHub
rm gcp-key.json
```

## Step 3: Configure Google Cloud Secrets

Add your Twilio credentials to Google Cloud Secret Manager:

```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Create secrets (you'll be prompted for values)
echo -n "YOUR_TWILIO_ACCOUNT_SID" | gcloud secrets create TWILIO_ACCOUNT_SID --data-file=-
echo -n "YOUR_TWILIO_AUTH_TOKEN" | gcloud secrets create TWILIO_AUTH_TOKEN --data-file=-
echo -n "+1234567890,+0987654321" | gcloud secrets create ALLOWED_PHONE_NUMBERS --data-file=-

# Grant access to the service account
SA_EMAIL="github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com"

for secret in TWILIO_ACCOUNT_SID TWILIO_AUTH_TOKEN ALLOWED_PHONE_NUMBERS; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/secretmanager.secretAccessor"
done
```

## Step 4: Deploy via GitHub Actions

The deployment will happen automatically when you push to the main branch:

```bash
# Push any changes to trigger deployment
git push origin main
```

### Monitor the Deployment

1. Go to Actions tab in your GitHub repository
2. Watch the "Deploy WhatsApp-AutoCoder to Google Cloud Run" workflow
3. The workflow will:
   - Run tests
   - Build Docker image
   - Push to Google Artifact Registry
   - Deploy to Cloud Run
   - Run smoke tests

## Step 5: Get Your Cloud Run Service URL

After successful deployment:

1. Check the GitHub Actions output for the service URL
2. Or get it from Google Cloud Console:
   ```bash
   gcloud run services describe whatsapp-coder --region=us-central1 --format='value(status.url)'
   ```

Your service URL will look like: `https://whatsapp-coder-xxxxx-uc.a.run.app`

## Step 6: Configure Twilio Webhook

Update your Twilio WhatsApp sandbox configuration:

1. Go to [Twilio Console](https://console.twilio.com)
2. Navigate to Messaging → Settings → WhatsApp sandbox settings
3. Update the webhook URLs:
   - **When a message comes in**: `https://YOUR-SERVICE-URL/webhook/whatsapp`
   - **Status callback URL**: `https://YOUR-SERVICE-URL/webhook/status`
4. Save the configuration

## Step 7: Test Your Deployment

### Verify Service Health

```bash
# Test health endpoint
curl https://YOUR-SERVICE-URL/health

# Run smoke tests
./scripts/smoke-test.sh https://YOUR-SERVICE-URL
```

### Test WhatsApp Integration

1. Send a WhatsApp message to your Twilio sandbox number
2. Try these commands:
   - `/help` - Show available commands
   - `/new TestProject` - Create a new project
   - `/list` - List your projects

## Monitoring and Logs

### View Logs in Google Cloud

```bash
# Stream logs
gcloud alpha run services logs tail whatsapp-coder --region=us-central1

# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=whatsapp-coder" --limit=50
```

### View Logs in GitHub Actions

Check the Actions tab in your GitHub repository for deployment logs and history.

## Updating the Service

To update your service:

1. Make changes to your code
2. Commit and push to main branch:
   ```bash
   git add .
   git commit -m "feat: your changes"
   git push origin main
   ```
3. GitHub Actions will automatically deploy the update

## Cost Optimization

Cloud Run charges only for the resources you use:

### Free Tier (per month)
- 2 million requests
- 360,000 GB-seconds of memory
- 180,000 vCPU-seconds

### Cost Optimization Tips

1. **Set maximum instances**:
   ```bash
   gcloud run deploy whatsapp-coder --max-instances=5
   ```

2. **Set minimum instances to 0** (already configured):
   - Service scales to zero when not in use

3. **Monitor usage**:
   ```bash
   gcloud monitoring metrics-descriptors list --filter="metric.type:run.googleapis.com"
   ```

## Troubleshooting

### Common Issues

#### 1. Health check fails
- Check the PORT environment variable handling in Dockerfile
- Verify the /health endpoint is accessible

#### 2. Twilio signature verification fails
- Ensure TWILIO_AUTH_TOKEN secret is correct
- Verify webhook URL matches exactly (including https://)

#### 3. Phone number not authorized
- Check ALLOWED_PHONE_NUMBERS secret format
- Phone numbers should include country code: +1234567890

#### 4. Service returns 500 errors
- Check logs for specific errors
- Verify all secrets are properly configured
- Ensure Redis connection (if using external Redis)

### Debug Commands

```bash
# Check service status
gcloud run services describe whatsapp-coder --region=us-central1

# Check recent errors
gcloud logging read "severity>=ERROR AND resource.type=cloud_run_revision" --limit=20

# Test with curl
curl -X POST https://YOUR-SERVICE-URL/webhook/whatsapp \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=whatsapp:+1234567890&Body=test"
```

## Security Best Practices

1. **Never commit secrets** to the repository
2. **Use Secret Manager** for all sensitive data
3. **Regularly rotate** service account keys
4. **Monitor access logs** for unauthorized attempts
5. **Keep dependencies updated** for security patches

## Support

For issues or questions:
- GitHub Issues: https://github.com/eladrave/WhatsappCoder/issues
- Documentation: See `/docs` directory
- Logs: Check Google Cloud Logging and GitHub Actions

## Next Steps

After successful deployment:

1. ✅ Test all WhatsApp commands
2. ✅ Set up monitoring alerts in Google Cloud
3. ✅ Configure custom domain (optional)
4. ✅ Enable AutoCoder MCP integration
5. ✅ Set up backup and disaster recovery plan

---

**Congratulations!** Your WhatsApp-AutoCoder service is now deployed and running on Google Cloud Run! 🎉
