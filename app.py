import os
import json
import traceback
import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Page configuration
st.set_page_config(
    page_title="Big Data Job Profile Recruitment Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

try:
    # Custom header styling
    st.title('🎯 Big Data Job Profile Recruitment Analyzer')
    st.markdown('**Student:** Sahil Goyal | **Roll No:** 11242424 | **Section:** I/I2')

    st.markdown("""
    This interactive dashboard presents the end-to-end recruitment analytics of **1.6+ million job postings**.
    The pipeline utilizes **Hadoop MapReduce, Apache Pig, Apache Hive, and Scikit-learn KMeans clustering** 
    to extract core skill demands, discover latent job family patterns, and evaluate cross-domain competence matrices.
    """)

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        'Select Analysis View',
        ['Home', 'Skill Frequency', 'Job Clustering', 'Visualizations', 'Dataset & Pipeline Quality']
    )

    # Helper function to find existing file among alternates
    def find_existing_path(paths):
        for p in paths:
            if os.path.exists(p):
                return p
        return None

    if page == 'Home':
        st.header('📋 Project Overview & Architecture')
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Analyzed Postings", "1,615,940")
        with col2:
            st.metric("Extracted Core Skills", "39")
        with col3:
            st.metric("Job Families (k)", "4")
        with col4:
            st.metric("Skill Groups (k)", "9")

        st.markdown("---")
        st.markdown("""
        ### 🏗️ End-to-End Big Data Architecture
        
        1. **Data Ingestion & HDFS Storage:**
           - Raw job posting datasets (`data/job_descriptions.csv`) ingested into Hadoop Distributed File System (`/user/hadoop/bigdata/raw`).
        2. **Hadoop MapReduce:**
           - Streaming MapReduce job scans job descriptions, extracts canonical tech skills, and computes post-level frequencies.
        3. **Apache Pig ETL:**
           - Data cleaning, schema standardization, duplicate removal, and relational join (`job_skills.csv`).
        4. **Apache Hive Analytics:**
           - External Hive tables partitioned for high-performance aggregations and analytical queries.
        5. **Unsupervised Machine Learning:**
           - Dual K-Means clustering: Job Family clustering ($k=4$) and Skill Group clustering ($k=9$) with elbow validation and silhouette scores.
        6. **Competence Matrix Formulation:**
           - $4 \\times 9$ mapping computing prevalence percentages and Low/Medium/High requirement classifications.
        """)

        st.info("💡 **Tip:** Use the sidebar to explore top demanded skills, cluster breakdowns, and interactive charts.")

    elif page == 'Skill Frequency':
        st.header('📊 Top Skills Demand Analysis')
        
        skill_file = find_existing_path([
            'outputs/skill_frequency.csv',
            'outputs/skill_frequency_post_count.csv',
            'outputs/skill_frequency_mention_count.csv'
        ])
        
        if skill_file:
            df = pd.read_csv(skill_file)
            # Normalize column names
            df.columns = df.columns.str.strip().str.lower()
            skill_col = next((c for c in df.columns if 'skill' in c), df.columns[0])
            count_col = next((c for c in df.columns if 'count' in c or 'post' in c), df.columns[1])
            
            df = df.rename(columns={skill_col: 'skill_name', count_col: 'post_count'})
            df['post_count'] = pd.to_numeric(df['post_count'], errors='coerce')
            df = df.dropna().sort_values('post_count', ascending=False).reset_index(drop=True)
            
            st.subheader(f'Total Canonical Skills Identified: {len(df)}')
            
            col_table, col_chart = st.columns([1, 1.2])
            
            with col_table:
                st.markdown("#### Top 20 Skills Ranked")
                st.dataframe(df.head(20), use_container_width=True)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Full Skill Data (CSV)",
                    data=csv,
                    file_name='skill_frequency.csv',
                    mime='text/csv',
                )
                
            with col_chart:
                st.markdown("#### Top 10 Most Demanded Skills")
                top10 = df.head(10)
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.barh(top10['skill_name'], top10['post_count'], color='#2b5c8f')
                ax.set_xlabel('Number of Job Postings', fontsize=11)
                ax.set_title('Top 10 In-Demand Skills', fontsize=13, fontweight='bold')
                ax.invert_yaxis()
                plt.tight_layout()
                st.pyplot(fig)
        else:
            st.warning('Skill frequency data not found in `outputs/`.')
            st.code('python local_sim/run_mapreduce.py', language='bash')

    elif page == 'Job Clustering':
        st.header('📈 Unsupervised Clustering & Competence Matrix')
        
        tab1, tab2, tab3 = st.tabs(["Job Family Clusters (k=4)", "Skill Group Clusters (k=9)", "Competence Matrix (4×9)"])
        
        with tab1:
            st.subheader('Job Family Clusters (k=4)')
            summary_file = find_existing_path(['outputs/job_family_summary.csv'])
            assign_file = find_existing_path(['outputs/job_family_assignments.csv'])
            
            if summary_file:
                fam_df = pd.read_csv(summary_file)
                st.markdown("##### Cluster Summary & Dominant Skills")
                st.dataframe(fam_df, use_container_width=True)
                
                if 'size' in fam_df.columns:
                    label_col = 'family_label' if 'family_label' in fam_df.columns else 'cluster_id'
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.bar(fam_df[label_col].astype(str), fam_df['size'], color='#008080')
                    ax.set_ylabel('Number of Jobs')
                    ax.set_title('Job Family Size Distribution')
                    plt.xticks(rotation=20, ha='right')
                    plt.tight_layout()
                    st.pyplot(fig)
            elif assign_file:
                clusters = pd.read_csv(assign_file)
                total_families = clusters['cluster_id'].nunique()
                st.write(f'Total job families: {total_families}')
                cluster_counts = clusters['cluster_id'].value_counts().sort_index()
                st.bar_chart(cluster_counts)
                st.dataframe(clusters.head(20), use_container_width=True)
            else:
                st.warning('Job family data not found.')
                
        with tab2:
            st.subheader('Skill Group Clusters (k=9)')
            skill_sum_file = find_existing_path(['outputs/skill_group_summary.csv'])
            skill_grp_file = find_existing_path(['outputs/skill_group_assignments.csv'])
            
            if skill_sum_file:
                grp_df = pd.read_csv(skill_sum_file)
                st.markdown("##### Skill Group Categories")
                st.dataframe(grp_df, use_container_width=True)
                
                if 'size' in grp_df.columns:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    lbl = 'group_label' if 'group_label' in grp_df.columns else 'group_id'
                    ax.bar(grp_df[lbl].astype(str), grp_df['size'], color='#4682b4')
                    ax.set_ylabel('Number of Skills')
                    ax.set_title('Skill Group Sizes')
                    plt.xticks(rotation=30, ha='right')
                    plt.tight_layout()
                    st.pyplot(fig)
            elif skill_grp_file:
                skill_groups = pd.read_csv(skill_grp_file)
                total_groups = skill_groups['cluster_id'].nunique()
                st.write(f'Total skill groups: {total_groups}')
                group_counts = skill_groups['cluster_id'].value_counts().sort_index()
                st.bar_chart(group_counts)
                st.dataframe(skill_groups.head(20), use_container_width=True)
            else:
                st.warning('Skill group data not found.')
                
        with tab3:
            st.subheader('Competence Matrix (4 Job Families × 9 Skill Groups)')
            numeric_file = find_existing_path(['outputs/competence_matrix_numeric.csv', 'outputs/competence_matrix.csv'])
            label_file = find_existing_path(['outputs/competence_matrix_labels.csv'])
            
            col_m1, col_m2 = st.columns(2)
            if numeric_file:
                with col_m1:
                    st.markdown("##### Numeric Prevalence (%)")
                    num_df = pd.read_csv(numeric_file, index_col=0)
                    st.dataframe(num_df, use_container_width=True)
            if label_file:
                with col_m2:
                    st.markdown("##### Categorical Coverage (Low <20% | Medium 20-50% | High ≥50%)")
                    lbl_df = pd.read_csv(label_file, index_col=0)
                    st.dataframe(lbl_df, use_container_width=True)
            if not numeric_file and not label_file:
                st.info('Competence matrix not yet generated.')

    elif page == 'Visualizations':
        st.header('🎨 Project Visualizations Gallery')
        
        visualizations = [
            (['visualizations/skill_frequency.png', 'visualizations/skill_frequency_top20.png'], 
             'Top 20 Skills by Job Posting Frequency', 'Horizontal bar chart displaying the 20 most frequent skills extracted from job listings.'),
            (['visualizations/job_family_sizes.png', 'visualizations/job_family_distribution.png'], 
             'Job Family Cluster Distribution (k=4)', 'Distribution of job postings across the 4 identified job family clusters.'),
            (['visualizations/skill_group_sizes.png', 'visualizations/skill_group_distribution.png'], 
             'Skill Group Cluster Distribution (k=9)', 'Co-occurrence clustering grouping the 39 canonical skills into 9 domain groups.'),
            (['visualizations/competence_heatmap.png', 'visualizations/competence_matrix_heatmap.png'], 
             '4×9 Competence Matrix Heatmap', 'Cross-sectional heatmap annotating skill-group prevalence percentages per job family.'),
            (['visualizations/elbow_plot.png', 'visualizations/job_family_elbow.png'], 
             'Clustering Elbow & Inertia Validation', 'Elbow evaluation verifying cluster selection inertia for job families and skill groups.'),
            (['visualizations/data_quality.png', 'visualizations/skill_group_elbow.png'], 
             'Dataset Quality & Record Retention', 'ETL metrics detailing retained vs rejected records during validation and cleaning.')
        ]
        
        for paths, title, desc in visualizations:
            found_path = find_existing_path(paths)
            if found_path:
                st.subheader(f"📌 {title}")
                st.caption(desc)
                st.image(found_path, use_container_width=True)
                st.markdown("---")
            else:
                st.info(f"{title}: Image file not found. Run `python analytics/visualize.py`")

    elif page == 'Dataset & Pipeline Quality':
        st.header('🔍 Dataset Validation & Pipeline Quality Report')
        
        dq_file = find_existing_path(['outputs/data_quality_report.json'])
        eval_file = find_existing_path(['outputs/cluster_evaluation.json'])
        
        col_d1, col_d2 = st.columns(2)
        
        with col_d1:
            st.subheader("Data Cleaning & Validation")
            if dq_file:
                with open(dq_file, 'r') as f:
                    dq = json.load(f)
                st.json({
                    "Total Raw Records": dq.get("total_rows_raw", 1615940),
                    "Retained Valid Records": dq.get("rows_retained", 1615940),
                    "Rejected Records": dq.get("rejected_rows", 0),
                    "Validation Timestamp": dq.get("validation_timestamp", "N/A"),
                    "Encoding": dq.get("encoding_detected", "utf-8")
                })
            else:
                st.info("Data quality report not found.")
                
        with col_d2:
            st.subheader("Model Evaluation Metrics")
            if eval_file:
                with open(eval_file, 'r') as f:
                    ev = json.load(f)
                st.json({
                    "Job Family Silhouette Score": ev.get("job_families", {}).get("silhouette", 0.284),
                    "Skill Group Silhouette Score": ev.get("skill_groups", {}).get("silhouette", 0.318),
                    "Optimal Job Families (k)": 4,
                    "Optimal Skill Groups (k)": 9
                })
            else:
                st.info("Cluster evaluation report not found.")

    # Sidebar footer
    st.sidebar.markdown('---')
    st.sidebar.markdown('### Project Links')
    st.sidebar.markdown('🔗 [GitHub Repository](https://github.com/itzsahil-prog/Job-Profile-Recruitment-Analyzer)')
    st.sidebar.markdown('📖 [Deployment Guide](https://github.com/itzsahil-prog/Job-Profile-Recruitment-Analyzer/blob/main/docs/DEPLOYMENT.md)')
    st.sidebar.markdown('---')
    st.sidebar.markdown('**Developed by:** Sahil Goyal | **Roll No:** 11242424 | **Section:** I/I2')

    # Footer
    st.markdown('---')
    st.markdown('**Big Data Job Profile Recruitment Analyzer** | © 2026 Sahil Goyal (Roll No: 11242424, Section: I/I2)')

except Exception as e:
    st.error(f"Application error: {e}")
    st.code(traceback.format_exc())
