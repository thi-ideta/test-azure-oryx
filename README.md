# Test Azure Oryx Build - POST_BUILD_COMMAND Debug

Minimal FastAPI project to test whether Oryx `POST_BUILD_COMMAND` runs correctly on Azure App Service Linux.

**The problem:** `docling` pulls `opencv-python` (full) which requires `libGL.so.1` — not available on Azure headless servers. We use a post-build script to replace it with `opencv-python-headless`.

## Project Structure

```
test-azure-oryx/
├── .github/workflows/deploy.yml   # GitHub Actions CI/CD
├── app.py                         # FastAPI with health check endpoints
├── requirements.txt               # fastapi, uvicorn, gunicorn, docling
├── scripts/postbuild.sh           # Replaces opencv-python with headless version
├── startup.sh                     # Gunicorn startup command
└── build.env                      # Oryx build config (POST_BUILD_COMMAND)
```

## Step-by-Step Deployment

### 1. Create Azure App Service

```bash
# Login
az login

# Create resource group (skip if you already have one)
az group create --name rg-test-oryx --location westeurope

# Create App Service plan (B1 minimum for testing)
az appservice plan create \
  --name plan-test-oryx \
  --resource-group rg-test-oryx \
  --sku B1 \
  --is-linux

# Create web app
az webapp create \
  --name <your-app-name> \
  --resource-group rg-test-oryx \
  --plan plan-test-oryx \
  --runtime "PYTHON:3.12"
```

### 2. Configure App Settings

```bash
az webapp config appsettings set \
  --name <your-app-name> \
  --resource-group rg-test-oryx \
  --settings \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true

az webapp config set \
  --name <your-app-name> \
  --resource-group rg-test-oryx \
  --startup-file "startup.sh"
```

### 3. Set Up GitHub Actions

1. Download the Publish Profile from Azure Portal:
   - Go to your App Service -> **Overview** -> **Download publish profile**

2. In your GitHub repo, go to **Settings** -> **Secrets and variables** -> **Actions**:
   - Add **secret**: `AZURE_WEBAPP_PUBLISH_PROFILE` = paste the publish profile XML content
   - Add **variable**: `AZURE_WEBAPP_NAME` = `<your-app-name>`

### 4. Create build.env (if not already done)

```bash
echo 'POST_BUILD_COMMAND=scripts/postbuild.sh' > build.env
```

### 5. Push and Deploy

```bash
git add -A
git commit -m "initial: test azure oryx post-build"
git push origin main
```

GitHub Actions will trigger automatically. Wait for the workflow to complete.

### 6. Check Deployment Logs

This is the most important part — verify that `postbuild.sh` actually ran:

1. Go to Azure Portal -> Your App Service -> **Deployment Center** -> **Logs** tab
2. Click the latest **Commit ID**
3. Click **"Show Logs"** next to **"Running oryx build..."**
4. Look for:
   - `>>> postbuild.sh started` (script executed)
   - `cv2 version: 4.11.0` (opencv-headless installed)
   - `✅ opencv-python-headless installed successfully`

**Alternative ways to check logs:**

```bash
# SSH into Kudu - check build log
# Go to: https://<your-app-name>.scm.azurewebsites.net
# Check: /tmp/build-debug.log

# Or via CLI
az webapp log config --name <your-app-name> --resource-group rg-test-oryx --docker-container-logging filesystem
az webapp log tail --name <your-app-name> --resource-group rg-test-oryx

# Or download all deployment logs
# https://<your-app-name>.scm.azurewebsites.net/api/zip/site/deployments
```

### 7. Test Endpoints

Once deployed, verify the app:

```bash
APP_URL="https://<your-app-name>.azurewebsites.net"

# Health check
curl $APP_URL/

# Check opencv-python-headless is installed (NOT opencv-python)
curl $APP_URL/check-opencv

# Check docling is available
curl $APP_URL/check-docling
```

**Expected results:**

| Endpoint | Expected Response |
|----------|-------------------|
| `/` | `{"status":"ok","env":"unknown"}` |
| `/check-opencv` | `{"opencv":"ok","version":"4.11.0","package":"opencv-python-headless (expected)"}` |
| `/check-docling` | `{"docling":"ok"}` |

If `/check-opencv` returns an error about `libGL.so.1`, the postbuild script did NOT run.

### 8. Cleanup

```bash
az group delete --name rg-test-oryx --yes --no-wait
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| No postbuild logs at all | `build.env` not in repo or `SCM_DO_BUILD_DURING_DEPLOYMENT` not set | Verify both are present |
| "Permission denied" on postbuild.sh | Missing execute permission | `git update-index --chmod=+x scripts/postbuild.sh` |
| opencv error on `/check-opencv` | postbuild.sh didn't run or ran in wrong venv | Check Oryx build logs for errors |
| App shows default Azure page | Startup command not set | Set startup command to `startup.sh` |
