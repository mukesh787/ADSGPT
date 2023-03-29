
import s3
import model
import dynamo
import yaml
import json
from yaml.loader import SafeLoader

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
                ads = item['ads']
                context = "Generate ads copies for " + ads_platform + " ad format is " + ads_format + " for the product " + campaign_name
                response = model.create_ad_copies(context, ads['headline'], 0.3)
                headline  = response['choices'][0]['message']['content']
                
                response = model.create_ad_copies(context, ads['text'], 0.3)
                text  = response['choices'][0]['message']['content']
                
                response = model.create_ad_copies(context, ads['description'], 0.3)
                description  = response['choices'][0]['message']['content']
                
                images = item['images']
                response = model.generate_image(campaign_name, images['resolution'], images['count'])
                url = response['data'][0]['url']
                
                creatives = dict({"headline": headline, "text": text, "description": description, "url": url})
                dynamo.create_ads(campaign_id, creatives)
                
                
def get_campaign_ads(campaign_id):
    response = dynamo.get_ads(campaign_id)
    return response['Items']
                
            
            