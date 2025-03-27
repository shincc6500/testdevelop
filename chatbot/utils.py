import json
import re
import requests  # requests 모듈 추가
import xmltodict
import os
import chromadb
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv


def address_info(category: str, address: str):
    """주소 정보를 가져오는 함수"""
    if category not in {"ROAD", "PARCEL"}:
        return None  # JsonResponse 대신 None 반환
    load_dotenv()
    vw_key = os.getenv("VWORLD_API_KEY")
    vw_URL = "https://api.vworld.kr/req/search"
    
    params = {'request': "search", 
              'key': vw_key, 
              'query': address, 
              'type': "address", 
              'category': category}
    
    add_response = requests.get(vw_URL, params=params)
    
    if add_response.status_code != 200:
        return None
    
    parsed_json = add_response.json()
    try:
        add_info = parsed_json["response"]["result"]['items'][0]
        return add_info
    except (KeyError, IndexError):
        return None


def soilexam(PNU_Code):
    """토양 정보를 가져오는 함수"""
    url = 'http://apis.data.go.kr/1390802/SoilEnviron/SoilExam/getSoilExam'
    load_dotenv()
    service_key = os.getenv("SOILEXAM_API_KEY")
    params = {'serviceKey': service_key, 'PNU_Code': PNU_Code}
    soil_response = requests.get(url, params=params)

    if soil_response.status_code != 200:
        return None
    
    try:
        response_json = xmltodict.parse(soil_response.text)["response"]
        return response_json["body"]["items"]["item"]
    except (KeyError, TypeError):
        return None

class SoilExamRAG:
    """토양 정보 기반 추천 시스템"""
    
    def __init__(self, PNU_Code: str, persist_dir="my_vector_store"):
        load_dotenv()
        open_api_key = os.getenv("OPENAI_API_KEY")
        self.PNU_Code = PNU_Code        
        self.model = ChatOpenAI(model="gpt-4o-mini", api_key=open_api_key)
        self.embeddings = OpenAIEmbeddings(api_key=open_api_key)
        self.vector_store = Chroma(
                persist_directory=persist_dir,
                embedding_function=self.embeddings,
                )
        self.retriever = self.vector_store.as_retriever()
    
    def fetch_soil_data(self):
        """토양 데이터 조회"""
        return soilexam(self.PNU_Code)
    
    def retrieve_context(self, input_data):
        """벡터 데이터베이스에서 컨텍스트 검색"""
        if not input_data:
            return ""
        
        query = "\n".join([f"{key}: {value}" for key, value in input_data.items()])
        docs = self.retriever.invoke(query)
        return "\n".join([doc.page_content for doc in docs]) if docs else ""
    
    def contexttojson(self, context): #context를 json으로 변환. 
        entries = re.split(r"\n: \d+\n", context.strip())
        json_list = []
        for entry in entries:
            lines = entry.split("\n")         
            entry_dict = {}
        
            for line in lines:
                if ": " in line:
                    key, value = line.split(": ", 1)
                    if key == "":
                        continue
                    entry_dict[key.strip()] = value.strip() if value.strip() != "NaN" else None
                    json_list.append(entry_dict)
        json_context = [dict(t) for t in {tuple(d.items()) for d in json_list}]
        return json_context
    
    def add_doc(self,json_context, recommendation):
        previous_data_dict = {entry["작물"]: entry for entry in json_context}
        # 결과 저장 리스트
        result = []

        # 현재 JSON을 순회하며 이전 JSON 데이터와 결합
        for rec in recommendation:
            crop_name = rec["추천 작물"]
            recommendation = rec["추천 이유"]
            
            # 이전 JSON에서 해당 작물 데이터를 가져오기
            if crop_name in previous_data_dict:
                crop_details = previous_data_dict[crop_name]
            else:
                crop_details = None  # 매칭되는 데이터가 없을 경우

            # 최종 결과 추가
            result.append({
                "crop": crop_name,
                "reason": recommendation,
                "crop_info": crop_details
            })
        return result

    def get_recommendation(self):
        """토양 정보를 바탕으로 추천 작물 반환"""
        input_data = self.fetch_soil_data()
        if input_data == 0:
            return None
        
        prompt = PromptTemplate(
            template="""
                아래의 참고문서를 사용자 입력과 비교하여 적합한 작물을 3종류까지 JSON 형식으로 추천해 주세요. 추천은 참고 문서 내용 내에서만 진행해 주세요. 
                참고문서에는 context의 내용중 : 46과 같은 처음 첫 줄 내용을 반드시 포함해 주세요. 
                참고문서가 없을 경우 추천할 수 없다고 답변해 주세요. 

                🌱 **사용자 입력 (토양 정보)**:
                {input_data}

                📄 **참고 문서 (작물별 적정 환경)**:
                {context}

                JSON 형식:
                {{
                    "추천 작물": "<추천할 작물>",
                    "추천 이유": "<추천한 이유>",
                    
                }}
                """,
                input_variables=["input_data", "context"]
                )

    
        context = self.retrieve_context(input_data)

        parser = JsonOutputParser()

        chain = prompt | self.model | parser
        recommendation = chain.invoke({"input_data": input_data, "context": context})
        json_context = self.contexttojson(context)
        
        response = self.add_doc(json_context, recommendation)
        # response = recommendation
        
        return response


# utils.py에서 직접 실행을 방지하기 위한 코드
if __name__ == "__main__":
    print("이 파일은 Django 프로젝트에서 import하여 사용하세요.")