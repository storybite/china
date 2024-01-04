import google.generativeai as genai
from google.generativeai.types.generation_types import GenerateContentResponse 
from pprint import pprint

from vertexai.preview.generative_models import GenerativeModel, FunctionDeclaration, Part, Tool, Part, GenerationResponse
from google.oauth2 import service_account
import vertexai

service_account_file_name = 'D:/google_key/_gemini/new_service_account_key.json'
credentials = service_account.Credentials.from_service_account_file(service_account_file_name)
   
vertexai.init(project="semantic-1-409712", credentials=credentials)

#presentRoomFeatures

is_table_available = FunctionDeclaration(
    name="is_table_available",
    description="교객이 질의한 일시에 예약이 가능한지 확인한다.",
    parameters={
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "고객이 말한 날짜(형식: yyyy-mm-dd)\n[!important]:오늘은 2024-01-04"
            },
            "time": {
                "type": "string",
                "description": "고객이 말한 시각(형식: HH24시 MI분, 예시: 19시 00분)"
            }
        }
    },
)



get_food_price = FunctionDeclaration(
    name="get_food_price",
    description="주문하려는 메뉴 가격 얻기",
    parameters={
    "type": "object",
    "properties": {
        "food": {
            "type": "string",
            "description": "주문하려는 메뉴명"
        }
    }
},
)

complete_reservation = FunctionDeclaration(
    name="complete_reservation",
    description="예약을 완료하다.",
    parameters={
    "type": "object",
    "properties": {
        "headcount": {
            "type": "string",
            "description": "인원수"
        },
        "date": {
            "type": "string",
            "description": "예약일자"
        },
        "time": {
            "type": "string",
            "description": "시각"
        }
    }
},
)

#############################
function_declarations=[
    FunctionDeclaration(
        name="inform_room_available",
        description="고객이 말한 날짜와 인원수에 대해 예약이 가능한지 여부",
        parameters={
            "type": "object",
            "properties": {
                "check_in_date": {
                    "type": "string",
                    "description": "고객이 말한  날짜(형식: yyyy-mm-dd)\n[!important]:오늘은 2024-01-04"
                },
                "number_of_guests ": {
                    "type": "number",
                    "description": "고객이 말한 인원수"
                }
            }
        },
    ),    
    FunctionDeclaration(
        name="check_number_of_guests",
        description="인원수 확인(고객이 날짜만 말하고 인원수는 말하지 않은 경우 실행)",
        parameters={
            "type": "object",
            "properties": {
                "check_in_date": {
                    "type": "string",
                    "description": "고객이 말한  날짜(형식: yyyy-mm-dd)"
                }
            }
        },
    ),    
    FunctionDeclaration(
        name="present_rooom_features",
        description="객실에 대해 고객에게 설명한다.",
        parameters={
            "type": "object",
            "properties": {
                "room_grade": {
                    "type": "string",
                    "description": "고객이 설명을 요청하는 객실 등급",
                    "enum": [
                        "Standard",
                        "Superior",
                        "Deluxe"
                    ]
                },         
            }
        },
    ),
    FunctionDeclaration(
        name="answer_room_price ",
        description="객실료에 대한 고객의 질문에 답한다.",
        parameters={
            "type": "object",
            "properties": {
                "room_grade": {
                    "type": "string",
                    "description": "객실 등급",
                    "enum": [
                        "Standard",
                        "Superior",
                        "Deluxe"
                    ]
                },  
                "number_of_guests ": {
                    "type": "number",
                    "description": "투숙인원수"
                }       
            }
        },
    ),
]

system_role1 = """
당신은 호텔 예약 직원으로서 다음 미션을 완수합니다. 
    1) 예약 가능날짜와 인원수를 수집하여 예약 가능한 객실을 검색합니다.
    2) 검색된 객실에 대해 고객의 질문에 응답합니다.

- 인사는 "안녕하세요? 구글 호텔 김구글이라고 합니다. 무엇을 도와드릴까요?"라고 말합니다.
```
당신의 역할에 대해 명확히 인지했으면 '네'라고만 답할 것.
"""

system_role2 = """
Thought, Action, Observation 단계를 번갈아 가며 질문에 답해가는 과정을 통해 <과제/>를 해결합니다.
1. Thought: 현재 상황에 대한 추론
2. Action:
    -  Search : 도구 목록에서 함수를 꺼내서 탐색
    -  Finish : 응답을 반환
3. Observation: 도구를 사용한 결과를 객관적으로 관찰

- 필요한 부분을 나누어 생각(Thought)할 것.
- Action을 출력할 때는 도구명과 keyword를 표기할 것.

<과제>
- 당신은 호델 직원으로 고객의 예약 요청 업무를 수행합니다.
</과제>
```
당신의 역할에 대해 명확히 인지했으면 '네'라고만 답할 것.
"""

system_role = """
1  당신은 호텔 예약 직원으로서 인사는 "안녕하세요? 김구글입니다. 무엇을 도와드릴까요?"라고 말합니다.
2. 당신의 임무는 아래입니다.
    2-1) 고객으로부터 예약 날짜와 인원수를 확인하여 예약 가능한 객실을 검색(함수호출 활용).
         예약 날짜와 인원수를 확인하기 전까지는 절대 가능여부에 대해 답하지 말 것 
    2-2) 검색된 객실에 대해 고객의 질문에 응답(함수호출 활용)

```
당신의 역할에 대해 명확히 인지했으면 '네'라고만 답할 것.
"""

def check_number_of_guests(**kwargs):    
    return {"답변": "몇 분이 투숙 예정이시긴가요?.", "주의사항": "답변대로만 답할 것"}

def inform_room_available(**kwargs):
    check_in_date = kwargs.get('check_in_date', None)
    number_of_guests = kwargs.get('number_of_guests', 0)
    return {"답변": "Delxue와 Standard 룸으로 예약 가능합니다.", "주의사항": "답변대로만 답할 것"}

def present_rooom_features(**kwargs):
    return {"답변": "Delxue 룸은 럭스룸에는 발코니가 있어서 야경을 즐길 수 있고, 조식이 2인에 대해 무료료 제공됩니다.", 
            "주의사항": '답변대로만 답할 것' }

def answer_room_price(**kwargs):
    return {"답변": "100_000원입니다." + "예약을 진행할까요?", "주의사항": '답변대로만 답할 것' }

function_repoistory = {
    "check_number_of_guests": check_number_of_guests,
    "inform_room_available": inform_room_available,
    "present_rooom_features": present_rooom_features,
    "answer_room_price": answer_room_price,
}


class Chatbot:
    
    def __init__(self, model_name='gemini-pro'):
        self.model = GenerativeModel(
                model_name,
                generation_config={"temperature": 0, "top_p":0},                
            ).start_chat()
        self.model.send_message(system_role)
            
    def send_message(self, message:str):
        response = self.model.send_message(message, tools=[Tool(function_declarations)])
        return self._extract_response(response)
    
    def _extract_response(self, response: GenerationResponse):
        part: Part = response.candidates[0].content.parts[0]
        #if hasattr(part._raw_part, "function_call"):        
        if  part.function_call: 
            function_call =  part.function_call
            function_name = function_call.name
            function_args = {key: value for key, value in function_call.args.items()}
            print("function_args=>:", function_args)
            function_result = function_repoistory[function_name](**function_args)
            print("function_result=>:", function_result)
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
    response = chatbot.send_message(message); print(response.text)
    
    #message = "내일 3명 투숙할 건데 예약 가능한가요?"; print(message)
    message = "내일 예약 가능한가요?"; print(message)
    response = chatbot.send_message(message); print(response.text)
    
    message = "3명이요"; print(message)
    response = chatbot.send_message(message); print(response.text)
    
    message = "Deluxe 객실은 어떤 가요?"; print(message)
    response = chatbot.send_message(message); print(response.text)
    
    message = "객실료는 어떻게 되요?"; print(message)
    response = chatbot.send_message(message); print(response.text)

