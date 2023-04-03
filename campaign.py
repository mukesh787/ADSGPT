
import s3
import model
import dynamo
import yaml
import json
from yaml.loader import SafeLoader
from PIL import Image
import requests
import uuid
import ai

def load_ads_config():
    with open('ads.yaml') as f:
        data = yaml.load(f, Loader=SafeLoader)
        print(data)
    return data

def create_campaign(objective, description, ads_platform, ads_format, copies, campaign_name, urls):
    config_yaml = load_ads_config()
    campaign_id = dynamo.create_campaign(objective, description, ads_platform, ads_format, copies, campaign_name, urls)
    for item in config_yaml['ads_config']:
        if (item['Platform'] == ads_platform and item['Format'] == ads_format):
            for _ in range(0, copies):
                ad_id = str(uuid.uuid4())
                ads = item['ads']
                context = "Generate ad copies for " + ads_platform + " ad format is " + ads_format + " for the product " + campaign_name
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
    ads = dynamo.get_all_campaign_ads(campaign_id)
    campaigns = dynamo.get_campaign_details(campaign_id)
    result = []
    for ad in ads['Items']:
        for campaign in campaigns['Items']:
            if ad['campaign_id'] == campaign['campaign_id']:
                ad['campaign_name'] = campaign['campaign_name']
                result.append(ad)
                    
    return result


def update_ads(ad_id, data):
    response = dynamo.get_ads(ad_id)
    if len(response['Items']) > 0:
        item = response['Items'][0]
        campaign_id = item['campaign_id']
        campaign = dynamo.get_campaign_details(campaign_id)
        context = "Generate ads copies for " + campaign['ads_platform'] + " ad format is " + campaign['ads_format'] + " for the product " + campaign['campaign_name']
        if 'headline' in data:
            new_headline = data['headline']
            print("item is ", item)
            creatives = json.loads(item['creatives'])
            old_headline = creatives['headline']
            response = model.regenerate_ad_copies(old_headline, new_headline, 27)
            text  = response['choices'][0]['message']['content']
            print("regenrated headline ", text)
            creatives['headline'] = text
            dynamo.create_ads(ad_id, campaign_id, creatives)
            return json.dumps({"headline": text}, 200)
        elif 'text' in data:
            new_text = data['text']
            creatives = json.loads(item['creatives'])
            old_text = creatives['text']
            response = model.regenerate_ad_copies(old_text, new_text, 125)
            text  = response['choices'][0]['message']['content']
            creatives['text'] = text
            dynamo.create_ads(ad_id, campaign_id, creatives)
            return json.dumps({"text": text})
        else:
            print("regenerate image url")
                        
def get_ads_config(campaign):
    config_yaml = load_ads_config()
    config = filter(lambda config : config['Platform'] == campaign['ads_platform'] and config['Format'] == campaign['ads_format'], config_yaml)
    return config

def upload_files(files):
    urls = []
    for file in files:
        print("each file", file.filename)
        prefix = str(uuid.uuid4())
        object_name = prefix + "_" + file.filename.lower().replace(" ", "")
        url = s3.upload_to_s3(object_name, file)
        print("url is ", url)
        urls.append(url)
    return urls
    