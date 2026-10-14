
import streamlit as st
from router import router
from faq import ingest_faq_data, faq_chain, faqs_path
from sql import sql_chain

# Page configuration
st.set_page_config(
    page_title="E-commerce Chatbot",
    page_icon="🛍️",
    layout="centered"
)

# Ingest FAQ data
ingest_faq_data(faqs_path)



def ask(query):
    route = router(query)

    print(f"User query: {query}")
    print(f"Selected route: {route}")

    if route == "faq":
        return faq_chain(query)

    elif route == "sql":
        return sql_chain(query)

    return f"Sorry, I couldn't identify the route: {route}"



# App title
st.title("🛍️ E-commerce Chatbot")
st.caption("Ask questions about returns, refunds, orders, and products.")

# Initialize conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
query = st.chat_input("Ask your question...")

if query:
    # Display and save user message
    st.session_state.messages.append({
        "role": "user",
        "content": query
    })

    with st.chat_message("user"):
        st.markdown(query)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Finding your answer..."):
            try:
                response = ask(query)
            except Exception:
                st.error(
                    "Sorry, something went wrong while processing "
                    "your question. Please check the terminal for details."
                )
                raise

        st.markdown(response)

    # Save assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })
