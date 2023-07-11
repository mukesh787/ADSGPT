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
import zipfile
import datetime
import random
import re
import urllib.request
import multiprocessing

cta_list = ["Apply now", "Book now", "Call Now", "Contact us", "Download", "Learn more", "Get quote", "Order now", "Shop now", "Sign up", "Watch more"]

def load_ads_config():
    with open('ads.yaml') as f:
        data = yaml.load(f, Loader=SafeLoader)
        print(data)
    return data

def process_ads( item, company_name, advertising_goal, objective, description, ads_tone, campaign_urls, cta_list, campaign_id, campaign_name, image_text, carousel_card, ads_format, copies, image_variations_count, landing_page_url, logo_url,ads_platform):
    ads = item['ads']
    headline = generate_copy(company_name, advertising_goal, objective, description, ads_tone, ads['headline'])
    text = generate_copy(company_name, advertising_goal, objective, description, ads_tone, ads['text'])
    cta_text = get_cta(company_name, advertising_goal, objective, description, cta_list)
    
    ad_id = str(uuid.uuid4())
    images = item['images']
    response = model.generate_image(image_text, images['resolution'], images['count'])
    url = response['data'][0]['url']
    
    object_name = ad_id + "_" +campaign_name.lower().replace(" ", "") + ".png"
    s3_url = upload_image(object_name, url)
    
    print(s3_url)

    if s3_url:
        creatives = dict({"text": text, "headline": headline, "cta": cta_text, "url": s3_url})
        dynamo.create_ads(ad_id, campaign_id, creatives, image_text, carousel_card, ads_format, copies, image_variations_count, landing_page_url, logo_url, campaign_urls,ads_platform )

def process_carousel_ads(item, company_name, advertising_goal, objective, description, ads_tone, campaign_urls, cta_list, campaign_id, campaign_name, image_text, cards, ads_format, copies, image_variations_count, landing_page_url, logo_url,ads_platform):
    ads = item['ads']
    text = generate_copy(company_name, advertising_goal, objective, description, ads_tone, ads['text'])
    images = item['images']
    ad_id = str(uuid.uuid4())
    carousel_cards = []
    for i in range(cards):
        headline = generate_copy(company_name, advertising_goal, objective, description, ads_tone, ads['headline'])
        cta_text = get_cta(company_name, advertising_goal, objective, description, cta_list)
        response = model.generate_image(image_text, images['resolution'], images['count'])
        url = response['data'][0]['url']
        object_name = ad_id + "_" + campaign_name.lower().replace(" ", "") + f"_card{i+1}.png"
        s3_url = upload_image(object_name, url)
        if s3_url:
            card = dict({"headline": headline, "cta": cta_text, "image_url": s3_url})  # Add headline and CTA text for each card
            carousel_cards.append(card)
        print(s3_url)

    if len(carousel_cards) >= 2:
        creatives = dict({"text": text ,"cards": carousel_cards})
        dynamo.create_ads(ad_id, campaign_id, creatives,image_text, cards, ads_format, copies, image_variations_count, landing_page_url, logo_url, campaign_urls,ads_platform)
     
def process_facebook_stories(item, company_name, advertising_goal, objective, description, ads_tone, campaign_urls, cta_list, campaign_id, campaign_name, image_text, carousel_card, ads_format, copies, image_variations_count, landing_page_url, logo_url,ads_platform):
    ads = item['ads']
    headline = generate_copy(company_name, advertising_goal, objective, description, ads_tone, ads['headline'])
    text = generate_copy(company_name, advertising_goal, objective, description, ads_tone, ads['text'])
    cta_text = get_cta(company_name, advertising_goal, objective, description, cta_list)
    
    ad_id = str(uuid.uuid4())
    images = item['images']

    response = model.generate_image(image_text, images['resolution'], images['count'])
    url = response['data'][0]['url']
    
    object_name = ad_id + "_" +campaign_name.lower().replace(" ", "") + ".png"
    s3_url = upload_image(object_name, url)
    
    print(s3_url)

    if s3_url:
        creatives = dict({"text": text, "headline": headline, "cta": cta_text,  "url": s3_url})
        dynamo.create_ads(ad_id, campaign_id, creatives, image_text, carousel_card, ads_format, copies, image_variations_count, landing_page_url, logo_url, campaign_urls,ads_platform)
        
def process_text_ads(item, company_name, advertising_goal, objective, description, ads_tone, campaign_urls, cta_list, campaign_id, campaign_name, image_text, carousel_card, ads_format, copies, image_variations_count, landing_page_url, logo_url,ads_platform):
    ads = item['ads']
    headline1 = generate_copy(company_name, advertising_goal, objective, description, ads_tone, ads['headline1'])
    headline2 = generate_copy(company_name, advertising_goal, objective, description, ads_tone, ads['headline2'])
    headline3 = generate_copy(company_name, advertising_goal, objective, description, ads_tone, ads['headline3'])
    description1 = generate_copy(company_name, advertising_goal, objective, description, ads_tone, ads['description1'])
    description2 = generate_copy(company_name, advertising_goal, objective, description, ads_tone, ads['description2'])
    cta_text = get_cta(company_name, advertising_goal, objective, description, cta_list)
    ad_id = str(uuid.uuid4())
    creatives = dict({"headline1": headline1, "headline2": headline2, "headline3": headline3, "description1": description1, "description2": description2 , "cta": cta_text})
    print(creatives)
    dynamo.create_ads(ad_id, campaign_id, creatives,image_text, carousel_card, ads_format, copies, image_variations_count, landing_page_url, logo_url, campaign_urls,ads_platform)
       
def create_campaign(user_id, objective, description, ads_platform, ads_format, copies, campaign_name, 
                    campaign_urls, company_name, advertising_goal, 
                    ads_tone, image_variations_count, landing_page_url, logo_url, image_text, carousel_card ):
    
    config_yaml = load_ads_config()
    for item in ads_format:
        if item == 'carousel':
            # Set image variations count to 1 for carousel ads
            image_variations_count = 1
        if item == 'Text':
            # Set image variations count to 1 for Text
            image_variations_count = 1
    campaign_id = dynamo.create_campaign(user_id, objective, description, ads_platform,campaign_name,company_name, advertising_goal, ads_tone,)
    processes = []
    p = None 
    for item in config_yaml['ads_config']:
        if (item['Platform'] == ads_platform):
            for it in ads_format:
                if item['Format'] == it:
                    for _ in range(0, copies*image_variations_count):
                        if it == 'carousel':
                            p = multiprocessing.Process(target=process_carousel_ads, args=(item, company_name, advertising_goal, objective, description, ads_tone, campaign_urls, cta_list, campaign_id, campaign_name, image_text, carousel_card, it, copies, image_variations_count, landing_page_url, logo_url,ads_platform))
                        elif it=='Facebook Stories':
                            p = multiprocessing.Process(target=process_facebook_stories, args=(item, company_name, advertising_goal, objective, description, ads_tone, campaign_urls, cta_list, campaign_id, campaign_name, image_text, carousel_card, it, copies, image_variations_count, landing_page_url, logo_url,ads_platform))
                        elif it=='NewsFeed':
                            p = multiprocessing.Process(target=process_ads, args=( item, company_name, advertising_goal, objective, description, ads_tone, campaign_urls, cta_list, campaign_id, campaign_name, image_text, carousel_card, it, copies, image_variations_count, landing_page_url, logo_url,ads_platform))
                        elif it=='Text':
                            p = multiprocessing.Process(target=process_text_ads, args=( item, company_name, advertising_goal, objective, description, ads_tone, campaign_urls, cta_list, campaign_id, campaign_name, image_text,carousel_card, it, copies, image_variations_count, landing_page_url, logo_url,ads_platform))
                        processes.append(p)
                        p.start()
                        p.join()
    
    for p in processes:
        p.join()

    return campaign_id

def edit_campaign(campaign_id, campaign_name, objective, ads_platform, description, ads_format, copies, campaign_urls, 
    company_name, advertising_goal, ad_tone, image_variations_count, landing_page_url, logo_url, image_text, carousel_card):
    
    config_yaml = load_ads_config()
    dynamo.update_campaign(campaign_id, campaign_name, objective, ads_platform, description,  company_name, advertising_goal, ad_tone)
    
    if ads_format == 'carousel':
        # Set image variations count to 1 for carousel ads
        image_variations_count = 1
    if ads_format == 'Text':
        # Set image variations count to 1 for Text
        image_variations_count = 1
    if copies and image_variations_count:
        existing_formats = dynamo.get_ads_format_for_campaign(campaign_id)
        formats_to_delete = [format for format in existing_formats if format == ads_format]
        if formats_to_delete:
            dynamo.delete_ads_by_campaign_id(campaign_id, formats_to_delete)
        processes = []
        for item in config_yaml['ads_config']:
            if (item['Platform'] == ads_platform and item['Format'] == ads_format):
                for _ in range(0, copies*image_variations_count):
                    if ads_format == 'carousel':
                        p = multiprocessing.Process(target=process_carousel_ads, args=(item, company_name, advertising_goal, objective, description, ad_tone, campaign_urls, cta_list, campaign_id, campaign_name, image_text, carousel_card, ads_format, copies, image_variations_count, landing_page_url, logo_url,ads_platform))
                    elif ads_format=='Facebook Stories':
                        p = multiprocessing.Process(target=process_facebook_stories, args=(item, company_name, advertising_goal, objective, description, ad_tone, campaign_urls, cta_list, campaign_id, campaign_name, image_text, carousel_card, ads_format, copies, image_variations_count, landing_page_url, logo_url,ads_platform))
                    elif ads_format=='NewsFeed':
                        p = multiprocessing.Process(target=process_ads, args=(item, company_name, advertising_goal, objective, description, ad_tone, campaign_urls, cta_list, campaign_id, campaign_name, image_text, carousel_card, ads_format, copies, image_variations_count, landing_page_url, logo_url,ads_platform))
                    elif ads_format=='Text': 
                        p = multiprocessing.Process(target=process_text_ads, args=(item, company_name, advertising_goal, objective, description, ad_tone, campaign_urls, cta_list, campaign_id, campaign_name, image_text, carousel_card, ads_format, copies, image_variations_count, landing_page_url, logo_url,ads_platform))
                    processes.append(p)
                    p.start()
                    p.join()
         
        for p in processes:
            p.join()



def generate_copy(company_name, advertising_goal, objective, description, ads_tone, query):
    prompt = model.resolve_copy_prompt(company_name, advertising_goal, objective, description, ads_tone, query)
    response = model.complete(prompt, 0.3)
    copy = response['choices'][0]['message']['content'].replace('"', '')
    copy = re.sub(' +', ' ', copy)
    return copy
                
def get_cta(company_name, advertising_goal, objective, description, cta_list):
    query = "Please pick up a suitable cta from the list and only return a single cta name in the output and do not add any additional text"
    prompt = model.resolve_cta_prompt(company_name, advertising_goal, objective, description, cta_list, query)
    response = model.complete(prompt, 0.0)
    cta_text = response['choices'][0]['message']['content']
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
        ads_format=item['ads_format']
        if ads_format=="NewsFeed":
            if 'headline' in data:
                new_headline = data['headline']
                creatives = json.loads(item['creatives'])
                response = model.regenerate_ad_copies(new_headline, 27)
                text  = response['choices'][0]['message']['content']
                creatives['headline'] = text
                return (json.dumps({"headline": text}), 200)
            elif 'text' in data:
                new_text = data['text']
                creatives = json.loads(item['creatives'])
                response = model.regenerate_ad_copies(new_text, 127)
                text  = response['choices'][0]['message']['content']
                creatives['text'] = text
                return (json.dumps({"text": text}), 200)
            else:
                print("regenerate image url")
        elif ads_format == 'Facebook Stories':
            if 'headline' in data:
                new_headline = data['headline']
                creatives = json.loads(item['creatives'])
                response = model.regenerate_ad_copies(new_headline, 40)
                text  = response['choices'][0]['message']['content']
                creatives['headline'] = text
                return (json.dumps({"headline": text}), 200)
            elif 'text' in data:
                new_text = data['text']
                creatives = json.loads(item['creatives'])
                response = model.regenerate_ad_copies(new_text, 125)
                text  = response['choices'][0]['message']['content']
                creatives['text'] = text
                return (json.dumps({"text": text}), 200)
            
            else:
                print("regenerate image url")
            
        elif ads_format == 'carousel':
            if 'text' in data:
                new_text = data['text']
                creatives = json.loads(item['creatives'])
                response = model.regenerate_ad_copies(new_text, 125)
                text  = response['choices'][0]['message']['content']
                creatives['text'] = text
                return (json.dumps({"text": text}), 200)
            
            elif 'headline' in data and 'index' in data:
                creatives = json.loads(item['creatives'])
                for index, card in enumerate(creatives):
                    new_headline = data['headline']
                    card_index = data['index']
                    if card_index == index:
                        response = model.regenerate_ad_copies(new_headline, 40) 
                        headline = response['choices'][0]['message']['content']
                        creatives['cards'][card_index]['headline'] = headline
                
                return (json.dumps({"headline": headline}), 200)
            
            else:
                print("regenerate image url")
        
        elif ads_format == 'Text':
            if 'headline' in data:
                new_headline = data['headline']
                creatives = json.loads(item['creatives'])
                response = model.regenerate_ad_copies(new_headline, 30)
                text  = response['choices'][0]['message']['content']
                creatives['headline'] = text
                return (json.dumps({"headline": text}), 200)
            elif 'text' in data:
                new_text = data['text']
                creatives = json.loads(item['creatives'])
                response = model.regenerate_ad_copies(new_text, 90)
                text  = response['choices'][0]['message']['content']
                creatives['text'] = text
                return (json.dumps({"text": text}), 200)
                                        
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

def regenerate_images(file, ad_id, card_index):
    temp_path = os.getenv("TEMP_PATH")
    new_file_name = file.filename.split(".")[0] + ".png"
    filename = secure_filename(new_file_name)
    path = os.path.join("/", temp_path, filename)
    file.save(path)
    square_image(path)
    url =edit_image(path)
    response = dynamo.get_ads(ad_id)
    if len(response['Items']) > 0:
        item = response['Items'][0]
        ads_format=item['ads_format']
        creatives = json.loads(item['creatives'])
        if ads_format == 'carousel':
            creatives['cards'][card_index]['image_url'] = url
        else:
            creatives['url']=url
    return url
    
def edit_image(path):
    url = model.edit_image(path)
    prefix = str(uuid.uuid4())
    object_name = prefix + ".png"
    s3_url = upload_image(object_name, url)
    return s3_url

def square_image(path):
    im = Image.open(path)
    sqrWidth = np.ceil(np.sqrt(im.size[0]*im.size[1])).astype(int)
    im_resize = im.resize((sqrWidth, sqrWidth))
    im_resize.save(path)
    
def get_user_campaigns(user_id):
    response = dynamo.fetch_user_campaigns(user_id)
    for item in response['Items']:
            ads = dynamo.get_all_campaign_ads(item['campaign_id'])
            formats = ads['Items']
            item['formats'] = formats
    sorted_items = sorted(response['Items'], key=lambda x: x.get('updated_ts', '1970-01-01 00:00:00'), reverse=True)
    return sorted_items

    

def export_ads(ad_ids, ads_format):
    TEMP_PATH = os.getenv("TEMP_PATH")
    os.makedirs(TEMP_PATH, exist_ok=True)
    if ads_format == "NewsFeed":
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
               
    elif ads_format == "carousel":
        # create csv file
        csv_path = os.path.join(TEMP_PATH, "creatives.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["text", "headline", "cta"])
            for ad_id in ad_ids:
                creatives = dynamo.get_creatives_ads(ad_id)
                creatives_dict = json.loads(creatives)
                carousel_cards = creatives_dict.get("cards")
                for card in carousel_cards:
                    writer.writerow([
                        creatives_dict["text"].replace('"', ''),
                        card["headline"].replace('"', ''),
                        card.get("cta", "").replace('"', ''),
                    ])
        # download images
        image_paths = []
        for ad_id in ad_ids:
            creatives = dynamo.get_creatives_ads(ad_id)
            creatives_dict = json.loads(creatives)
            carousel_cards = creatives_dict.get("cards")
            for i, card in enumerate(carousel_cards):
                image_url = card["image_url"]
                image_path = os.path.join(TEMP_PATH, f"{os.path.basename(image_url)}")
                urllib.request.urlretrieve(image_url, image_path)
                image_paths.append(image_path)
                
    elif ads_format == "Facebook Stories":
        # create csv file
        csv_path = os.path.join(TEMP_PATH, "creatives.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["headline", "text"])
            for ad_id in ad_ids:
                creatives = dynamo.get_creatives_ads(ad_id)
                creatives_dict = json.loads(creatives)
                writer.writerow([
                    creatives_dict["headline"].replace('"', ''),
                    creatives_dict["text"].replace('"', ''),
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

    elif ads_format == "Text":
         # create csv file
        csv_path = os.path.join(TEMP_PATH, "creatives.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["headline1", "headline2", "headline3", "description1", "description2", "cta"])
            for ad_id in ad_ids:
                creatives = dynamo.get_creatives_ads(ad_id)
                creatives_dict = json.loads(creatives)
                writer.writerow([
                    creatives_dict["headline1"].replace('"', ''),
                    creatives_dict["headline2"].replace('"', ''),
                    creatives_dict["headline3"].replace('"', ''),
                    creatives_dict["description1"].replace('"', ''),
                    creatives_dict["description2"].replace('"', ''),
                    creatives_dict.get("cta", "").replace('"', '')
                ])   
        # download images
        # image_paths = []
        # for ad_id in ad_ids:
        #     creatives = dynamo.get_creatives_ads(ad_id)
        #     creatives_dict = json.loads(creatives)
        #     image_url = creatives_dict["url"]
        #     image_path = os.path.join(TEMP_PATH, os.path.basename(image_url))
        #     urllib.request.urlretrieve(image_url, image_path)
        #     image_paths.append(image_path)
                
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
        if ads_format == "Text":
            pass
        else:
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
        ads_format=item['ads_format']
        ads_platform=item['ads_platform']
        creatives = json.loads(item['creatives'])
        if ads_format == "NewsFeed":
            new_text = data['text']
            headline = data['headline']
            new_url= data['url']
            new_cta=data['cta']
            creatives['text'] = new_text
            creatives['headline'] = headline
            creatives['url'] = new_url
            creatives['cta'] = new_cta
         
        elif ads_format == "Facebook Stories":  
            new_text = data['text']
            headline = data['headline']
            new_url= data['url']
            new_cta=data['cta']
            creatives['text'] = new_text
            creatives['headline'] = headline
            creatives['url'] = new_url
            creatives['cta'] = new_cta
            
        elif ads_format == "carousel":
            new_text = data['text']
            new_card= data['cards']
            creatives['text'] = new_text
            creatives['cards'] = new_card

        elif ads_format == "Text":
            new_headline1 = data['headline1']
            new_headline2 = data['headline2']
            new_headline3 = data['headline3']
            new_description1 = data['description1']
            new_description2 = data['description2']
            new_cta = data['cta']
            creatives['headline1'] = new_headline1
            creatives['headline2'] = new_headline2
            creatives['headline3'] = new_headline3
            creatives['description1'] = new_description1
            creatives['description2'] = new_description2
            creatives['cta'] = new_cta
          
        image_text=item.get('image_text',"")
        carousel_card=item.get('carousel_card',"")
        copies=item.get('copies',"")
        image_variations_count=item.get('image_variations_count',"")
        landing_page_url=item.get('landing_page_url',"")
        logo_url=item.get('logo_url',"")
        campaign_urls=item.get('campaign_urls',"")
        dynamo.create_ads(ad_id, campaign_id, creatives, image_text, carousel_card, ads_format, copies, image_variations_count, landing_page_url, logo_url, campaign_urls,ads_platform)
        return (json.dumps({"message": "updated successfully"}), 200)
