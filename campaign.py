
import s3
import model
import dynamo
import yaml
import json
from yaml.loader import SafeLoader
from PIL import Image
import requests
import uuid

def load_ads_config():
    with open('ads.yaml') as f:
        data = yaml.load(f, Loader=SafeLoader)
        print(data)
    return data

def create_campaign(objective, description, ads_platform, ads_format, copies, campaign_name):
    config_yaml = load_ads_config()
    campaign_id = dynamo.create_campaign(objective, description, ads_platform, ads_format, copies, campaign_name)
    for item in config_yaml['ads_config']:
        if (item['Platform'] == ads_platform and item['Format'] == ads_format):
            for i in range(0, copies):
                ad_id = str(uuid.uuid4())
                ads = item['ads']
                context = "Generate ads copies for " + ads_platform + " ad format is " + ads_format + " for the product " + campaign_name
                response = model.create_ad_copies(context, ads['headline'], 0.3)
                headline  = response['choices'][0]['message']['content']
                
                response = model.create_ad_copies(context, ads['text'], 0.3)
                text  = response['choices'][0]['message']['content']
                
                response = model.create_ad_copies(context, ads['description'], 0.5)
                description  = response['choices'][0]['message']['content']
                
                images = item['images']
                response = model.generate_image(campaign_name, images['resolution'], images['count'])
                url = response['data'][0]['url']
                
                object_name = ad_id + "_" +campaign_name.lower().replace(" ", "") + ".png"
                s3_url = upload_image(object_name, url)
                if url:
                    creatives = dict({"headline": headline, "text": text, "description": description, "url": s3_url})
                    dynamo.create_ads(ad_id, campaign_id, creatives)
            return campaign_id
                

def upload_image(object_name, url):
    image = requests.get(url, stream=True)
    url = s3.upload_to_s3(object_name, image.raw)
    return url

def get_campaign_ads(campaign_id):
    ads = dynamo.get_ads(campaign_id)
    campaigns = dynamo.get_campaign_details(campaign_id)
    result = []
    for ad in ads['Items']:
        for campaign in campaigns['Items']:
            if ad['campaign_id'] == campaign['campaign_id']:
                ad['campaign_name'] = campaign['campaign_name']
                result.append(ad)
                    
    return result
                
            
            