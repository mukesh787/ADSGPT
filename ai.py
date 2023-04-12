"AI (LLM) adapter"
# TODO: replace with ai_bricks.ai_openai

BUTCHER_EMBEDDINGS = None # this should be None, as it cuts the embedding vector to n first values (for debugging)


import tiktoken
import openai
import timeit

def get_token_count(text):
    tokens = num_tokens_from_messages(text)
    return tokens

def use_key(api_key):
    openai.api_key = api_key

def complete(prompt, temperature=0.0):
    messages = [dict({"role": "user", "content": prompt})]
    kwargs = dict(
        model = 'gpt-3.5-turbo',
        temperature = temperature,
        messages = messages,
        n = 1,
    )
    response = openai.ChatCompletion.create(**kwargs)
    return response


def embedding(text):
    resp = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002",
    )
    return resp


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo-0301":  # note: future models may deviate from this
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}""")
    
def generate_image(prompt, resolution, n):
    kwargs = dict(
        prompt = prompt,
        n = n,
        size=resolution
    )
    response = openai.Image.create(**kwargs)
    return response

def generate_variation(path):
    response = openai.Image.create_variation(
        image=open(path, "rb"),
        n=1,
        size="1024x1024"
    )
    image_url = response['data'][0]['url']
    print(image_url)
    return image_url