import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title('🎯 Big Data Job Profile Analyzer')
st.write('**Student:** Sahil Goyal | **Roll No:** 11242424')

# Load data
st.header('📊 Top Skills Analysis')
if st.button('Load Skill Frequency Data'):
    df = pd.read_csv('outputs/skill_frequency.csv')
    st.dataframe(df.head(20))
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    df.head(10).plot(kind='bar', x='skill_name', y='post_count', ax=ax)
    st.pyplot(fig)

st.header('📈 Clustering Results')
if st.button('Show Job Family Clusters'):
    clusters = pd.read_csv('outputs/job_family_assignments.csv')
    st.write(f'Total job families: {clusters[\"cluster_id\"].nunique()}')
    st.dataframe(clusters.head())

st.header('🎨 Visualizations')
st.image('visualizations/skill_frequency_top20.png')
st.image('visualizations/competence_matrix_heatmap.png')
