from openai.embeddings_utils import get_embedding, cosine_similarity
from collections import Counter
import re
import ai
import pandas as pd
from werkzeug.utils import secure_filename
import os
import os
import dynamo
CHUNK_SIZE = 1048

def use_key(api_key):
    api_key = os.getenv("OPENAI_KEY")
    ai.use_key(api_key)

def create_ad_copies(context, text, temperature):
    use_key(None)
    prompt = f"""
        Answer the question based on the context below.
        
        Context:
        {context}
        
        Question: {text}
        
        Answer:"""
    response = ai.complete(prompt, temperature)
    return response

def regenerate_ad_copies(old_headline, new_headline, limit):
    use_key(None)
    prompt = f"""
        {'I want you to act as ads copywriting expert,'}
        
        Based on your previous response, users wants few modifications on the ads copy, your previous response was {old_headline}
        
        Generate a new ad copy based on this instuction {new_headline}, but the generated copy should be with {limit}
        
        Answer:"""
    response = ai.complete(prompt)
    return response
    

def generate_image(prompt, resolution, n):
    use_key(None)
    response = ai.generate_image(prompt, resolution, n)
    print(response)
    return response