# Deployment Guide: LungSight AI on Google Cloud Run

This guide details the steps to deploy **LungSight AI** (an Agentic Medical Imaging Application) to Google Cloud Run. This architecture allows the application to run serverless, scale automatically, and be accessible via a public URL.

## Prerequisites

1.  **Google Cloud Project**: You need a project with billing enabled (Free Trial is sufficient).
2.  **Google Cloud SDK**: Installed and authenticated on your local machine.
3.  **Google AI Studio API Key**: A valid API key for Gemini models.
4.  **Project Structure**: Ensure your root folder (`Agent_Development`) contains the `lungSightAI` package folder.

---

## Step 1: Prepare Configuration Files

Create the following files in your **Root Directory** (outside the `lungSightAI` folder).

### 1. `Dockerfile`
This file tells Google Cloud how to build your application environment.

```dockerfile
# Use lightweight Python 3.11
FROM python:3.11-slim

# Allow logs to show up immediately in Cloud Console
ENV PYTHONUNBUFFERED=True

# Set standard port for Cloud Run
ENV PORT=8080

# Install system dependencies required for OpenCV and ADK
# libgl1/libglib2 are MANDATORY for cv2 to work in Docker
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory to /app
WORKDIR /app

# 1. Copy requirements first (for better caching)
COPY requirements.txt .

# 2. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy your actual application code
COPY . .

# 4. Run the ADK Web Server
# We point 'adk web' to the current directory where lungSightAI package exists
CMD ["adk", "web", "--host", "0.0.0.0", "--port", "8080"]

```

### 2. `.glcoudignore`
This prevents uploading massive local files (like virtual environments) that cause timeouts.

```.gloudignore
.git
.gitignore
Dockerfile
README.md

# Ignore the huge virtual environments
agent_env/
venv/
env/

# Ignore Python cache
__pycache__/
**/*.pyc
**/*.pyo
**/*.pyd

# Ignore IDE settings
.vscode/
.idea/

# Ignore Local Database/Session files
*.db
*.sqlite
lungSightAI/ADS_DB/
lungSightAI/manual_session.db

# Keep the Model Weights and Data!
!lungSightAI/Data/Model Weight/VGG.weights.h5
!lungSightAI/Data/
```
### 3. requirement.txt 
Clean version optimized for Cloud Run (CPU-only TensorFlow) 
[requirements.txt](https://github.com/eshaan-james-dl/LungSight-AI/blob/main/requirements.txt) 

### 4. Deployment Commands
#### 4.1 Initialize & Select Project
Replace YOUR_PROJECT_ID with your actual Google Cloud Project ID (e.g., gen-lang-client-xxxx).

``` 
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

#### 4.2 Deploy to Cloud Run
This single command builds the container, uploads it, and deploys it. Replace PASTE_API_KEY_HERE with your actual key.

```
gcloud run deploy lungsight-ai `
  --source . `
  --region us-central1 `
  --allow-unauthenticated `
  --memory 4Gi `
  --cpu 2 `
  --set-env-vars GOOGLE_API_KEY="PASTE_API_KEY_HERE",GOOGLE_GENAI_USE_VERTEXAI="0"
```
#### 4.3 Verification
1. Wait for the command to finish (approx. 8 minutes).
2. Look for the Service URL in the terminal output:
   
   ``` Service URL: https://lungsight-ai-xyz123-uc.a.run.app```

3. Click the link to open your live agent.

#### 4.4 Troubleshooting
* **503 Service Unavailable:** The model is overloaded. Retry in 1 minute or switch code to use gemini-1.5-flash-001.

* **Upload Timeout:** Ensure .gcloudignore exists and excludes your virtual envirnment

* **Billing Error:** Ensure a billing account is linked to your specific Project ID in the Google Cloud Console.
