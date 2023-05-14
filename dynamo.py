import boto3
import os
from boto3.dynamodb.conditions import Key
import json
import datetime
import uuid

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
    user_id = str(uuid.uuid4())
    users_table.put_item(
        Item = {
            "user-id": user_id,
            "user_name": user_name,
            "email": email,
            "password": pw_hash
        }
    )
    return user_id

def get_user(email):
    dynamodb = dynamo_connect()
    users_table = dynamodb.Table("users")
    response = users_table.query(
        IndexName="email-index",
        KeyConditionExpression=Key('email').eq(email)
    )
    return response['Items']

def create_campaign(user_id, objective, description, ads_platform, campaign_name, company_name, advertising_goal, ad_tone):
    dynamodb = dynamo_connect()
    campaign_table = dynamodb.Table("campaign")
    campaign_id = str(uuid.uuid4())
    campaign_table.put_item(
        Item = {
            'user_id': user_id,
            'campaign_id': campaign_id,
            'campaign_name': campaign_name,
            'objective': objective,
            'ads_platform': ads_platform,
            'description': description,
            'company_name': company_name,
            'advertising_goal' :advertising_goal,
            'ad_tone':ad_tone,
            'created_ts':datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_ts':datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') 
        }
    )
    return campaign_id

def create_ads(ad_id, campaign_id, creatives, image_text, carousel_card, ads_format, copies, image_variations_count, landing_page_url, logo_url, campaign_urls):
    dynamodb = dynamo_connect()
    ads_table = dynamodb.Table("ads")
    ads_table.put_item(
        Item = {
            'ad_id': ad_id,
            'campaign_id': campaign_id,
            'creatives': json.dumps(creatives),
            'image_text':image_text,
            'carousel_card':carousel_card,
            'image_text':image_text,
            'carousel_card':carousel_card,
            'copies': copies,
            'campaign_urls': campaign_urls,
            'image_variations_count':image_variations_count,
            'landing_page_url' : landing_page_url,
            'logo_url':logo_url, 
            'ads_format':ads_format
        }
    )
    
def get_all_campaign_ads(campaign_id):
    dynamodb = dynamo_connect()
    ads_table = dynamodb.Table("ads")
    response = ads_table.query(
        IndexName='campaign_id-index',
        KeyConditionExpression=Key('campaign_id').eq(campaign_id)
    )
    return response

def get_campaign_details(campaign_id):
    dynamodb = dynamo_connect()
    campaign_table = dynamodb.Table("campaign")
    response = campaign_table.query(
        KeyConditionExpression=Key('campaign_id').eq(campaign_id)
    )
    return response

def get_ads(ad_id):
    dynamodb = dynamo_connect()
    ads_table = dynamodb.Table("ads")
    response = ads_table.query(
        KeyConditionExpression=Key('ad_id').eq(ad_id)
    )
    return response

def update_campaign(campaign_id, campaign_name, objective, ads_platform, description,  company_name, advertising_goal, ad_tone):
    print("update call")
    dynamodb = dynamo_connect()
    campaign_table = dynamodb.Table("campaign")
    update_dict = {}
    for key, value in {'campaign_name': campaign_name, 'objective': objective, 'ads_platform': ads_platform, 
                      'description': description, 'company_name': company_name, 
                      'advertising_goal': advertising_goal, 'ad_tone': ad_tone}.items():
        
        if value is not None and value != '':
            update_dict[key] = {'Value': value, 'Action': 'PUT'}
    
    update_dict['updated_ts'] = {'Value': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') , 'Action': 'PUT'}

    response = campaign_table.update_item(
        Key={'campaign_id': campaign_id},
        AttributeUpdates=update_dict
    )
   

def fetch_user_campaigns(user_id):
    dynamodb = dynamo_connect()
    campaign_table = dynamodb.Table("campaign")
    response = campaign_table.query(
        IndexName="user_id-index",
        KeyConditionExpression=Key('user_id').eq(user_id)
    )
    return response
def get_creatives_ads(ad_id):
    dynamodb = dynamo_connect()
    ads_table = dynamodb.Table("ads")
    response = ads_table.query(
        KeyConditionExpression=Key('ad_id').eq(ad_id)
    )
    if 'Items' in response:
        items = response['Items']
        if len(items) > 0:
            ad = items[0]
            creatives = ad.get('creatives')
            return creatives
    return None

def get_campaign_id(ad_id):
    dynamodb = dynamo_connect()
    ads_table = dynamodb.Table("ads")
    response = ads_table.query(
        KeyConditionExpression=Key('ad_id').eq(ad_id)
    )
    if 'Items' in response:
        items = response['Items']
        if len(items) > 0:
            ad = items[0]
            campaign_id = ad.get('campaign_id')
            return campaign_id
    return None


def get_campaign_name(campaign_id):
    dynamodb = dynamo_connect()
    campaign_table = dynamodb.Table("campaign")
    response = campaign_table.query(
        KeyConditionExpression=Key('campaign_id').eq(campaign_id)
    )
    if 'Items' in response:
        items = response['Items']
        if len(items) > 0:
            campaign = items[0]
            campaign_name = campaign.get('campaign_name')
            return campaign_name
    return None

def get_all_ad_id(campaign_id):
    dynamodb = dynamo_connect()
    ads_table = dynamodb.Table("ads")
    response = ads_table.query(
        IndexName='campaign_id-index',
        KeyConditionExpression=Key('campaign_id').eq(campaign_id)
    )
    ad_ids = [item['ad_id'] for item in response['Items']]
    while 'LastEvaluatedKey' in response:
        response = ads_table.query(
            IndexName='campaign_id-index',
            KeyConditionExpression=Key('campaign_id').eq(campaign_id),
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        ad_ids.extend([item['ad_id'] for item in response['Items']])
    return ad_ids

def delete_ad(ad_id, campaign_id):
    dynamodb = dynamo_connect()
    ads_table = dynamodb.Table("ads")
    ads_table.delete_item(
        Key={
            "ad_id": ad_id,
            "campaign_id":campaign_id          
        }
    )
    
def delete_ads_by_campaign_id(campaign_id):
    
    dynamodb = dynamo_connect()
    ads_table = dynamodb.Table("ads")
    response = ads_table.query(
        IndexName='campaign_id-index',
        KeyConditionExpression=Key('campaign_id').eq(campaign_id)
    )
    
    for item in response['Items']:
        ads_table.delete_item(
            Key={
                "ad_id": item["ad_id"],
                "campaign_id": item["campaign_id"]
            }
        )
        
        
def get_ads_format_for_campaign(campaign_id):
    dynamodb = dynamo_connect()
    ads_table = dynamodb.Table("ads")
    response = ads_table.query(
        IndexName='campaign_id-index',
        KeyConditionExpression=Key('campaign_id').eq(campaign_id)
    )
    if response['Count'] == 0:
        return None
    else:
        ads_format_set = set()
        for item in response['Items']:
            ads_format_set.add(item['ads_format'])
            print("ads format")
        return ads_format_set
    
def delete_ads_by_campaign_id(campaign_id, formats_to_delete):
    
    dynamodb = dynamo_connect()
    ads_table = dynamodb.Table("ads")
    response = ads_table.query(
        IndexName='campaign_id-index',
        KeyConditionExpression=Key('campaign_id').eq(campaign_id)
    )
    
    for item in response['Items']:
        if item['ads_format'] in formats_to_delete:
            ads_table.delete_item(
                Key={
                    "ad_id": item["ad_id"],
                    "campaign_id": item["campaign_id"]
                }
            )
    
    
    

    
    

