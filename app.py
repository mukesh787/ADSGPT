from flask_bcrypt import Bcrypt
from flask import json, Flask, request
from flask_cors import CORS, cross_origin
import logging
import dynamo
from campaign import create_campaign, get_campaign_ads, update_ads, upload_files, regenerate_images, export_ad

app = Flask(__name__)
bcrypt = Bcrypt(app)
CORS(app)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
        
@app.route("/adsgpt/signup", methods=['POST'])
def signup():
    data = request.get_json()
    user_name = data['username']
    email = data['email']
    password = data['password']
    pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    dynamo.save_user(user_name, email, pw_hash)
    return (json.dumps({'success': 'succes'}), 200)

@app.route("/adsgpt/login", methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']
    items = dynamo.get_user(email)
    if len(items) > 0:
        item = items[0]
        pw_hash = item['password']
        is_valid = bcrypt.check_password_hash(pw_hash, password)
        if is_valid:
            return (json.dumps({'success': 'success'}), 200)
        else:
            return (json.dumps({'message': 'Invalid password'}), 400)
        
    return (json.dumps({'message': 'Invalid password'}), 400)


@app.route("/adsgpt/campaign", methods=['POST'])
def campaign():
    data = request.get_json()
    objective = data['objective']
    description = data['description']
    ads_platform = data['ads_platform']
    ads_format = data['ads_format']
    copies = data['copies']
    campaign_name = data['campaign_name']
    urls = data['urls']
    campaign_id = create_campaign(objective, description, ads_platform, ads_format, copies, campaign_name, urls)
    return (json.dumps({"campaign_id": campaign_id}), 200)


@app.route("/adsgpt/campaign/images", methods=['POST'])
def update_campaign():
    files = request.files.getlist("file")
    urls = upload_files(files)
    return (json.dumps({"urls": urls}), 200)
    

@app.route("/adsgpt/campaign/ads", methods=['GET'])
def ads():
    request_args = request.args
    if request_args and 'campaign_id' in request_args:
        campaign_id = request_args['campaign_id']
    creatives = get_campaign_ads(campaign_id)
    return (json.dumps({"message": creatives}), 200)


@app.route("/adsgpt/update/ads", methods=['POST'])
def regenerate_ads():
    data = request.get_json()
    ad_id = data.get('ad_id', '')
    return update_ads(ad_id, data)

@app.route("/adsgpt/regenerate/image", methods=['POST'])
def regenerate_image():
    file = request.files['file']
    data = dict(request.form)
    ad_id = data.get('ad_id')
    url =  regenerate_images(file, ad_id)
    return (json.dumps({"url": url}), 200)

@app.route("/adsgpt/export/zip", methods=['POST'])
def export():
    request_args = request.args
    if request_args and 'ad_id' in request_args:
       ad_id = request_args['ad_id']
    url=export_ad(ad_id)
    return (json.dumps({"Success": url}), 200)
    
    

if __name__ == "__main__":
  app.run(host='0.0.0.0', port=8888, debug=True)
  
  
  
