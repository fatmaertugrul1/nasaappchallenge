import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px

# API Key for News API
API_KEY = 'c077ad22149948fea02cbb1166efab32'  # Put your own API key here

def fetch_news(query):
    url = 'https://newsapi.org/v2/everything'
    params = {
        'q': query,
        'language': 'en',  # English news
        'apiKey': API_KEY
    }
    
    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json().get('articles', [])  # Ensure articles is returned as a list
    else:
        st.error("An error occurred while fetching the news.")
        return []

def is_relevant_article(article):
    return 'landfill' in article.get('title', '').lower()

def format_date(iso_date_str):
    try:
        date_obj = datetime.strptime(iso_date_str, "%Y-%m-%dT%H:%M:%SZ")
        return date_obj.strftime("%d %B %Y")
    except ValueError:
        return "Unknown Date"

def display_article(article):
    image_url = article.get('urlToImage') or 'https://via.placeholder.com/150'  # Default image if urlToImage is None
    published_at = format_date(article.get("publishedAt", "Unknown"))

    # Article card
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <img src="{image_url}" style="width: 120px; height: 80px; object-fit: cover; border-radius: 5px; margin-right: 15px;" alt="Article Image">
        <div style="flex: 1;">
            <h3 style="margin: 0; font-size: 20px; color: #FF6347;">{article.get("title", "No Title")}</h3>
            <p style="margin: 5px 0; font-size: 14px; color: #333;">{article.get("description", "No Description")}</p>
            <div style="display: flex; justify-content: space-between; font-size: 12px; color: #555;">
                <a href="{article.get('url', '#')}" target="_blank" style="color: #007BFF; text-decoration: none;">Read More</a>
                <span>Published on: {published_at}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_news_section():
    st.header("Latest News About Landfills")
    articles = fetch_news('landfill fire')

    suggestion_queries = ['waste', 'environment', 'landfill']
    suggested_articles = []
    
    for query in suggestion_queries:
        suggested_articles += fetch_news(query)
    
    all_articles = articles + suggested_articles
    filtered_articles = [article for article in all_articles if is_relevant_article(article)]
    
    if filtered_articles:
        num_articles_per_page = 3
        total_articles = len(filtered_articles)
        
        if 'page' not in st.session_state:
            st.session_state.page = 0
        
        st.markdown("""
        <style>
        .pagination-buttons {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }
        .pagination-buttons button {
            width: 100px;
            height: 35px;
            margin: 0 10px;
            font-size: 14px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="pagination-buttons">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])
        previous_clicked = col1.button("Previous", use_container_width=True)
        next_clicked = col2.button("Next", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if previous_clicked and st.session_state.page > 0:
            st.session_state.page -= 1
        
        if next_clicked and (st.session_state.page + 1) * num_articles_per_page < total_articles:
            st.session_state.page += 1
        
        start_idx = st.session_state.page * num_articles_per_page
        end_idx = min(start_idx + num_articles_per_page, len(filtered_articles))

        for article in filtered_articles[start_idx:end_idx]:
            display_article(article)
    else:
        st.write("No relevant news found.")

# Load the dataset for emissions
def load_emissions_data():
    df = pd.read_csv('solid-waste-disposal_emissions_sources.csv')
    df_filtered = df[['lat', 'lon', 'start_time', 'source_name', 'emissions_quantity', 'source_id', 'gas']]
    df_filtered = df_filtered[df_filtered['gas'] == 'co2e_100yr']
    df_filtered['year'] = pd.to_datetime(df_filtered['start_time']).dt.year
    df_filtered['rank'] = df_filtered['emissions_quantity'].rank(method="min", ascending=False).astype(int)
    return df_filtered

def display_emissions_map_and_chart(df_filtered):
    st.title("Top Emissions Locations on the Map")

    year = st.radio('Select Year', [2021, 2022])
    data_to_display = df_filtered[df_filtered['year'] == year]

    emissions_per_location = df_filtered.groupby(['lat', 'lon']).agg({
        'emissions_quantity': 'sum',
        'source_name': 'first',  # Get the first source_name for the popup
        'rank': 'first'          # Get the first rank for the popup
    }).reset_index()

    top_10_locations = emissions_per_location.nlargest(20, 'emissions_quantity')

    map_center = [data_to_display['lat'].mean(), data_to_display['lon'].mean()]
    m = folium.Map(location=map_center, zoom_start=6)

    # Create markers for each location
    for _, row in data_to_display.iterrows():
        folium.CircleMarker(
            location=(row['lat'], row['lon']),
            radius=5 + (row['emissions_quantity'] / 200000),  # Adjust radius based on emissions quantity (scaled down)
            color='blue',
            fill=True,
            fill_opacity=0.6,
            popup=(
                f"<b>{row['source_name']}</b><br>"
                f"<div>{int(row['emissions_quantity']):,} tons CO<sub>2</sub>e in {row['year']}</div>"
                f"<div>Rank: {row['rank']}</div>"
            )
        ).add_to(m)

    # Create markers for the top 10 locations
    for _, row in top_10_locations.iterrows():
        folium.Marker(
            location=(row['lat'], row['lon']),
            popup=(f"<b>{row['source_name']}</b><br>"
                   f"<div>{int(row['emissions_quantity']):,} tons CO<sub>2</sub>e</div>"
                   f"<div>Rank: {row['rank']}</div>"),
            icon=folium.Icon(color='green')  # Top 10 locations with a green marker
        ).add_to(m)

    st_folium(m, width=725, height=500)

    # Create and show the bar chart for emissions quantity
    st.subheader("Emissions Quantity Bar Chart")
    
    # Prepare data for the bar chart
    top_10_data = emissions_per_location.nlargest(20, 'emissions_quantity')
    top_10_data['source_name'] = top_10_data['source_name'].astype(str)
    
    # Create a horizontal bar chart using Plotly
    fig = px.bar(top_10_data, y='source_name', x='emissions_quantity',
                 labels={'source_name': 'Location', 'emissions_quantity': 'Emissions Quantity (Ton)'},
                 title="Top Emissions Quantity Locations",
                 orientation='h')  # 'h' for horizontal bars

    # Display the chart in Streamlit
    st.plotly_chart(fig)

# Main Streamlit application
if __name__ == "__main__":
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.radio("Choose an option", ["News Section", "Emissions Map"])

    if app_mode == "News Section":
        display_news_section()
    elif app_mode == "Emissions Map":
        df_filtered = load_emissions_data()
        display_emissions_map_and_chart(df_filtered)
