import google.generativeai as genai
from google.generativeai.types.generation_types import GenerateContentResponse 
from pprint import pprint

from vertexai.preview.generative_models import GenerativeModel, FunctionDeclaration, Part, Tool, Part, GenerationResponse
from google.oauth2 import service_account
import vertexai

service_account_file_name = 'D:/google_key/_gemini/new_service_account_key.json'
credentials = service_account.Credentials.from_service_account_file(service_account_file_name)
   
vertexai.init(project="semantic-1-409712", credentials=credentials)


#############################
function_declarations=[
    FunctionDeclaration(
        name="inform_available_bungalows",
        description="고객이 말한 날짜와 인원수에 대해 예약이 가능한지 여부",
        parameters={
            "type": "object",
            "properties": {
                "check_in_date": {
                    "type": "string",
                    "description": "고객이 말한  날짜(형식: yyyy-mm-dd)\n[!important]:오늘은 2024-01-05"
                },
                "number_of_guests ": {
                    "type": "number",
                    "description": "고객이 말한 인원수"
                }
            }
        },
    ),        
    FunctionDeclaration(
        name="present_bungalows_features",
        description="숙소에 대해 고객에게 설명한다.",
        parameters={
            "type": "object",
            "properties": {
                "bungalow_name": {
                    "type": "string",
                    "description": "고객이 설명을 요청하는 숙소 이름",
                    "enum": [
                        "가든동",
                        "숲속동",
                        "오션동"
                    ]
                },         
            }
        },
    ),
    FunctionDeclaration(
        name="answer_bungalows_price",
        description="숙박료에 대한 고객의 질문에 답한다.",
        parameters={
            "type": "object",
            "properties": {
                "bungalow_name": {
                    "type": "string",
                    "description": "숙소 이름",
                    "enum": ["가든동","숲속동","오션동"]
                }       
            }
        },
    ),
    FunctionDeclaration(
        name="make_reservation",
        description="예약을 진행한다.",
        parameters={
            "type": "object",
            "properties": {
                "check_in_date": {
                    "type": "string",
                    "description": "고객이 말한  날짜(형식: yyyy-mm-dd)\n[!important]:오늘은 2024-01-04"
                },
                "bungalow_name": {
                    "type": "string",
                    "description": "숙소 등급",
                     "enum": ["가든동","숲속동","오션동"]
                },
            }
        },
    ),
]

bungalows = {
     "가든동": {"서비스": "정원 뷰", "수용인원": 2, "숙박료": 300_000},
     "숲속동": {"서비스": "계곡 뷰 / 조식 50% 할인", "가능인원": 4, "숙박료": 500_000},
     "오션동": {"서비스": "오션 뷰 / 조식 무료 제공" ,"가능인원": 8, "숙박료": 800_000}
}

bookings = {
    "2024-01-06":  ["숲속동","가든동"],
    "2024-01-13":  ["가든동"]
}

def get_availables(date, number):
    bungalow_names = set(bungalows.keys())
    reserved_bungalow_names = set(bookings.get(date, {}))
    vacant_bungalow_names = bungalow_names.difference(reserved_bungalow_names)    
    availables = []
    for vacant_bungalow_name in vacant_bungalow_names:
        if (capacity := bungalows[vacant_bungalow_name]['가능인원']) >=number:
            availables.append(f"{vacant_bungalow_name}, 가능인원: {capacity}명")     

    return availables

def inform_available_bungalows(**kwargs):
    date = kwargs.get('check_in_date', None)
    number = kwargs.get('number_of_guests', 0)
    answer = get_availables(date, number)
    return {"답변": answer, "주의사항": "답변대로만 답할 것"}

def present_bungalows_features(**kwargs):
    name = kwargs.get('bungalow_name', None)    
    return {"답변": bungalows[name]['서비스'], 
            "주의사항": '답변 범위 내에서만 답할 것' }

def answer_bungalows_price(**kwargs):
    name = kwargs.get('bungalow_name', None)    
    return {"답변": bungalows[name]['숙박료'], 
            "주의사항": '답변 범위 내에서만 답할 것' }

def make_reservation(**kwargs):
    return {"답변": "예약이 완료되었습니다. 감사합니다.", "주의사항": '답변대로만 답할 것' }


function_repoistory = {    
    "inform_available_bungalows": inform_available_bungalows,
    "present_bungalows_features": present_bungalows_features,
    "answer_bungalows_price": answer_bungalows_price,
    "make_reservation": make_reservation,
}

system_role = """
당신은 예약 담당 펜션 직원으로서 아래 절차를 준수하여 임무를 완수합니다.
1. 고객이 인사하면 "안녕하세요? 김구글입니다. 무엇을 도와드릴까요?"라고 인사(emoji)
2. 고객으로부터 예약 날짜와 인원수를 확인하여 예약 가능한 숙소를 확인(함수호출 활용)
    2-1. 인원수를 확인하기 전까지는 절대 예약 가능하다고 답하지 말 것
3. 검색된 숙소에 대해 고객의 질문에 응답(함수호출 활용)
```
당신의 역할에 대해 명확히 인지했으면 '네'라고만 답할 것
"""

class Chatbot:
    
    def __init__(self, model_name='gemini-pro'):
        self.model = GenerativeModel(
                model_name,
                generation_config={"temperature": 0, "top_p":0},                
                tools=[Tool(function_declarations)]
            ).start_chat()
        #self.model.send_message(system_role)
        text = self.send_message(system_role)        
        print("system_role response", text)
            
    def send_message(self, message:str):
        response = self.model.send_message(message)
        return self._extract_response(response)
    
    def _extract_response(self, response: GenerationResponse):
        part: Part = response.candidates[0].content.parts[0]
        if  part.function_call: 
            function_call =  part.function_call
            function_name = function_call.name
            function_args = {key: value for key, value in function_call.args.items()}
            print(f"{function_name} args=>: {function_args}")
            function_result = function_repoistory[function_name](**function_args)
            print(f"{function_name} result=>: {function_result}")
            response = self.model.send_message(
                Part.from_function_response(
                    name=function_name,
                    response={
                        "content": function_result,
                    }
                ),
            )
            print("Part.from_function_response", response)
            return response
        else:
           return response
   
    @property
    def messages(self):
        return [v.parts[0].text for idx, v in enumerate(self.model.history) if idx > 1]
        
        
class Chatbot1:
    
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
        

# if __name__ == "__main__":   

#     chatbot = Chatbot("gemini-pro")
#     pprint(chatbot.messages)        

#     user_messages = ["안녕하세요?", "내일 19:00에 예약 가능한가요?", "짜장면은 얼마에요?", "알겠습니다.."]

#     for user_message in user_messages:
#         print(f'user_message: {user_message}')
#         chatbot.add_user_message(user_message)
#         response = chatbot.send_request()
#         chatbot.add_response(response)
#         print(f'response: {response.text}')     

        

if __name__ == "__main__":   
    chatbot = Chatbot("gemini-pro")
    
    message = "안녕하세요"; print(message)
    print("="*50)
    response = chatbot.send_message(message); print(response.text)
    #message = "내일 3명 투숙할 건데 예약 가능한가요?"; print(message)
    
    message = "다음주 토요일에 3명 숙박하려고 하는데 예약 가능한가요?"; print(message)
    print("="*50)
    response = chatbot.send_message(message); print(response.text)
        
    message = "3명이요"; print(message)
    print("="*50)
    response = chatbot.send_message(message); print(response.text)
        
    message = "오션동은 어떤 가요?"; print(message)
    print("="*50)
    response = chatbot.send_message(message); print(response.text)
        
    message = "숙박료는 어떻게 되요?"; print(message)
    print("="*50)
    response = chatbot.send_message(message); print(response.text)
    print("="*50)
    
    message = "네. 예약해주세요"; print(message)
    print("="*50)
    response = chatbot.send_message(message); print(response.text)
    print("="*50)

