from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain.schema.runnable import RunnableBranch
from transformers import pipeline, Gemma3ForCausalLM, AutoTokenizer
from langchain.schema.output_parser import StrOutputParser
from pydantic import BaseModel, ValidationError
from langchain.llms import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from operator import itemgetter
from typing import Literal
import requests
import torch
import os

# Pydantic chema
class TopicClassifier(BaseModel):
    topic: Literal["юридический", "общий"]

# Custom parser
class PydanticClassifierParser(StrOutputParser):
    def parse(self, text: str) -> str:
        try:
            text = text.strip().lower()
            if "юридический" in text:
                return TopicClassifier(topic="юридический")
        except ValidationError:
            pass
        return TopicClassifier(topic="общий")



class LLMClient:
    def __init__(self):
        checkpoint = os.getenv("LLM_NAME")
        self.tokenizer = AutoTokenizer.from_pretrained(checkpoint)

        model = Gemma3ForCausalLM.from_pretrained(
            checkpoint,
            device_map="cuda",
            torch_dtype=torch.bfloat16
        ).eval()

        pipe = pipeline('text-generation',
            model=model,
            tokenizer=self.tokenizer,
            max_new_tokens=1024,
            return_full_text=False, # return only answer
            do_sample=True,
            temperature=0.001,
            top_p=0.95,
            repetition_penalty=1.12)
        
        self.llm = HuggingFacePipeline(pipeline=pipe)

        self.classification_prompt = self.set_classification_prompt()
        self.pre_retrieval_prompt = self.set_pre_retrieval_promt()
        self.prompt = self.set_cot_promt()
        self.general_prompt = self.set_general_prompt()

        # Classification chain for input query
        self.classifier_chain = (
            self.classification_prompt
            | self.llm
            | PydanticClassifierParser()
        )

        self.pre_retrieval_chain = RunnableParallel(
            text=self.get_pre_retrieval_prompt | self.llm,
            query=RunnablePassthrough()
            ) | self.make_retriev
        
        self.lawyer_chain = (
            self.pre_retrieval_chain
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

        self.general_chain = self.general_prompt | self.llm | StrOutputParser()

        self.chain_branch = RunnableBranch(
            (lambda x: x["topic"].topic == "юридический", self.lawyer_chain), # заменить на цепочку с RAG
            self.general_chain
        )

        self.router_chain = (
            RunnablePassthrough.assign(topic=itemgetter("text") | self.classifier_chain)
            | self.chain_branch
            | StrOutputParser()
        )

    def get_pre_retrieval_prompt(self, query):
        query = query['text']
        prompt_text = {"query": query, "num_variants": "2"}  
        pre_retrieval_text = self.pre_retrieval_prompt.invoke(prompt_text)
        pre_retrieval_text = pre_retrieval_text.text 
        return pre_retrieval_text


    def make_retriev(self, data):
        query, text = data["query"]['text'], data["text"]
        querys = [q.strip() for q in text.split('\n') if q.strip()][-int("2"):]
        querys.append(query)
        
        url_faiss_api = os.getenv("FAISS_API_URL") + "/batch_search"
        # Тащит документы
        faiss_response = requests.post(
            url_faiss_api,
            # "http://faiss_api:8000/batch_search",
            # "http://172.18.65.108:8000/search",
            json={"querys": querys, "k": 2}
        )
        context = "\n\n".join([doc["content"] for doc in faiss_response.json()["results"]])
        generate_input = {"context": context, "text": query}
        return generate_input



    def set_classification_prompt(self):
        class_conversation = [{
            "role": "system",
            "content": [{"type": "text", "text": """Ты русскоязычный классификатор."""}]
        }, {
            "role": "user",
            "content": [{"type": "text", "text": """

            Вопрос: {text}

            1. Сначала определи к какой теме относится вопрос 
            2. Затем выбери категорию: "юридический" или "общий" вопрос
            3. В ответе верни название выбранной категории

            Ответ:"""}]
        }]
        classification_template = self.tokenizer.apply_chat_template(conversation=class_conversation,
                                                                     tokenize=False,
                                                                     add_generation_prompt=True)
        classification_prompt = PromptTemplate.from_template(classification_template)
        return classification_prompt

    def set_pre_retrieval_promt(self):
        pre_retrieval_template = self.tokenizer.apply_chat_template(conversation=[{
                "role": "system",
                "content": [{"type": "text", "text": """Ты опытный поисковый ассистент, специализирующийся на оптимизации запросов."""}]
            }, {
                "role": "user",
                "content": [{"type": "text", "text": """Исходный запрос: {query}

                Задание:
                1. Удали все лишние детали, оставив только суть запроса
                2. Сгенерируй {num_variants} разных варианта формулировки
                3. Каждый вариант должен быть максимально кратким и содержательным
                4. Используй ключевые слова из исходного запроса
                5. Избегай повторений и сохрани технические термины

                Формат вывода: Только новые варианты на отдельной строке без нумерации
            
                """}]
                }], 
            tokenize=False,
            add_generation_prompt=True)
        pre_retrieval_prompt = PromptTemplate.from_template(pre_retrieval_template)
        return pre_retrieval_prompt
    
    def set_cot_promt(self):
        template = self.tokenizer.apply_chat_template(conversation=[{
                "role": "system",
                "content": [{"type": "text", "text": """Ты русскоязычный автоматический ассистент юриста.
                Ты отвечаешь на вопросы по законодательству Российской Федерации по представленному контексту"""}]
            }, {
                "role": "user",
                "content": [{"type": "text", "text": """
                Контекст: {context}

                Вопрос: {text}

                Объясни шаг за шагом, прежде чем ответить. Сначала определи ключевые элементы вопроса, 
                затем найди соответствующие информации в контексте, и наконец сформулируй ответ.
                
                Пошаговое объяснение:
                1. Анализирую вопрос: что именно спрашивается?
                2. Ищу в контексте релевантные фрагменты
                3. Связываю информацию из контекста с вопросом
                4. Формулирую окончательный ответ

                Ответ:"""}]
            }], 
            tokenize=False,
            add_generation_prompt=True)
        prompt = PromptTemplate.from_template(template)
        return prompt
    
    def set_general_prompt(self,):
        general_template = self.tokenizer.apply_chat_template(conversation=[{
                "role": "system",
                "content": [{"type": "text", "text": """Ты русскоязычный ассистент по общим вопросам"""}]
            }, {
                "role": "user",
                "content": [{"type": "text", "text": """

                Вопрос: {text}
                Отвечай по существу вопроса
                Ответ:"""}]
            }], 
            tokenize=False,
            add_generation_prompt=True)
        general_prompt = PromptTemplate.from_template(general_template)
        return general_prompt

    
    def generate(self, query: str) -> str:
        result_text = self.router_chain.invoke({'text': query})
        return result_text
    