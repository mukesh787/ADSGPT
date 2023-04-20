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
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np
import csv
import os
import shutil
import urllib.request
import zipfile
import datetime
import random

cta_list = ["Apply now", "Book now", "Call Now", "Contact us", "Download", "Learn more", "Get quote", "Order now", "Shop now", "Sign up", "Watch more"]

def load_ads_config():
    with open('ads.yaml') as f:
        data = yaml.load(f, Loader=SafeLoader)
        print(data)
    return data

def create_campaign(user_id, objective, description, ads_platform, ads_format, copies, campaign_name, 
                    campaign_urls, company_name, advertising_goal, 
                    ads_tone, image_variations_count, landing_page_url, logo_url):
    config_yaml = load_ads_config()
    campaign_id = dynamo.create_campaign(user_id, objective, description, ads_platform, ads_format, copies, campaign_name, campaign_urls,
                                         company_name, advertising_goal, ads_tone, image_variations_count, landing_page_url, logo_url)
    
    for item in config_yaml['ads_config']:
        if (item['Platform'] == ads_platform and item['Format'] == ads_format):
            for _ in range(0, copies):
                
                ads = item['ads']
                prompt = model.resolve_copy_prompt(company_name, advertising_goal, objective, description, ads_tone, ads['headline'])
                response = model.complete(prompt, 0.3)
                headline  = response['choices'][0]['message']['content']
                                                                
                prompt = model.resolve_copy_prompt(company_name, advertising_goal, objective, description, ads_tone, ads['text'])
                response = model.complete(prompt, 0.3)
                text  = response['choices'][0]['message']['content']
                                    
                prompt = model.resolve_copy_prompt(company_name, advertising_goal, objective, description, ads_tone, ads['description'])
                
                response = model.complete(prompt, 0.5)
                description  = response['choices'][0]['message']['content']
                cta_text = get_cta(company_name, advertising_goal, objective, description, cta_list)
                
                for _ in range(0, image_variations_count):
                    ad_id = str(uuid.uuid4())
                    
                    images = item['images']
                    response = model.generate_image(advertising_goal, images['resolution'], images['count'])
                    url = response['data'][0]['url']
                
                    object_name = ad_id + "_" +campaign_name.lower().replace(" ", "") + ".png"
                    s3_url = upload_image(object_name, url)
                
                    if url:
                        creatives = dict({"headline": headline, "text": text, "description": description, "cta": cta_text, "url": s3_url})
                        dynamo.create_ads(ad_id, campaign_id, creatives)
            return campaign_id

def get_cta(company_name, advertising_goal, objective, description, cta_list):
    query = "Please pick up a suitable cta from the list and only return a single cta name in the output and do not add any additional text"
    prompt = model.resolve_cta_prompt(company_name, advertising_goal, objective, description, cta_list, query)
    response = model.complete(prompt, 0.0)
    cta_text = response['choices'][0]['message']['content']
    print("CTA text is ", cta_text)
    for cta in cta_list:
        if cta_text.find(cta) > 0:
            return cta
    return random.choice(cta_list)

def upload_image(object_name, url):
    image = requests.get(url, stream=True)
    url = s3.upload_to_s3(object_name, image.raw)
    return url

def get_campaign_ads(campaign_id):
    ads = dynamo.get_all_campaign_ads(campaign_id)
    print("ads")
    print(ads)
    campaigns = dynamo.get_campaign_details(campaign_id)
    result = []
    for ad in ads['Items']:
        for campaign in campaigns['Items']:
            if ad['campaign_id'] == campaign['campaign_id']:
                ad['campaign_name'] = campaign['campaign_name']
                result.append(ad)
                    
    return result


def regenerate_ads(ad_id, data):
    response = dynamo.get_ads(ad_id)
    if len(response['Items']) > 0:
        item = response['Items'][0]
        if 'headline' in data:
            new_headline = data['headline']
            creatives = json.loads(item['creatives'])
            old_headline = creatives['headline']
            response = model.regenerate_ad_copies(old_headline, new_headline, 27)
            text  = response['choices'][0]['message']['content']
            creatives['headline'] = text
            return (json.dumps({"headline": text, "old_headline": old_headline}), 200)
        elif 'text' in data:
            new_text = data['text']
            creatives = json.loads(item['creatives'])
            old_text = creatives['text']
            response = model.regenerate_ad_copies(old_text, new_text, 125)
            text  = response['choices'][0]['message']['content']
            creatives['text'] = text
            return (json.dumps({"text": text, "old_text": old_text}), 200)
        else:
            print("regenerate image url")
            
                        
def get_ads_config(campaign):
    config_yaml = load_ads_config()
    config = filter(lambda config : config['Platform'] == campaign['ads_platform'] and config['Format'] == campaign['ads_format'], config_yaml)
    return config

def upload_files(files):
    urls = []
    for file in files:
        prefix = str(uuid.uuid4())
        object_name = prefix + "_" + file.filename.lower().replace(" ", "")
        url = s3.upload_to_s3(object_name, file)
        urls.append(url)
    return urls

def regenerate_images(file):
        temp_path = os.getenv("TEMP_PATH")
        filename = secure_filename(file.filename)
        path = os.path.join("/", temp_path, filename)
        file.save(path)
        square_image(path)
        url = model.edit_image(path)
        prefix = str(uuid.uuid4())
        object_name = prefix + "_" +file.filename.lower().replace(" ", "")
        s3_url = upload_image(object_name, url)
        return s3_url

def square_image(path):
    im = Image.open(path)
    sqrWidth = np.ceil(np.sqrt(im.size[0]*im.size[1])).astype(int)
    im_resize = im.resize((sqrWidth, sqrWidth))
    im_resize.save(path)
    
def get_user_campaigns(user_id):
    response = dynamo.fetch_user_campaigns(user_id)
    for item in  response['Items']:
        ads = dynamo.get_all_campaign_ads(item['campaign_id'])
        item['ads'] = ads['Items']  
    sorted_items = sorted(response['Items'], key=lambda x: datetime.datetime.strptime(x.get('updated_ts', '1970-01-01 00:00:00'), '%Y-%m-%d %H:%M:%S'), reverse=True)
    return sorted_items
        

def export_ads(ad_ids):
    TEMP_PATH = os.getenv("TEMP_PATH")
    os.makedirs(TEMP_PATH, exist_ok=True)

    # create csv file
    csv_path = os.path.join(TEMP_PATH, "creatives.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["headline", "text", "description", "cta"])
        for ad_id in ad_ids:
            creatives = dynamo.get_creatives_ads(ad_id)
            creatives_dict = json.loads(creatives)
            writer.writerow([
                creatives_dict["headline"].replace('"', ''),
                creatives_dict["text"].replace('"', ''),
                creatives_dict["description"].replace('"', ''),
                creatives_dict.get("cta", "").replace('"', '')
            ])
            
    # download images
    image_paths = []
    for ad_id in ad_ids:
        creatives = dynamo.get_creatives_ads(ad_id)
        creatives_dict = json.loads(creatives)
        image_url = creatives_dict["url"]
        image_path = os.path.join(TEMP_PATH, os.path.basename(image_url))
        urllib.request.urlretrieve(image_url, image_path)
        image_paths.append(image_path)

    # create zip file
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    campaign_id = dynamo.get_campaign_id(ad_ids[0])
    campaign_name = dynamo.get_campaign_name(campaign_id)
    campaign_name = campaign_name.replace(' ', '_')
    zip_name = f"{campaign_name}_{today}.zip"
    zip_path = os.path.join(os.getcwd(), zip_name)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        folder_name =  f"{campaign_name}_{today}"
        zipf.write(csv_path, os.path.join(folder_name, os.path.basename(csv_path)))
        for image_path in image_paths:
            zipf.write(image_path, os.path.join(folder_name, os.path.basename(image_path)))

    # delete temporary folder
    shutil.rmtree(TEMP_PATH)

    print(f"Successfully created zip file: {zip_path}")
    zip_url = s3.upload_zip_to_s3(zip_name)
    return zip_url

def update_ads(ad_id, data):
    response = dynamo.get_ads(ad_id)
    if len(response['Items']) > 0:
        item = response['Items'][0]
        campaign_id = item['campaign_id']
        new_text = data['text']
        new_description = data['description']
        new_url= data['url']
        new_cta=data['cta']
        creatives = json.loads(item['creatives'])
        creatives['text'] = new_text
        creatives['description'] = new_description
        creatives['url'] = new_url
        creatives['cta'] = new_cta
        dynamo.create_ads(ad_id, campaign_id, creatives)
        return (json.dumps({"message": "updated successfully"}), 200)
