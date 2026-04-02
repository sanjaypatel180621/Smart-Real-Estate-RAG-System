import streamlit as st
import time
import router

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Real Estate AI",
    page_icon="🏢",
    layout="wide"
)

# ---------- BACKGROUND STYLE ----------
st.markdown("""
<style>
[data-testid="stAppViewContainer"]{
    background-image: url("https://images.unsplash.com/photo-1560518883-ce09059eeffa");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}

[data-testid="stHeader"]{
    background: rgba(0,0,0,0);
}

.title {
    font-size: 42px;
    font-weight: 700;
    color: white;
    text-align: center;
}

.subtitle {
    font-size: 18px;
    color: #f1f1f1;
    text-align: center;
    margin-bottom: 25px;
}

.chat-container{
    background: rgba(255,255,255,0.15);
    backdrop-filter: blur(12px);
    padding: 25px;
    border-radius: 20px;
}

.card{
    background:white;
    border-radius:18px;
    padding:14px;
    margin-bottom:14px;
    display:flex;
    gap:15px;
    align-items:center;
    box-shadow:0 8px 20px rgba(0,0,0,0.18);
    transition:0.2s;
}

.card:hover{
    transform:scale(1.02);
}

.card img{
    width:90px;
    height:90px;
    border-radius:12px;
    object-fit:cover;
}

.card-text{
    font-size:14px;
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown('<div class="title">🏙️ Real Estate Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Ask anything about projects, prices, amenities or locations</div>', unsafe_allow_html=True)

# ---------- SESSION MEMORY ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- RESULT FORMATTER WITH IMAGES ----------
def format_response(result):

    if not result or not isinstance(result, dict):
        return "⚠️ No data found."

    answer = result.get("answer")

    formatted = ""

    # ---------- CASE 1: LIST RESULTS (GRAPH) ----------
    if isinstance(answer, list):

        if not answer:
            return "❌ No matching properties found."

        for row in answer:

            img = "https://images.unsplash.com/photo-1600585154340-be6161a56a0c"

            formatted += f"""
            <div class="card">
                <img src="{img}">
                <div class="card-text">
                    {"".join([f"<b>{k.replace('_',' ').title()}</b>: {v}<br>" for k,v in row.items()])}
                </div>
            </div>
            """

        return formatted


    # ---------- CASE 2: TEXT ANSWER (RAG) ----------
    if isinstance(answer, str):

        img = "https://images.unsplash.com/photo-1600585154340-be6161a56a0c"

        formatted += f"""
        <div class="card">
            <img src="{img}">
            <div class="card-text">
                {answer}
            </div>
        </div>
        """

        return formatted


    # ---------- CASE 3: UNKNOWN ----------
    return "⚠️ Unexpected response format."


    if not result or not isinstance(result, dict):
        return "⚠️ No data found."

    answer = result.get("answer")

    # ---------- CASE 1: LIST RESULT (GRAPH DB) ----------
    if isinstance(answer, list):

        if not answer:
            return "❌ No matching properties found."

        formatted = ""

        for row in answer:

            img = "https://images.unsplash.com/photo-1600585154340-be6161a56a0c"

            formatted += f"""
            <div class="card">
                <img src="{img}">
                <div class="card-text">
                    {"".join([f"<b>{k.replace('_',' ').title()}</b>: {v}<br>" for k,v in row.items()])}
                </div>
            </div>
            """

        return formatted


    # ---------- CASE 2: TEXT ANSWER (RAG) ----------
    if isinstance(answer, str):
        return f"""
        <div class="card">
            <div class="card-text">{answer}</div>
        </div>
        """


    # ---------- CASE 3: UNKNOWN ----------
    return "⚠️ Unexpected response format."





# ---------- CHAT WINDOW ----------
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


# ---------- INPUT ----------
prompt = st.chat_input("Ask about projects, prices, locations...")

if prompt:

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing real estate data..."):
            raw = router.route_query(prompt)
            response = format_response(raw)
            print(response)
            st.markdown(response, unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": response})


# ---------- FOOTER ----------
st.markdown("""
<br>
<center style='color:white; opacity:0.7'>
AI Powered • Knowledge Graph • Neo4j Backend
</center>
""", unsafe_allow_html=True)
