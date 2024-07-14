import boto3
from botocore.client import Config
from flask import Flask, render_template, request
import logging
from collections import defaultdict
import re
import concurrent.futures

app = Flask(__name__)

# Configuration for generic S3-compatible storage
ACCESS_KEY = 'accesskey'
SECRET_KEY = 'secret-key'
ENDPOINT_URL = 'yours3compatibleendpoint'

# Initialize S3 client
s3 = boto3.client('s3',
                  aws_access_key_id=ACCESS_KEY,
                  aws_secret_access_key=SECRET_KEY,
                  endpoint_url=ENDPOINT_URL,
                  config=Config(signature_version='s3v4'))

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_buckets():
    try:
        response = s3.list_buckets()
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        return buckets
    except Exception as e:
        logger.error(f"Error retrieving bucket list: {e}", exc_info=True)
        return []

def generate_presigned_url(bucket_name, key):
    try:
        return s3.generate_presigned_url('get_object',
                                         Params={'Bucket': bucket_name, 'Key': key},
                                         ExpiresIn=3600)  # URL expires in 1 hour
    except Exception as e:
        logger.error(f"Error generating presigned URL for {key}: {e}", exc_info=True)
        return None

def list_all_objects(bucket_name):
    """Lists all objects in an S3 bucket using pagination to handle large lists efficiently."""
    objects = []
    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name)
    for page in page_iterator:
        if 'Contents' in page:
            objects.extend(page['Contents'])
    return objects

def get_image_urls(bucket_name, year=None, month=None):
    try:
        logger.info(f"Listing objects in bucket: {bucket_name}")
        # List all objects using pagination
        objects = list_all_objects(bucket_name)
        
        if not objects:
            logger.warning("No contents found in bucket.")
            return []

        image_urls = defaultdict(list)
        keys = [obj['Key'] for obj in objects]

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            future_to_key = {executor.submit(generate_presigned_url, bucket_name, key): key for key in keys}
            for future in concurrent.futures.as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    image_url = future.result()
                    if image_url:
                        # Generate a presigned URL for the thumbnail
                        thumb_key = f"thumbs/{key}"
                        thumb_url = generate_presigned_url(bucket_name, thumb_key)
                        
                        # Determine if the file is a video or an image
                        if key.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                            media_type = 'image'
                        elif key.endswith(('.mp4', '.mov', '.avi')):
                            media_type = 'video'
                        else:
                            continue

                        # Extract year and month from filename
                        match = re.match(r'(\d{4})(\d{2})(\d{2})_', key)
                        if match:
                            file_year, file_month, file_day = match.groups()
                            if (year is None or file_year == year) and (month is None or file_month == month):
                                date = f"{file_year}-{file_month}-{file_day}"
                                image_urls[date].append({'url': image_url, 'thumb': thumb_url, 'type': media_type})
                        else:
                            image_urls['Unknown'].append({'url': image_url, 'thumb': thumb_url, 'type': media_type})

                except Exception as e:
                    logger.error(f"Error processing key {key}: {e}", exc_info=True)
        
        return dict(sorted(image_urls.items()))  # Sort by date
    except Exception as e:
        logger.error(f"Error retrieving images from bucket: {e}", exc_info=True)
        return defaultdict(list)

@app.route('/', methods=['GET', 'POST'])
def index():
    images = defaultdict(list)
    bucket_name = None
    year = None
    month = None
    buckets = get_buckets()
    if request.method == 'POST':
        bucket_name = request.form['bucket_name']
        year = request.form.get('year')
        month = request.form.get('month')
        images = get_image_urls(bucket_name, year, month)
    return render_template('index.html', images=images, bucket_name=bucket_name, buckets=buckets, year=year, month=month)

if __name__ == '__main__':
    app.run(debug=True)

