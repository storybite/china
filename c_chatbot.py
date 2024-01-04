import google.generativeai as genai
from google.generativeai.types.generation_types import GenerateContentResponse
from pprint import pprint
import vertexai
import streamlit as st

system_role = """
당신은 중식 레스토랑의 예약 담당 직원으로서, 고객의 예약 요청에 대해 밝고 친절하게 응대해야 합니다.
- 사용자가 인사하면 이모티콘과 함께 "안녕하세요? 구글 중국집 김구글이라고 합니다. 무엇을 도와드릴까요?"라고 말합니다.
- 음식값에 대해 물어보면 아래 "메뉴"에서 찾아서 답해야 합니다.
    "메뉴": {"짜장면":"10000원", "짬뽕": "15000원", "탕수육": "30000원"}
- 이상의 내용 이외에 대해서 질문하면 정확히 모르겠다고 말하고, 전화번호를 알려주면 확인 후 답변하겠다고 말할 것.
"""
confirm = "당신의 역할에 대해 명확히 인지했으면 '네'라고만 답할 것."

class Chatbot:
    
    def __init__(self, model_name='gemini-pro'):
        #vertexai.init(project="semantic-1", location="us-central1", credentials=st.secrets["gcs_connections"])
        self.model =  genai.GenerativeModel(model_name)
        self.messages = []
        self.add_user_message([system_role, confirm])  
        response = self.send_request()
        self.add_response(response)
        
    def add_user_message(self, user_message: str):
        user_messages = user_message if isinstance(user_message, list) else [user_message]
        self.messages.append({"role": "user", "parts": user_messages})

    def send_request(self)->GenerateContentResponse:
        response: GenerateContentResponse = self.model.generate_content(self.messages)
        return response
        
    def add_response(self, response: GenerateContentResponse)->str:
        self.messages.append({"role": "model", "parts": [response.text]})
        return response.text
        

if __name__ == "__main__":   

    chatbot = Chatbot("gemini-pro")
    pprint(chatbot.messages)        

    user_messages = ["안녕하세요?", "내일 19:00에 예약 가능한가요?", "짜장면은 얼마에요?", "알겠습니다.."]

    for user_message in user_messages:
        print(f'user_message: {user_message}')
        chatbot.add_user_message(user_message)
        response = chatbot.send_request()
        chatbot.add_response(response)
        print(f'response: {response.text}')     

