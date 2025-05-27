import streamlit as st
import time
import requests
import os

# ---------- Config ----------
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ---------- API Call Function ----------
def get_api_recommendations(query: str, top_n: int = 5):
    try:
        response = requests.post(
            f"{BACKEND_URL}/recommend",
            json={"query": query, "top_n": top_n}
        )
        if response.status_code == 200:
            return response.json()["recommendations"]
        else:
            return [{"title": "Error", "description": f"Failed with status code {response.status_code}"}]
    except Exception as e:
        return [{"title": "Error", "description": f"Connection failed: {e}"}]

# ---------- Page Config ----------
st.set_page_config(page_title="📚 AI Book Recommender", layout="wide")

# ---------- Sidebar ----------
with st.sidebar:
    st.title("🤖 AI Book Recommender")
    username = st.session_state.get("username", "Guest")
    st.markdown(f"Welcome, **{username}**! Enjoy your personalized book suggestions.")
    
    chat_mode = st.radio("Choose Chat Mode:", ["General Chat", "First-Time Reader Assistant"])

    if chat_mode == "General Chat":
        st.subheader("Filters")
        selected_genres = st.multiselect(
            "Select Genre(s):",
            ["Sci-Fi", "Romance", "Fantasy", "Non-Fiction", "Mystery", "Historical", "Self-Help"],
            default=["Sci-Fi"]
        )
        min_rating = st.slider("Minimum Book Rating:", 1.0, 5.0, 3.5, 0.1)
    
    st.markdown("---")
    st.caption("Powered by NLP and HuggingFace")

# ---------- Session State Setup ----------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "recent_queries" not in st.session_state:
    st.session_state.recent_queries = []

# ---------- General Chat Mode ----------
def run_general_chat():
    st.markdown("<h1 style='text-align: center;'>📚 Ask Me Anything About Books!</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Your AI reading companion, powered by NLP</p>", unsafe_allow_html=True)
    st.markdown("")

    for entry in st.session_state.chat_history:
        with st.chat_message(entry["role"]):
            st.markdown(entry["content"])

    user_query = st.chat_input("Type your question here...")

    if user_query:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        st.session_state.recent_queries.append(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                time.sleep(1.5)
                recommendations = get_api_recommendations(user_query)
                rec_text = "Here are your book recommendations:\n\n"
                for book in recommendations:
                    rec_text += f"- *{book['title']}*\n  {book['description']}\n\n"

                st.markdown(rec_text)
                st.session_state.chat_history.append({"role": "assistant", "content": rec_text})

    with st.expander("🕵️‍♂️ View Recent Queries"):
        if st.session_state.recent_queries:
            for q in st.session_state.recent_queries[-5:][::-1]:
                st.markdown(f"- {q}")
        else:
            st.write("No queries yet!")

# ---------- First-Time Reader Assistant Mode ----------
def run_first_time_reader_chat():
    st.header("📘 Let's Find Your First Book!")

    if "ft_stage" not in st.session_state:
        st.session_state.ft_stage = 0
        st.session_state.ft_answers = {}

    stages = [
        "What kind of mood are you in? 😊",
        "What topics are you interested in?",
        "Do you want a light or deep read?",
        "Which age group do you prefer reading for?"
    ]

    options = [
        ["Happy & light", "Something emotional", "Mysterious", "Surprise me"],
        ["Science", "Romance", "History", "Technology", "Philosophy"],
        ["Easy and quick", "Inspiring", "Deep and thoughtful"],
        ["Young Adult", "Adult", "Timeless Classics"]
    ]

    if st.session_state.ft_stage < len(stages):
        st.markdown(f"**{stages[st.session_state.ft_stage]}**")
        choice = st.radio("Choose one:", options[st.session_state.ft_stage], key=f"choice_{st.session_state.ft_stage}")
        if st.button("Next"):
            st.session_state.ft_answers[stages[st.session_state.ft_stage]] = choice
            st.session_state.ft_stage += 1
            st.rerun()
    else:
        st.success("Thanks! Generating recommendations based on your preferences...")

        # Build query from collected answers
        summary = ". ".join([f"{k} {v}" for k, v in st.session_state.ft_answers.items()])
        recommendations = get_api_recommendations(summary)

        st.markdown("### 📚 Based on your preferences:")
        for book in recommendations:
            st.markdown(f"**{book['title']}**\n\n{book['description']}\n")

        if st.button("🔁 Restart"):
            del st.session_state.ft_stage
            del st.session_state.ft_answers
            st.experimental_rerun()

# ---------- Main App ----------
if chat_mode == "General Chat":
    run_general_chat()
else:
    run_first_time_reader_chat()
