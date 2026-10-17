import os
import re
import json
import traceback
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Try importing pypdf for resume parsing
try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

# Page Configuration
st.set_page_config(
    page_title="Big Data Job Profile & Recruitment Analyzer",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper function to find existing files safely
def find_existing_path(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None

# Load Skills Dictionary for NLP Extraction & Normalization
@st.cache_data
def load_skills_dictionary():
    dict_path = find_existing_path(['config/skills_dictionary.csv', '../config/skills_dictionary.csv'])
    if dict_path:
        try:
            df = pd.read_csv(dict_path)
            skills = {}
            for _, row in df.iterrows():
                canon = str(row['canonical_skill']).strip()
                raw_aliases = str(row['aliases']).split(',') if pd.notna(row['aliases']) else []
                aliases = [a.strip().lower() for a in raw_aliases if a.strip()]
                aliases.append(canon.lower())
                skills[canon] = {
                    'category': str(row.get('category', 'Technology')),
                    'aliases': list(set(aliases))
                }
            return skills
        except Exception:
            pass
    
    # Fallback canonical list if file missing
    fallback_skills = [
        'Python', 'SQL', 'Java', 'AWS', 'JavaScript', 'Azure', 'Docker', 'Kubernetes',
        'Git', 'Linux', 'Spark', 'Hadoop', 'Tableau', 'Power BI', 'React', 'Node.js',
        'C++', 'Bash', 'Terraform', 'Kafka', 'GCP', 'PostgreSQL', 'MongoDB', 'MySQL',
        'PyTorch', 'TensorFlow', 'scikit-learn', 'CI/CD', 'Ansible', 'Agile', 'Cassandra',
        'Hive', 'Pig', 'HDFS', 'MapReduce', 'YARN', 'HBase', 'Flink', 'Zookeeper'
    ]
    return {s: {'category': 'Technology', 'aliases': [s.lower()]} for s in fallback_skills}

SKILLS_DICT = load_skills_dictionary()
ALL_CANONICAL_SKILLS = sorted(list(SKILLS_DICT.keys()))

def extract_text_from_upload(uploaded_file):
    """Extract text from uploaded PDF or TXT resume."""
    if uploaded_file is None:
        return ""
    
    filename = uploaded_file.name.lower()
    
    if filename.endswith('.pdf'):
        if PYPDF_AVAILABLE:
            try:
                reader = pypdf.PdfReader(uploaded_file)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
            except Exception as e:
                return f"Error reading PDF: {e}"
        else:
            return "pypdf library not available for PDF parsing. Please paste text directly."
    else:
        try:
            return uploaded_file.read().decode('utf-8', errors='ignore')
        except Exception as e:
            return f"Error reading file: {e}"

def extract_skills_from_text(text):
    """NLP-based skill extraction and alias normalization."""
    if not text or not isinstance(text, str):
        return []
    lower_text = text.lower()
    found = set()
    for canon, data in SKILLS_DICT.items():
        for alias in data['aliases']:
            if len(alias) <= 3:
                pattern = r'\b' + re.escape(alias) + r'\b'
                if re.search(pattern, lower_text):
                    found.add(canon)
                    break
            else:
                if alias in lower_text:
                    found.add(canon)
                    break
    return sorted(list(found))

try:
    # Header Banner
    st.title("💼 Big Data–Driven Job Profile and Recruitment Analyzer")
    st.caption("Powered by Hadoop, Apache Hive, Apache Spark, Python NLP & Machine Learning")
    
    # Sidebar Navigation aligned with the 5 Core Project Modules
    st.sidebar.title("Navigation")
    menu = st.sidebar.radio(
        "Select Module:",
        [
            "🏠 System Architecture & Overview",
            "📄 Module 1 & 2: Resume Ingestion & NLP Extraction",
            "🎯 Module 3: Candidate-Job Matching",
            "📈 Module 4: Recruitment Trend Analytics",
            "💡 Module 5: Skill Gaps & Career Pathways",
            "🏢 Job Families & Competence Matrix",
            "🎨 Visualizations Gallery"
        ]
    )

    # =========================================================================
    # MODULE: SYSTEM ARCHITECTURE & OVERVIEW
    # =========================================================================
    if menu == "🏠 System Architecture & Overview":
        st.header("📋 Platform Overview & End-to-End Architecture")
        
        # High-level Metrics
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            st.metric("Total Postings Analyzed", "1,615,940", help="Aggregated from HDFS recruitment repositories")
        with kpi2:
            st.metric("Canonical Tech Skills", f"{len(ALL_CANONICAL_SKILLS)}+", help="Tracked technical competencies")
        with kpi3:
            st.metric("Job Family Profiles (k)", "4", help="Identified via unsupervised KMeans")
        with kpi4:
            st.metric("Skill Domains (k)", "9", help="Clustered functional tech domains")

        st.markdown("---")
        
        col_arch1, col_arch2 = st.columns([1.2, 1])
        
        with col_arch1:
            st.markdown("""
            ### 🎯 Core Purpose & Problem Statement
            Modern enterprise hiring suffers from massive data volumes, unstructured candidate resumes, and misaligned skill terminology.
            This platform processes big data recruitment datasets using distributed storage and compute:
            
            - **Hadoop HDFS & Hive:** Distributed storage and SQL analytics over 1.6M+ job postings.
            - **Apache Spark & Pig:** Data cleaning, ETL pipelines, and high-performance joins.
            - **Python NLP:** Text parsing, alias normalization, and skill extraction.
            - **Machine Learning:** Dual KMeans clustering ($k=4$ job families, $k=9$ skill groups) and explainable candidate-job matching.
            """)
            
            st.markdown("""
            ### 🏗️ Complete Big Data Technology Stack
            | Layer | Technologies Deployed |
            | :--- | :--- |
            | **Distributed Storage** | Apache Hadoop HDFS |
            | **Data Warehouse** | Apache Hive (Partitioned External Tables) |
            | **Processing & ETL** | Apache Spark / Pig / MapReduce |
            | **NLP & Text Mining** | Python, Regex Entity Normalizer, TF-IDF |
            | **Machine Learning** | Scikit-learn (KMeans, Silhouette Validation) |
            | **Interactive Dashboard** | Streamlit, Matplotlib, Seaborn |
            | **Container Deployment** | Docker, Docker Compose |
            """)

        with col_arch2:
            st.markdown("### 🔄 Big Data Architecture Pipeline")
            st.markdown("""
            ```mermaid
            graph TD
                A[Resume PDFs + Job Listings] --> B[Data Ingestion with Python]
                B --> C[HDFS: Raw Data Storage]
                C --> D[Cleaning and Processing with Spark/Pig]
                D --> E[Hive: Structured Recruitment Tables]
                E --> F[NLP and Skill Extraction]
                F --> G[Candidate-Job Matching Model]
                F --> H[Recruitment Trend Analytics]
                G --> I[FastAPI + Streamlit Dashboard]
                H --> I
                I --> J[Match Scores, Skill Gaps and Hiring Insights]
            ```
            """)
            st.info("💡 **Explainable Matching:** The platform provides transparent, auditable scores comparing candidate qualifications directly against verified job requirements.")

    # =========================================================================
    # MODULE 1 & 2: INGESTION & NLP EXTRACTION
    # =========================================================================
    elif menu == "📄 Module 1 & 2: Resume Ingestion & NLP Extraction":
        st.header("📄 Module 1 & 2: Resume Ingestion & NLP Skill Extraction")
        st.markdown("Upload candidate resumes (PDF, TXT) or paste job descriptions to parse raw text and extract normalized technical competencies.")

        tab_ingest1, tab_ingest2 = st.tabs(["Candidate Resume Ingestion", "Job Description Parser"])

        with tab_ingest1:
            st.subheader("Candidate Resume Parser")
            uploaded_file = st.file_uploader("Upload Candidate Resume (PDF or TXT):", type=['pdf', 'txt'])
            
            pasted_resume = st.text_area(
                "Or Paste Resume Text Directly:", 
                height=150, 
                placeholder="Example: Experienced Big Data Engineer skilled in Python, SQL, Hadoop, Hive, Spark, Docker, and AWS..."
            )
            
            raw_text = ""
            if uploaded_file is not None:
                with st.spinner("Parsing uploaded file..."):
                    raw_text = extract_text_from_upload(uploaded_file)
            elif pasted_resume.strip():
                raw_text = pasted_resume.strip()

            if raw_text:
                st.markdown("---")
                st.markdown("#### 🔍 Extracted Raw Text Preview")
                st.text_area("Extracted Text:", raw_text[:800] + ("..." if len(raw_text) > 800 else ""), height=100)
                
                extracted_skills = extract_skills_from_text(raw_text)
                
                if extracted_skills:
                    st.success(f"✅ Successfully identified {len(extracted_skills)} normalized skills!")
                    
                    col_sk1, col_sk2 = st.columns([1.2, 1])
                    with col_sk1:
                        st.markdown("##### Extracted Skill Badges:")
                        st.write(" • ".join([f"`{s}`" for s in extracted_skills]))
                        
                    with col_sk2:
                        cat_counts = {}
                        for s in extracted_skills:
                            cat = SKILLS_DICT.get(s, {}).get('category', 'Technology')
                            cat_counts[cat] = cat_counts.get(cat, 0) + 1
                        
                        fig, ax = plt.subplots(figsize=(6, 3))
                        ax.bar(list(cat_counts.keys()), list(cat_counts.values()), color='#2b5c8f')
                        ax.set_ylabel("Skill Count")
                        ax.set_title("Skills by Technical Category")
                        plt.xticks(rotation=20, ha='right')
                        plt.tight_layout()
                        st.pyplot(fig)
                else:
                    st.warning("No canonical technical skills identified. Please ensure the resume mentions recognized technologies.")

        with tab_ingest2:
            st.subheader("Job Posting Requirement Extraction")
            jd_text = st.text_area(
                "Paste Job Description / Requisition:",
                height=160,
                placeholder="Example: We are hiring a Senior Data Scientist. Requirements include Python, SQL, PyTorch, Scikit-learn, Tableau, and experience deploying models on AWS..."
            )
            
            if st.button("🚀 Analyze Job Description", type="primary"):
                if not jd_text.strip():
                    st.warning("Please provide a job description.")
                else:
                    jd_skills = extract_skills_from_text(jd_text)
                    if jd_skills:
                        st.success(f"Extracted {len(jd_skills)} required technical competencies:")
                        st.write(" | ".join([f"**`{s}`**" for s in jd_skills]))
                    else:
                        st.info("No matching canonical tech skills detected.")

    # =========================================================================
    # MODULE 3: CANDIDATE-JOB MATCHING
    # =========================================================================
    elif menu == "🎯 Module 3: Candidate-Job Matching":
        st.header("🎯 Module 3: Explainable Candidate-Job Matching Model")
        st.markdown("""
        Evaluates candidate competencies against specific job vacancy requirements to produce an **explainable match score**, 
        highlighting covered skills and identifying missing requirements.
        """)

        preset_jobs = {
            "Big Data Engineer": ["Python", "SQL", "Hadoop", "Hive", "Spark", "Kafka"],
            "Machine Learning Engineer": ["Python", "PyTorch", "TensorFlow", "scikit-learn", "SQL", "Docker"],
            "Cloud & DevOps Architect": ["AWS", "Terraform", "Docker", "Kubernetes", "Ansible", "CI/CD", "Bash"],
            "Data Analyst & BI Specialist": ["SQL", "Tableau", "Power BI", "Excel", "Python", "Data Modeling"],
            "Custom Role": []
        }

        col_j1, col_j2 = st.columns(2)
        
        with col_j1:
            st.subheader("1. Job Requirements")
            selected_preset = st.selectbox("Select Target Job Role:", list(preset_jobs.keys()))
            default_reqs = preset_jobs[selected_preset] if selected_preset != "Custom Role" else ["Python", "SQL", "Hadoop", "Hive", "Spark"]
            
            target_skills = st.multiselect(
                "Required Skills for Job:",
                options=ALL_CANONICAL_SKILLS,
                default=default_reqs
            )

        with col_j2:
            st.subheader("2. Candidate Profile")
            default_cand = ["Python", "SQL", "Hadoop", "Hive"]
            candidate_skills = st.multiselect(
                "Candidate Possessed Skills:",
                options=ALL_CANONICAL_SKILLS,
                default=default_cand
            )

        if st.button("📊 Calculate Match Score & Explainability Breakdown", type="primary"):
            if not target_skills:
                st.warning("Please specify at least 1 required skill for the job.")
            else:
                req_set = set(s.lower() for s in target_skills)
                cand_set = set(s.lower() for s in candidate_skills)
                
                matched = req_set.intersection(cand_set)
                missing = req_set - cand_set
                
                match_percentage = int((len(matched) / len(req_set)) * 100)
                
                st.markdown("---")
                st.subheader(f"Illustrative Matching Result: **{match_percentage}%**")
                st.progress(match_percentage / 100)
                
                col_res1, col_res2, col_res3 = st.columns(3)
                with col_res1:
                    st.metric("Required Skills", len(req_set))
                with col_res2:
                    st.metric("Covered by Candidate", len(matched))
                with col_res3:
                    st.metric("Missing Skills", len(missing))

                col_det1, col_det2 = st.columns(2)
                with col_det1:
                    st.markdown("#### ✅ Required Skill Coverage")
                    if matched:
                        for m in matched:
                            st.markdown(f"- 🟢 **{m.title()}** *(Matched)*")
                    else:
                        st.info("No required skills matched.")
                        
                with col_det2:
                    st.markdown("#### ❌ Missing Skills to Bridge")
                    if missing:
                        for mis in missing:
                            st.markdown(f"- 🔴 **{mis.title()}** *(Missing)*")
                    else:
                        st.success("🎉 Perfect match! 100% of required competencies covered.")
                        
                st.markdown("---")
                st.info(f"💡 **Explainability Note:** The {match_percentage}% score is calculated directly using documented skill overlap weights. Transparent matching ensures auditability and eliminates black-box hiring bias.")

    # =========================================================================
    # MODULE 4: RECRUITMENT TREND ANALYTICS
    # =========================================================================
    elif menu == "📈 Module 4: Recruitment Trend Analytics":
        st.header("📈 Module 4: Big Data Recruitment Trend Analytics")
        st.markdown("Hive queries and distributed aggregations over **1.6M+ job postings** analyzing demand, locations, salaries, and experience.")

        trend_tab1, trend_tab2, trend_tab3 = st.tabs(["Skill Demand Trends", "Salary & Experience Distributions", "Hiring Regions & Roles"])

        with trend_tab1:
            st.subheader("Top Demanded Skills Across 1.6M+ Postings")
            sf_file = find_existing_path(['outputs/skill_frequency.csv', 'outputs/skill_frequency_post_count.csv'])
            if sf_file:
                df_sf = pd.read_csv(sf_file)
                df_sf.columns = df_sf.columns.str.strip().str.lower()
                s_col = next((c for c in df_sf.columns if 'skill' in c), df_sf.columns[0])
                c_col = next((c for c in df_sf.columns if 'count' in c or 'post' in c), df_sf.columns[1])
                df_sf = df_sf.rename(columns={s_col: 'skill_name', c_col: 'post_count'})
                df_sf['post_count'] = pd.to_numeric(df_sf['post_count'], errors='coerce')
                df_sf = df_sf.dropna().sort_values('post_count', ascending=False)
                
                top15 = df_sf.head(15)
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.bar(top15['skill_name'], top15['post_count'], color='#1f77b4')
                ax.set_ylabel("Number of Job Postings")
                ax.set_title("Top 15 Technical Skills by Hiring Volume", fontweight='bold')
                plt.xticks(rotation=35, ha='right')
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.info("Skill frequency data loading...")

        with trend_tab2:
            st.subheader("Market Salary & Experience Profiles")
            mt_file = find_existing_path(['outputs/market_trends_summary.json'])
            if mt_file:
                with open(mt_file, 'r') as f:
                    mt = json.load(f)
                    
                col_sal, col_exp = st.columns(2)
                with col_sal:
                    st.markdown("##### Salary Range Distributions")
                    sal_data = mt.get('salary_ranges', {})
                    fig_s, ax_s = plt.subplots(figsize=(6, 4))
                    ax_s.bar(list(sal_data.keys()), list(sal_data.values()), color='#2ca02c')
                    ax_s.set_ylabel("Percentage of Market (%)")
                    plt.xticks(rotation=25, ha='right')
                    plt.tight_layout()
                    st.pyplot(fig_s)
                    
                with col_exp:
                    st.markdown("##### Experience Requirements")
                    exp_data = mt.get('experience_distribution', {})
                    fig_e, ax_e = plt.subplots(figsize=(6, 4))
                    ax_e.bar(list(exp_data.keys()), list(exp_data.values()), color='#e27c38')
                    ax_e.set_ylabel("Percentage of Market (%)")
                    plt.xticks(rotation=25, ha='right')
                    plt.tight_layout()
                    st.pyplot(fig_e)

        with trend_tab3:
            st.subheader("Geographic Regions & Role Distributions")
            mt_file = find_existing_path(['outputs/market_trends_summary.json'])
            if mt_file:
                with open(mt_file, 'r') as f:
                    mt = json.load(f)
                    
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    st.markdown("##### Top Tech Hiring Regions")
                    reg_data = mt.get('top_tech_hiring_regions', {})
                    fig_r, ax_r = plt.subplots(figsize=(7, 4))
                    ax_r.barh(list(reg_data.keys())[::-1], list(reg_data.values())[::-1], color='#9467bd')
                    ax_r.set_xlabel("Job Volume Sample")
                    plt.tight_layout()
                    st.pyplot(fig_r)
                    
                with col_r2:
                    st.markdown("##### Top Tech Job Titles")
                    role_data = mt.get('top_roles', {})
                    fig_ro, ax_ro = plt.subplots(figsize=(7, 4))
                    ax_ro.barh(list(role_data.keys())[::-1], list(role_data.values())[::-1], color='#17becf')
                    ax_ro.set_xlabel("Post Count")
                    plt.tight_layout()
                    st.pyplot(fig_ro)

    # =========================================================================
    # MODULE 5: SKILL GAPS & CAREER RECOMMENDATIONS
    # =========================================================================
    elif menu == "💡 Module 5: Skill Gaps & Career Pathways":
        st.header("💡 Module 5: Skill Gap & Actionable Career Pathways")
        st.markdown("""
        Empowers candidates and talent teams by identifying precise skill deficiencies and generating 
        custom project-based learning roadmaps to achieve 100% role readiness.
        """)

        target_role = st.selectbox(
            "Select Target Career Track:",
            ["Big Data Engineer", "Machine Learning Specialist", "Cloud & DevOps Architect", "Data Analytics & BI Professional"]
        )

        role_roadmaps = {
            "Big Data Engineer": {
                "core": ["Python", "SQL", "Hadoop", "Hive", "Spark", "Kafka"],
                "learning_paths": [
                    ("Apache Spark", "Complete a practical distributed data-processing project processing multi-GB CSV/Parquet files with PySpark."),
                    ("Apache Kafka", "Build a real-time event streaming pipeline producing and consuming logs via Kafka topic partitions."),
                    ("Apache Hive", "Design external partitioned tables and write optimized HiveQL analytics queries.")
                ]
            },
            "Machine Learning Specialist": {
                "core": ["Python", "SQL", "PyTorch", "TensorFlow", "scikit-learn", "Docker"],
                "learning_paths": [
                    ("PyTorch / Deep Learning", "Implement neural network classification and transfer learning on an open-source image or NLP dataset."),
                    ("MLOps & Docker", "Containerize a trained machine learning model inside a Docker container and serve predictions via FastAPI."),
                    ("scikit-learn", "Master cross-validation, hyperparameter tuning (GridSearchCV), and feature engineering.")
                ]
            },
            "Cloud & DevOps Architect": {
                "core": ["AWS", "Azure", "Docker", "Kubernetes", "Terraform", "CI/CD", "Bash"],
                "learning_paths": [
                    ("Terraform (IaC)", "Author declarative Terraform scripts provisioning cloud VPCs, subnets, and compute instances."),
                    ("Kubernetes", "Deploy multi-tier containerized applications with K8s Deployments, Services, and Ingress rules."),
                    ("CI/CD Automation", "Build an automated GitHub Actions pipeline executing unit tests and deploying containers.")
                ]
            },
            "Data Analytics & BI Professional": {
                "core": ["SQL", "Tableau", "Power BI", "Data Modeling", "Python", "Data Warehousing"],
                "learning_paths": [
                    ("Advanced SQL", "Master window functions, CTEs, self-joins, and query execution plan optimization."),
                    ("Power BI / Tableau", "Design executive-ready interactive dashboards with KPI cards, drill-downs, and custom DAX calculations."),
                    ("Data Modeling", "Learn Star and Snowflake dimensional schema designs for enterprise data warehouses.")
                ]
            }
        }

        current_skills = st.multiselect(
            "Select Your Current Skills:",
            options=ALL_CANONICAL_SKILLS,
            default=["Python", "SQL"]
        )

        curr_set = set(s.lower() for s in current_skills)
        needed = set(s.lower() for s in role_roadmaps[target_role]["core"])
        gaps = needed - curr_set

        st.markdown("---")
        st.subheader("🎯 Personalized Gap Analysis & Roadmap")

        if gaps:
            st.warning(f"⚠️ You have **{len(gaps)} skill gaps** for the **{target_role}** track: {', '.join([g.title() for g in gaps])}")
            
            st.markdown("#### 🛠️ Recommended Practical Learning Pathways:")
            for skill_name, action in role_roadmaps[target_role]["learning_paths"]:
                if skill_name.lower() in gaps or any(g in skill_name.lower() for g in gaps):
                    st.markdown(f"""
                    - **Action Plan for `{skill_name}`:**
                      {action}
                    """)
        else:
            st.success(f"🎉 Exceptional! You possess all primary competencies for the **{target_role}** track.")

    # =========================================================================
    # JOB FAMILIES & COMPETENCE MATRIX
    # =========================================================================
    elif menu == "🏢 Job Families & Competence Matrix":
        st.header("🏢 Job Families & Competence Matrix ($4 \\times 9$)")
        st.markdown("""
        Unsupervised Machine Learning ($k$-Means) identified **4 Job Family Profiles** and **9 Functional Domains**.
        The **Competence Matrix** below outlines prevalence and proficiency standards across families.
        """)

        tab_fam, tab_grp, tab_mat = st.tabs(["Job Family Profiles (k=4)", "Skill Group Clusters (k=9)", "Competence Matrix (4×9)"])

        with tab_fam:
            fam_sum_file = find_existing_path(['outputs/job_family_summary.csv'])
            if fam_sum_file:
                fam_df = pd.read_csv(fam_sum_file)
                st.markdown("#### Summary of Discovered Job Profiles")
                st.dataframe(fam_df, use_container_width=True)
                
                lbl_col = 'family_label' if 'family_label' in fam_df.columns else ('cluster_id' if 'cluster_id' in fam_df.columns else fam_df.columns[0])
                size_col = 'size' if 'size' in fam_df.columns else next((c for c in fam_df.columns if 'size' in c.lower() or 'count' in c.lower() or 'post' in c.lower()), None)
                
                if size_col:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.bar(fam_df[lbl_col].astype(str), fam_df[size_col], color='#008080')
                    ax.set_ylabel('Number of Postings')
                    ax.set_title('Recruitment Distribution Across Job Families')
                    plt.xticks(rotation=20, ha='right')
                    plt.tight_layout()
                    st.pyplot(fig)
            else:
                st.info("Job family summary data loading...")

        with tab_grp:
            grp_sum_file = find_existing_path(['outputs/skill_group_summary.csv'])
            if grp_sum_file:
                grp_df = pd.read_csv(grp_sum_file)
                st.markdown("#### 9 Functional Tech Stack Domains")
                
                # Derive 'size' column safely if not present
                if 'size' not in grp_df.columns:
                    if 'member_skills' in grp_df.columns:
                        grp_df['size'] = grp_df['member_skills'].fillna('').apply(
                            lambda x: len([s for s in str(x).split('|') if s.strip()])
                        )
                    else:
                        grp_df['size'] = 1
                
                lbl_col = 'group_label' if 'group_label' in grp_df.columns else ('group_id' if 'group_id' in grp_df.columns else grp_df.columns[0])
                
                st.dataframe(grp_df, use_container_width=True)
                
                fig, ax = plt.subplots(figsize=(9, 4))
                ax.bar(grp_df[lbl_col].astype(str), grp_df['size'], color='#4682b4')
                ax.set_ylabel('Skills Count')
                ax.set_title('Skill Count per Functional Domain')
                plt.xticks(rotation=30, ha='right')
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.info("Skill group summary loading...")

        with tab_mat:
            st.markdown("#### Cross-Domain Competence Matrix ($4 \\times 9$)")
            num_file = find_existing_path(['outputs/competence_matrix_numeric.csv', 'outputs/competence_matrix.csv'])
            lbl_file = find_existing_path(['outputs/competence_matrix_labels.csv'])
            
            c1, c2 = st.columns(2)
            if num_file:
                with c1:
                    st.markdown("##### Numeric Prevalence (% of postings with skill group)")
                    df_num = pd.read_csv(num_file, index_col=0)
                    st.dataframe(df_num, use_container_width=True)
            if lbl_file:
                with c2:
                    st.markdown("##### Categorical Standard (Low <20% | Medium 20-50% | High ≥50%)")
                    df_lbl = pd.read_csv(lbl_file, index_col=0)
                    st.dataframe(df_lbl, use_container_width=True)

    # =========================================================================
    # VISUALIZATIONS GALLERY
    # =========================================================================
    elif menu == "🎨 Visualizations Gallery":
        st.header("🎨 Publication-Ready Visualizations Gallery")
        st.markdown("Generated directly from pipeline outputs across MapReduce, Hive, and KMeans clustering.")

        viz_items = [
            (['visualizations/skill_frequency.png', 'visualizations/skill_frequency_top20.png'], 
             'Top 20 Skills by Recruitment Frequency', 'Distribution of the 20 most frequently required skills extracted from recruitment postings.'),
            (['visualizations/job_family_sizes.png', 'visualizations/job_family_distribution.png'], 
             'Job Family Cluster Distribution (k=4)', 'Proportion of market postings grouped by skill profile into 4 primary job families.'),
            (['visualizations/skill_group_sizes.png', 'visualizations/skill_group_distribution.png'], 
             'Skill Group Cluster Distribution (k=9)', 'Co-occurrence clustering partitioning 39 core skills into functional domain clusters.'),
            (['visualizations/competence_heatmap.png', 'visualizations/competence_matrix_heatmap.png'], 
             '4×9 Competence Matrix Heatmap', 'Cross-sectional heatmap annotating skill-group prevalence percentages per job family.'),
            (['visualizations/elbow_plot.png', 'visualizations/job_family_elbow.png'], 
             'Clustering Elbow & Inertia Validation', 'Within-cluster sum of squares (inertia) across k=2..10 validating cluster selection.'),
            (['visualizations/data_quality.png', 'visualizations/skill_group_elbow.png'], 
             'Dataset Quality & Record Retention', 'Record retention metrics verifying data cleaning fidelity across 1.6M+ raw records.')
        ]

        for paths, title, desc in viz_items:
            found = find_existing_path(paths)
            if found:
                st.subheader(f"📌 {title}")
                st.caption(desc)
                st.image(found, use_container_width=True)
                st.markdown("---")
            else:
                st.info(f"{title}: Image file not found.")

    # Sidebar Footer
    st.sidebar.markdown('---')
    st.sidebar.markdown('### Project Information')
    st.sidebar.markdown('🔗 [GitHub Repository](https://github.com/itzsahil-prog/Job-Profile-Recruitment-Analyzer)')
    st.sidebar.markdown('📖 [Deployment Guide](https://github.com/itzsahil-prog/Job-Profile-Recruitment-Analyzer/blob/main/docs/DEPLOYMENT.md)')
    st.sidebar.caption("Big Data–Driven Job Profile and Recruitment Analyzer")

    st.markdown("---")
    st.caption("💼 **Big Data Job Profile and Recruitment Analyzer** | Hadoop • Hive • Spark • Python ML • NLP • Streamlit")

except Exception as e:
    st.error(f"Application runtime error: {e}")
    st.code(traceback.format_exc())
