import boto3
import os
from boto3.dynamodb.conditions import Key
import json
from datetime import datetime

def dynamo_connect():
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    REGION_NAME = os.getenv("AWS_REGION")

    dynamodb = boto3.resource(
        'dynamodb',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=REGION_NAME
    )
    return dynamodb

def save_user(user_name, email, pw_hash):
    dynamodb = dynamo_connect()
    users_table = dynamodb.Table("users")
    response = users_table.put_item(
        Item = {
            "user_name": user_name,
            "email": email,
            "password": pw_hash
        }
    )
    return response

def get_user(email):
    dynamodb = dynamo_connect()
    users_table = dynamodb.Table("users")
    response = users_table.query(
        KeyConditionExpression=Key('email').eq(email)
    )
    return response['Items']
    
def get_file_names(user_id):
    dynamodb = dynamo_connect()
    table = dynamodb.Table("chats")

    response = table.query(
        KeyConditionExpression=Key('user-id').eq(user_id)
    )
    
    file_names = [item['file-name'] for item in response['Items']]

    return file_names
    
def delete_file(user_id, file_name):
    dynamodb = dynamo_connect()
    chats_table = dynamodb.Table("chats")
    chats_table.delete_item(
        Key={
            "user-id": user_id,
            "file-name": file_name,  
        }
    )
    file_names= get_file_names(user_id)
    return file_names


def save_chat(text, ai_response, user_id, file_name):
    dynamodb = dynamo_connect()
    chats_table = dynamodb.Table("chats")
    response = chats_table.query(
        KeyConditionExpression=Key('user-id').eq(user_id) & Key('file-name').eq(file_name)
    )
    existing_history = []
    for item in response['Items']:
       existing_history = item.get('history',[])

    new_history = dict({"user": {"message": text}, "bot": {"message": ai_response}})
    existing_history.append(new_history)
    item={
        'user-id': user_id,
        'file-name': file_name,
        'history': existing_history        
    }
    response = chats_table.put_item(Item=item)
    return response


def save_prompt_templates(user_id, data):
    dynamodb = dynamo_connect()
    prompts_templates = dynamodb.Table("prompts-template")
    response = prompts_templates.put_item(
        Item = {
            "user-id": user_id,
            "title": data['title'],
            "is-private": data['is_private'],
            "template": data['template'],
            "teaser": data['teaser'],
            "hint": data['hint'],
            "activity": data['activity'],
            "author-name": data['author_name'],
            "author-url": data['author_url']
        }
    )
    print(response)
    return response

def get_private_prompts(user_id):
    dynamodb = dynamo_connect()
    prompts_templates = dynamodb.Table("prompts-template")
    response = prompts_templates.query(
        KeyConditionExpression=Key('user-id').eq(user_id)
    )
    prompts = [item for item in response['Items'] if item['is-private']]
    return prompts

def get_public_prompts():
    dynamodb = dynamo_connect()
    prompts_templates = dynamodb.Table("prompts-template")
    response = prompts_templates.scan()
    items = response['Items']
    while 'LastEvaluatedKey' in response:
        response = prompts_templates.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])
    prompts = [item for item in items if not item['is-private']]
    return prompts
    
def get_chats(user_id, file_name):
    dynamodb = dynamo_connect()
    table = dynamodb.Table("chats")

    response = table.query(
        KeyConditionExpression=Key('user-id').eq(user_id)& Key('file-name').eq(file_name)
    )
    
    print(response)
    if 'Items' in response and len(response['Items']) > 0:
        for item in response['Items']:
            return item['history']