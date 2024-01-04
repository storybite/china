import streamlit as st
import time
from c_chatbot import Chatbot
from google.oauth2 import service_account
import vertexai
import requests
import os
import google.ai.generativelanguage as glm
from vertexai.preview.generative_models import (    
    GenerativeModel,
)


def check_server(port):
    try:
        response = requests.get(f"http://localhost:{port}")
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.ConnectionError:
        return False

# if check_server(8501):
#     print("local 서버가 실행 중입니다.")    
#     # scoped_credentials = credentials.with_scopes(
#     # ['https://www.googleapis.com/auth/cloud-platform', 'https://www.googleapis.com/auth/generative-language.retriever'])
# else:
#     print("remote 서버가 실행 중입니다.")
#     credentials = service_account.Credentials.from_service_account_info(st.secrets["gcs_connections"])
#     vertexai.init(project="semantic-1", location="us-central1", credentials=credentials)
#     print(f'credentials:=====================================> {credentials}')

st.title("Google Chinese Restaurant!!!!~") 

@st.cache_resource
def load_chatbot():
    os.write(1,b'Something was executed.\n')
    print("1")
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"] 
    print("2")
    print("os.environ GOOGLE_API_KEY================================>", os.environ["GOOGLE_API_KEY"])
    print("3")
    print("st.secrets gcs_connections================================>", st.secrets["gcs_connections"])
    print("4")
    credentials = service_account.Credentials.from_service_account_info(st.secrets["gcs_connections"]) 
    
    print("credentials ================================>", credentials)
    
    vertexai.init(project="semantic-1-409712", credentials=credentials)
    
    model = GenerativeModel("gemini-pro")
    
    resp = model.generate_content("hi")
    print("resp2", resp.text)
    
    return  Chatbot(model_name="gemini-pro")

print("33333333333333")

chatbot = load_chatbot()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
        
for idx, message in enumerate(chatbot.messages):
    if idx > 1:
        with st.chat_message(message["role"]):
            st.markdown(message["parts"][0])

# Accept user input
if prompt := st.chat_input("What is up?"):
    chatbot.add_user_message(prompt)
    #with st.chat_message("user", avatar="🧑‍💻"):  avatar=st.image('path_to_image'
    with st.chat_message("user"):  
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        response = chatbot.send_request()
        assistant_response = chatbot.add_response(response)    
        
        # Simulate stream of response with milliseconds delay
        for chunk in assistant_response.split():
            full_response += chunk + " "
            time.sleep(0.05)
            # Add a blinking cursor to simulate typing
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    