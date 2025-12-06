# Ghost Agent Deployment Checklist

## Step 1: Generate GitHub Personal Access Token (PAT)
1. Go to https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. **Note**: "Ghost Agent"
4. **Expiration**: "No expiration"
5. **Scopes**: Check **`repo`** (Full control of private repositories)
6. Click **"Generate token"**
7. **COPY THE TOKEN** (you won't see it again!)

## Step 2: Create the Ghost Agent Repository
1. Go to https://github.com/new
2. **Repository name**: `ghost-agent` (or any name you prefer)
3. **Visibility**: **Private** ⚠️ IMPORTANT
4. **Do NOT** initialize with README
5. Click **"Create repository"**

## Step 3: Add the Secret Token
1. In your new `ghost-agent` repo, click **Settings**
2. Left sidebar: **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. **Name**: `GH_PAT` (must be exactly this)
5. **Secret**: Paste your token from Step 1
6. Click **"Add secret"**

## Step 4: Upload Files to Ghost Agent Repo
Upload these files from `contri-chart-script` folder:
- ✅ `agent.py`
- ✅ `config.json`
- ✅ `history.json`
- ✅ `.github/workflows/schedule.yml`

**Method 1 (Easy - Web Upload):**
1. Go to your `ghost-agent` repo
2. Click **"Add file"** → **"Upload files"**
3. Drag all 4 files
4. Commit changes

**Method 2 (Git Command Line):**
```bash
cd c:/Users/ck-sayan/Documents/contri-chart-script
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/ck-sayan/ghost-agent.git
git push -u origin main
```

## Step 5: Activate the Agent
1. Go to your `ghost-agent` repo
2. Click **"Actions"** tab
3. Click **"I understand my workflows, go ahead and enable them"**
4. You should see "Ghost Agent Daily Run" workflow

## Step 6: Test Run (Optional)
1. In the Actions tab, click **"Ghost Agent Daily Run"**
2. Click **"Run workflow"** → **"Run workflow"**
3. Wait 30 seconds, refresh the page
4. Click on the running job to see logs
5. Check one of your 4 repos for a new commit!

## 🛑 How to STOP the Agent
If you want to stop the script permanently:

**Option 1: Disable (Recommended)**
1. Go to your `ghost-agent` repo on GitHub.
2. Click the **"Actions"** tab.
3. Click **"Ghost Agent Daily Run"** on the left sidebar.
4. Click the **"..."** (three dots) menu near the top right.
5. Click **"Disable workflow"**.
*The agent will stop running immediately, but your code remains safe.*

**Option 2: Delete (Permanent)**
1. Go to your `ghost-agent` repo **Settings**.
2. Scroll to the bottom "Danger Zone".
3. Click **"Delete this repository"**.
*This removes the agent completely.*
