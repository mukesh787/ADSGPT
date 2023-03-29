from openai.embeddings_utils import get_embedding, cosine_similarity
from collections import Counter
import re
import ai
import pandas as pd
from werkzeug.utils import secure_filename
import os
import db
import os
import dynamo
CHUNK_SIZE = 1048

def use_key(api_key):
    api_key = os.getenv("OPENAI_KEY")
    ai.use_key(api_key)

def query_by_vector(df, search_vector):
    df["similarity"] = df.vectors.apply(lambda x: cosine_similarity(x, search_vector))
    results = (
        df.sort_values("similarity", ascending=False)
        .head(3)
    )
    return results

def get_vectors(text_list):
    "transform texts into embedding vectors"
    vectors = []
    usage = Counter()
    for _,text in enumerate(text_list):
        resp = ai.embedding(text)
        v = resp['vector']
        u = resp['usage']
        u['cnt'] = 1
        usage.update(u)
        vectors += [v]
    return {'vectors':vectors, 'usage':dict(usage)}


def index_file(file, user_id):
    use_key(None)
    file_name = file.filename
    content = read_file(file)
    create_embeddings(content, 512, user_id, file_name)
    dynamo.put_chat(user_id, file_name)
    
def read_file(file):
    filename = secure_filename(file.filename)
    file.save(os.path.join("/", "tmp", filename))
    with open("/tmp/"+filename) as f:
        file_content = f.read()
    return file_content
                                      
def get_vectors(pages):
    vectors = []
    usage = Counter()
    for index,page in enumerate(pages):
        resp = ai.embedding(page)
        vector = resp['vector']
        db.saveEmbeddings(str(index), vector)
        u = resp['usage']
        u['cnt'] = 1
        usage.update(u)
    return {'vectors':vectors, 'usage':dict(usage)}


def create_embeddings(content, batch_size, user_id, file_name):
    "split pages (list of texts) into smaller fragments (list of texts)"
    file = file_name.split(".")[0]
    batch_size = len(content)
    for i in range(0, len(content), len(content)):
        i_end = min(i+batch_size, len(content))
        lines_batch = content[i: i+batch_size]
        ids_batch = [file+str(i_end)]
        resp = ai.embedding(lines_batch)
        vector = resp['data'][0]['embedding']
        embeds = [record['embedding'] for record in resp['data']]
        to_upsert = zip(ids_batch, embeds, [{"text": lines_batch, "user_id": user_id, "file_name": file_name}])
        db.createIndex(len(vector))
        db.saveEmbeddings(to_upsert)

def text_to_fragments(text, size, page_offset):
    "split single text into smaller fragments (list of texts)"
    if size and len(text)>size:
        out = []
        pos = 0
        page = 1
        p_off = page_offset.copy()[1:]
        eos = find_eos(text)
        if len(text) not in eos:
            eos += [len(text)]
        for i in range(len(eos)):
            if eos[i]-pos>size:
                text_fragment = f'PAGE({page}):\n'+text[pos:eos[i]]
                out += [text_fragment]
                pos = eos[i]
                if eos[i]>p_off[0]:
                    page += 1
                    del p_off[0]
        # ugly: last iter
        text_fragment = f'PAGE({page}):\n'+text[pos:eos[i]]
        out += [text_fragment]
        #
        out = [x for x in out if x]
        return out
    else:
        return [text]

def fix_text_problems(text):
    text = re.sub('\s+[-]\s+','',text) # word continuation in the next line
    return text

def find_eos(text):
    "return list of all end-of-sentence offsets"
    return [x.span()[1] for x in re.finditer('[.!?]\s+',text)]

def query(text, user_id, file_name, is_stream):
    use_key(None)
    print(user_id, file_name)
    resp = ai.embedding(text)
    vector = resp['data'][0]['embedding']
    res = db.queryEmbeddings(vector, user_id, file_name)
    contexts = [
        x['metadata']['text'] if x['metadata']['file_name'].strip() == file_name.strip() else '' for x in res['matches']
    ]
    print(contexts)
    prompt_start = (
        "Answer the question based on the context below.\n\n"+
        "Context:\n"
    )
    prompt_end = (
        f"\n\nQuestion: {text}\nAnswer:"
    )
    limit = 3700
    for i in range(0, len(contexts)):
        if len("\n\n---\n\n".join(contexts[:i])) >= limit:
            prompt = (
                prompt_start +
                "\n\n---\n\n".join(contexts[:i-1]) +
                prompt_end
            )
            break
        elif i == len(contexts)-1:
            prompt = (
                prompt_start +
                "\n\n---\n\n".join(contexts) +
                prompt_end
            )
    
    response = ai.complete([dict({"role": "user", "content": prompt})], is_stream)
    return response
