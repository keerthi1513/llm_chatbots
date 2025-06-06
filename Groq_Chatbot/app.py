import streamlit as st
import os
import time
import uuid
from datetime import datetime
from groq import Groq
from typing import List, Dict

# Configure page
st.set_page_config(page_title="LLaMA 3 Chatbot", layout="centered")

# Initialize session state for chat management
def init_chat_management():
    if "all_chats" not in st.session_state:
        st.session_state.all_chats = {}
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []

def create_new_chat():
    """Create a new chat session"""
    chat_id = str(uuid.uuid4())
    st.session_state.all_chats[chat_id] = {
        "title": "New Chat",
        "messages": [],
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat()
    }
    st.session_state.current_chat_id = chat_id
    st.session_state.messages = []
    return chat_id

def save_current_chat():
    """Auto-save current chat"""
    if st.session_state.current_chat_id and st.session_state.current_chat_id in st.session_state.all_chats:
        st.session_state.all_chats[st.session_state.current_chat_id]["messages"] = st.session_state.messages.copy()
        st.session_state.all_chats[st.session_state.current_chat_id]["last_updated"] = datetime.now().isoformat()
        
        # Auto-generate title from first user message
        if st.session_state.messages and st.session_state.all_chats[st.session_state.current_chat_id]["title"] == "New Chat":
            first_user_msg = next((msg["content"] for msg in st.session_state.messages if msg["role"] == "user"), None)
            if first_user_msg:
                title = first_user_msg[:50] + "..." if len(first_user_msg) > 50 else first_user_msg
                st.session_state.all_chats[st.session_state.current_chat_id]["title"] = title

def load_chat(chat_id: str):
    """Load a specific chat"""
    if chat_id in st.session_state.all_chats:
        save_current_chat()  # Save current before switching
        st.session_state.current_chat_id = chat_id
        st.session_state.messages = st.session_state.all_chats[chat_id]["messages"].copy()

def delete_chat(chat_id: str):
    """Delete a chat"""
    if chat_id in st.session_state.all_chats:
        del st.session_state.all_chats[chat_id]
        # If deleting current chat, clear it
        if st.session_state.current_chat_id == chat_id:
            st.session_state.current_chat_id = None
            st.session_state.messages = []

# Initialize chat management
init_chat_management()

# Sidebar for chat management
with st.sidebar:
    st.header("💬 Chat Management")
    
    # New Chat Button
    if st.button("➕ New Chat", use_container_width=True):
        save_current_chat()
        create_new_chat()
        st.rerun()
    
    st.divider()
    
    # Chat History
    if st.session_state.all_chats:
        st.subheader("Recent Chats")
        
        # Sort chats by last updated
        sorted_chats = sorted(
            st.session_state.all_chats.items(), 
            key=lambda x: x[1]['last_updated'], 
            reverse=True
        )
        
        for chat_id, chat_data in sorted_chats:
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Highlight current chat
                if chat_id == st.session_state.current_chat_id:
                    st.markdown(f"**🟢 {chat_data['title']}**")
                else:
                    if st.button(chat_data['title'], key=f"load_{chat_id}", use_container_width=True):
                        load_chat(chat_id)
                        st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"delete_{chat_id}", help="Delete chat"):
                    delete_chat(chat_id)
                    st.rerun()
            
            # Show last updated time
            last_updated = datetime.fromisoformat(chat_data['last_updated'])
            st.caption(f"Updated: {last_updated.strftime('%m/%d %H:%M')}")
            st.divider()
    else:
        st.info("No chat history yet. Start a new conversation!")

# Main content area
st.title("🧠 LLaMA 3 Chatbot (Groq API)")

# Show current chat info
if st.session_state.current_chat_id:
    current_title = st.session_state.all_chats[st.session_state.current_chat_id]["title"]
    st.caption(f"Current chat: {current_title}")

# Model Selection (Groq only)
model_choice = st.selectbox("Choose a Model", [
    "llama3-8b-8192",
    "llama3-70b-8192"
])
model = model_choice.strip()

# Display past chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle user input
if prompt := st.chat_input("Ask something..."):
    # Create new chat if none exists
    if not st.session_state.current_chat_id:
        create_new_chat()
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Placeholder for assistant response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        response_placeholder.markdown("🧠 Thinking...")

        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                temperature=0.7,
                max_tokens=1024
            )
            answer = response.choices[0].message.content
        except Exception as e:
            answer = f"❌ Error: {e}"

        # Display and save assistant response
        response_placeholder.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        
        # Auto-save the chat
        save_current_chat()