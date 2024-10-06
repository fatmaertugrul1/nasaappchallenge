import streamlit as st
import requests

# Place your API key here
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
        return response.json()['articles']  # Get data from the 'articles' key
    else:
        st.error("An error occurred while fetching the news.")
        return []
def is_political_article(article):
    # Define keywords to filter out political news
    political_keywords = ['politics', 'government', 'election', 'party', 'political', 'vote', 'candidate','war','flee']
    # Check if any of the keywords are in the article's title or description
    return any(keyword.lower() in article['title'].lower() or keyword.lower() in article['description'].lower() for keyword in political_keywords)

def display_article(article, large=False):
    # If large is True, display the article prominently
    if large:
        st.image(article.get('urlToImage', 'https://via.placeholder.com/300'), width=300)  # Larger image
        st.markdown(f'<p style="font-size:24px; color:#FF6347;"><b>{article["title"]}</b></p>', unsafe_allow_html=True)
        st.write(article['description'])
        st.write(f"[Read More]({article['url']})")
        st.write(f"*Published on: {article['publishedAt']}*")
    else:
        st.image(article.get('urlToImage', 'https://via.placeholder.com/150'), width=100)  # Smaller image
        st.markdown(f'<p style="font-size:18px; color:#FF6347;"><b>{article["title"]}</b></p>', unsafe_allow_html=True)
    
    st.markdown("---")

def main():
    st.title("Latest News About Landfill Fires")

    # Fetch main articles
    articles = fetch_news('landfill fire')

    # Suggested news categories
    suggestion_queries = [ 'waste', 'environment', 'landfill']
    suggested_articles = []
    
    for query in suggestion_queries:
        suggested_articles += fetch_news(query)
    
    # Combine main articles and suggested articles
    all_articles = articles + suggested_articles
     # Filter out political articles
    filtered_articles = [article for article in all_articles if not is_political_article(article)]


    if filtered_articles:
        # First, show the most relevant article prominently
        st.markdown("## Recommended Article")
        display_article(filtered_articles[0], large=True)  # Display the first article as the recommendation

        if len(filtered_articles) > 1:
            # Remove the first article from the list for the slider
            remaining_articles = filtered_articles[1:]

            # Now show the rest of the articles in a slider
            st.markdown("## Other Articles")
            num_remaining_articles = len(remaining_articles)

            if num_remaining_articles > 1:
                # Slider to select an article from the remaining ones
                article_index = st.slider('Select other articles', min_value=0, max_value=10, value=0, step=1)
                # Display the selected article in a smaller format
                display_article(remaining_articles[article_index], large=False)
            else:
                # Display the only remaining article
                display_article(remaining_articles[0], large=False)
    else:
        st.write("No news found.")

if __name__ == "__main__":
    main()
