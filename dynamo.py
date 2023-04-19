import boto3
import os
from boto3.dynamodb.conditions import Key
import json
from datetime import datetime
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

def create_campaign(user_id, objective, description, ads_platform, ads_format, copies, campaign_name, campaign_urls,
                    company_name, advertising_goal, ad_tone, image_variations_count, landing_page_url, logo_url):
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
            'ads_format': ads_format,
            'copies': copies,
            'campaign_urls': campaign_urls,
            'company_name': company_name,
            'advertising_goal' :advertising_goal,
            'ad_tone':ad_tone,
            'image_variations_count':image_variations_count,
            'landing_page_url' : landing_page_url,
            'logo_url':logo_url
            
        }
    )
    return campaign_id

def create_ads(ad_id, campaign_id, creatives):
    dynamodb = dynamo_connect()
    ads_table = dynamodb.Table("ads")
    ads_table.put_item(
        Item = {
            'ad_id': ad_id,
            'campaign_id': campaign_id,
            'creatives': json.dumps(creatives)
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

def update_campaign(campaign_id, object):
    dynamodb = dynamo_connect()
    campaign_table = dynamodb.Table("campaign")
    response = campaign_table.update_item(
        Key={'campaign_id': campaign_id},
        AttributeUpdates = object
    )
    return response

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

    
    

