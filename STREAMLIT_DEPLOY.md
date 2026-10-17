# 🚀 Streamlit & Docker Deployment Guide

**Platform:** Job Profile Recruitment Analyzer — Big Data Talent Intelligence  
**Repository:** https://github.com/itzsahil-prog/Job-Profile-Recruitment-Analyzer

---

## 📱 Option 1: Deploy to Streamlit Cloud (FREE Cloud Hosting)

Streamlit Community Cloud provides 1-click free hosting directly from your GitHub repository.

### Step 1: Verification Checklist
The repository is completely configured with all deployable assets:
- ✅ `app.py` - Modern, responsive multi-page Streamlit application
- ✅ `requirements.txt` - All dependencies specified
- ✅ `outputs/*.csv` & `outputs/*.json` - Pre-computed analytics summaries and competence matrix
- ✅ `visualizations/*.png` - All 6 high-resolution analytical charts
- ✅ GitHub repository synced on `main` branch

### Step 2: 1-Click Launch
1. Visit: **https://streamlit.io/cloud**
2. Sign in with your GitHub account: `itzsahil-prog`
3. Click **"New app"**
4. Fill in the deployment details:
   - **Repository:** `itzsahil-prog/Job-Profile-Recruitment-Analyzer`
   - **Branch:** `main`
   - **Main file path:** `app.py`
5. Click **"Deploy!"**

Alternatively, use this direct deploy URL:
**https://share.streamlit.io/deploy?repository=itzsahil-prog/Job-Profile-Recruitment-Analyzer&branch=main&mainModule=app.py**

---

## 🐳 Option 2: Deploy with Docker / Docker Compose (Containerized)

The repository includes a production-grade `Dockerfile` and `docker-compose.yml` for local or cloud container deployment (AWS ECS, GCP Cloud Run, Azure Container Instances, or DigitalOcean).

### Running with Docker Compose:
```bash
docker-compose up --build
```
Access the application at: `http://localhost:8501`

### Running with Docker CLI:
```bash
# 1. Build the container image
docker build -t job-profile-analyzer .

# 2. Run the container
docker run -d -p 8501:8501 --name analyzer-app job-profile-analyzer

# 3. View logs
docker logs -f analyzer-app
```

---

## 💻 Option 3: Running Locally

```bash
# 1. Activate your virtual environment
.venv\Scripts\activate   # Windows PowerShell
# or: source .venv/bin/activate  # Linux/macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch Streamlit
streamlit run app.py
```
Your default browser will automatically open to `http://localhost:8501`.

---

## 🎨 Dashboard Features

1. **Home & Architecture:**
   - 1.6M+ job postings analyzed, 39 core skills extracted, 4 job families, 9 skill groups.
   - Comprehensive overview of the Hadoop ecosystem pipeline.
2. **Skill Frequency:**
   - Ranked Top 20 skills table with interactive horizontal bar charts and CSV export.
3. **Job Clustering & Competence Matrix:**
   - Job Family clustering ($k=4$) with dominant skills and size distribution.
   - Skill Group clustering ($k=9$) categorizing tech domains.
   - $4 \times 9$ Competence Matrix displaying numeric prevalence (%) and Low/Medium/High coverage.
4. **Visualizations Gallery:**
   - High-resolution display of all 6 charts (Skill Frequency, Cluster Sizes, Heatmap, Elbow Plot, Data Quality).
5. **Dataset & Pipeline Quality:**
   - Data validation audit, record retention stats, and silhouette scores (0.284 for jobs, 0.318 for skills).
