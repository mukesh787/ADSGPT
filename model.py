from openai.embeddings_utils import get_embedding, cosine_similarity
from collections import Counter
import re
import ai
import pandas as pd
from werkzeug.utils import secure_filename
import os
import os
from langchain import OpenAI, ConversationChain, LLMChain, PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import load_prompt

def use_key(api_key):
    api_key = os.getenv("OPENAI_KEY")
    ai.use_key(api_key)

def complete(prompt, temperature):
    use_key(None)
    response = ai.complete(prompt, temperature)
    return response

def resolve_copy_prompt(company_name, ads_goal, objective, problem, ads_tone, query):
    template = load_prompt("./prompts/ad_copies.yaml")
    prompt = template.format(company_name=company_name, ads_goal=ads_goal, objective=objective, problem=problem, ads_tone=ads_tone, query=query)
    return prompt

def resolve_cta_prompt(company_name, ads_goal, objective, problem, cta, query):
    template = load_prompt("./prompts/cta.yaml")
    prompt = template.format(company_name=company_name, ads_goal=ads_goal, objective=objective, problem=problem, cta=cta, query=query)
    return prompt
    
def regenerate_ad_copies(new_headline, limit):
    use_key(None)
    prompt = f"""
        {'I want you to act as ads copywriting expert '}
                
        Generate a new ad copy based on this instuction {new_headline}, but the generated copy should be within {limit} characters limit
        
        Answer:"""
    response = ai.complete(prompt, temperature=0.3)
    return response
    

def generate_image(prompt, resolution, n):
    use_key(None)
    response = ai.generate_image(prompt, resolution, n)
    print(response)
    return response

def edit_image(path):
    use_key(None)
    return ai.generate_variation(path)