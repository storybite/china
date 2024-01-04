import requests
import json

class RestResponse:
     
    def __init__(self, response) -> None:
        self.data  = response.json()
    
    @property
    def candidates(self):
        return self.data['candidates']
    
    @property
    def content(self):
        return self.data['candidates'][0]['content']    
    
    @property
    def text(self)->str:
        return self.data['candidates'][0]['content']['parts'][0]['text']


class RestModel:

    def __init__(self, model: str):
        self.model=model
        self.api_key = None
        
    def configure(self, api_key: str):
        self.api_key = api_key        
            
    def generate_content(self, data:list[dict], generation_config:dict=None, safety_settings:dict=None):                
        sending_data = {"contents": data}        
        if safety_settings is not None:
            sending_data.update({"safetySettings": safety_settings})
        if generation_config is not None:
            sending_data.update({"generationConfig": generation_config})
        print(f'sending_data: {sending_data}')
        response = requests.post(
                        url=f'https://generativelanguage.googleapis.com/v1beta/models/{self.modeel}:generateContent', 
                        headers={'Content-Type': 'application/json'}, 
                        data=json.dumps(sending_data), 
                        params={'key': self.api_key}
                    )
        if response.status_code != 200:
            raise requests.HTTPError(response.json())
        
        return RestResponse(response)   



system_role = """
당신은 중식 레스토랑의 예약 담당 직원으로서, 고객의 예약 요청에 대해 밝고 친절하게 응대해야 합니다.
- 사용자가 인사하면 이모티콘과 함께 "안녕하세요? 구글 중국집 김구글이라고 합니다. 무엇을 도와드릴까요?"라고 말합니다.
- 음식값에 대해 물어보면 아래 "메뉴"에서 찾아서 답해야 합니다.
    "메뉴": {"짜장면":"10000원", "짬뽕": "15000원", "탕수육": "30000원"}
- 이상의 내용 이외에 대해서 질문하면 정확히 모르겠다고 말하고, 전화번호를 알려주면 확인 후 답변하겠다고 말할 것.
"""
confirm = "당신의 역할에 대해 명확히 인지했으면 '네'라고만 답할 것."

class RestChatbot:
    
    def __init__(self, model_name='gemini-pro'):
        self.model =  RestModel(model_name)
        self.messages = []
        self.add_user_message([system_role, confirm]) 
        response = self.send_request()
        self.add_response(response)
        
    def add_user_message(self, user_message: str):
        if isinstance(user_message, list):
            m_list = [{"text": v} for v in user_message ]
        else:
            m_list = [{"text": user_message}]
        self.messages.append({"role": "user", "parts": m_list})

    def send_request(self)->RestResponse:
        response: RestResponse = self.model.generate_content(self.messages)
        return response
        
    def add_response(self, response: RestResponse)->str:
        self.messages.append({"role": "model", "parts": [response.text]})
        return response.text



if __name__ == "__main__":
    # model = RestModel("gemini-pro")
    # model.configure(api_key="AIzaSyD6cnBeAH8hgSgvrQOaU7CuXIDcGrS03QM")
    # messages = [
    #     {'role':'user',
    #      'parts': [{"text":"안녕?"}]}
    # ]
    # response = model.generate_content(messages)
    # print(response.text)
    
    chatbot = RestChatbot("gemini-pro")
    chatbot.add_user_message("안녕?")
    response = chatbot.send_request()
    print(response.text)
    