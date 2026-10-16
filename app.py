import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

st.title('🎯 Big Data Job Profile Analyzer')
st.write('**Student:** Sahil Goyal | **Roll No:** 11242424 | **Section:** I/I2')

st.markdown("""
This interactive dashboard displays the results of analyzing 1.6+ million job postings 
to identify skill demand patterns and job family clusters.
""")

# Sidebar navigation
page = st.sidebar.selectbox(
    'Select Analysis',
    ['Home', 'Skill Frequency', 'Job Clustering', 'Visualizations']
)

if page == 'Home':
    st.header('📋 Project Overview')
    st.markdown("""
    ### Big Data Job Profile Recruitment Analyzer
    
    A comprehensive Hadoop-based analytics pipeline that processes job posting data through:
    - **MapReduce** - Skill frequency extraction
    - **Pig** - Data cleaning and transformation
    - **Hive** - Analytics queries
    - **Python ML** - KMeans clustering (k=4 job families, k=9 skill groups)
    - **Visualizations** - matplotlib/seaborn charts
    
    **Technologies:** Hadoop, Python, pandas, scikit-learn, matplotlib
    
    **GitHub:** [View Repository](https://github.com/itzsahil-prog/Job-Profile-Recruitment-Analyzer)
    """)
    
    # Display project stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Job Postings", "1.6M+")
    with col2:
        st.metric("Skills Analyzed", "39")
    with col3:
        st.metric("Job Families", "4")

elif page == 'Skill Frequency':
    st.header('📊 Top Skills Analysis')
    
    if os.path.exists('outputs/skill_frequency.csv'):
        df = pd.read_csv('outputs/skill_frequency.csv')
        
        st.subheader(f'Total Skills Identified: {len(df)}')
        
        # Display top 20
        st.dataframe(df.head(20), use_container_width=True)
        
        # Plot top 10
        st.subheader('Top 10 Most Demanded Skills')
        fig, ax = plt.subplots(figsize=(12, 6))
        top10 = df.head(10)
        ax.barh(top10['skill_name'], top10['post_count'], color='steelblue')
        ax.set_xlabel('Number of Job Postings')
        ax.set_title('Top 10 Skills by Demand')
        ax.invert_yaxis()
        st.pyplot(fig)
        
        # Download option
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Full Skill Data",
            data=csv,
            file_name='skill_frequency.csv',
            mime='text/csv',
        )
    else:
        st.warning('Skill frequency data not found. Please run the MapReduce pipeline first.')
        st.code('python local_sim/run_mapreduce.py', language='bash')

elif page == 'Job Clustering':
    st.header('📈 Clustering Results')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader('Job Family Clusters (k=4)')
        if os.path.exists('outputs/job_family_assignments.csv'):
            clusters = pd.read_csv('outputs/job_family_assignments.csv')
            total_families = clusters['cluster_id'].nunique()
            st.write(f'Total job families: {total_families}')
            
            # Cluster distribution
            cluster_counts = clusters['cluster_id'].value_counts().sort_index()
            st.bar_chart(cluster_counts)
            
            st.dataframe(clusters.head(20), use_container_width=True)
        else:
            st.warning('Job family data not found.')
    
    with col2:
        st.subheader('Skill Group Clusters (k=9)')
        if os.path.exists('outputs/skill_group_assignments.csv'):
            skill_groups = pd.read_csv('outputs/skill_group_assignments.csv')
            total_groups = skill_groups['cluster_id'].nunique()
            st.write(f'Total skill groups: {total_groups}')
            
            # Skill group distribution
            group_counts = skill_groups['cluster_id'].value_counts().sort_index()
            st.bar_chart(group_counts)
            
            st.dataframe(skill_groups.head(20), use_container_width=True)
        else:
            st.warning('Skill group data not found.')
    
    # Competence Matrix
    st.subheader('Competence Matrix (4×9)')
    if os.path.exists('outputs/competence_matrix.csv'):
        comp_matrix = pd.read_csv('outputs/competence_matrix.csv')
        st.dataframe(comp_matrix, use_container_width=True)
    else:
        st.info('Competence matrix not yet generated.')

elif page == 'Visualizations':
    st.header('🎨 Visualizations')
    
    visualizations = [
        ('visualizations/skill_frequency_top20.png', 'Top 20 Skills by Frequency'),
        ('visualizations/job_family_distribution.png', 'Job Family Distribution'),
        ('visualizations/skill_group_distribution.png', 'Skill Group Distribution'),
        ('visualizations/competence_matrix_heatmap.png', 'Competence Matrix Heatmap'),
        ('visualizations/job_family_elbow.png', 'Job Family Elbow Plot'),
        ('visualizations/skill_group_elbow.png', 'Skill Group Elbow Plot'),
    ]
    
    for viz_path, viz_title in visualizations:
        if os.path.exists(viz_path):
            st.subheader(viz_title)
            st.image(viz_path, use_column_width=True)
        else:
            st.info(f'{viz_title}: Not yet generated. Run `python analytics/visualize.py`')

# Sidebar info
st.sidebar.markdown('---')
st.sidebar.markdown('### About')
st.sidebar.info("""
**Big Data Job Profile Analyzer**

Analyzes 1.6M+ job postings to identify:
- Top demanded skills
- Job family patterns (k=4)
- Skill groupings (k=9)
- Competence requirements

**Tech Stack:**
- Hadoop (MapReduce, Pig, Hive)
- Python (pandas, scikit-learn)
- Streamlit Dashboard
""")

st.sidebar.markdown('### Links')
st.sidebar.markdown('[GitHub Repository](https://github.com/itzsahil-prog/Job-Profile-Recruitment-Analyzer)')
st.sidebar.markdown('[View Documentation](https://github.com/itzsahil-prog/Job-Profile-Recruitment-Analyzer/blob/main/docs/DEPLOYMENT.md)')

# Footer
st.markdown('---')
st.markdown('**Developed by:** Sahil Goyal | **Roll No:** 11242424 | **Section:** I/I2')