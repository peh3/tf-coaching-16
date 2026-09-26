import json
import boto3
import os
import random
import string
import time
from datetime import datetime, timezone

ddb = boto3.resource('dynamodb', region_name=os.environ.get('REGION_AWS', 'us-east-1'))
table = ddb.Table(os.environ.get('DB_NAME'))

def generate_short_id(min_c, max_c):
    length = random.randint(int(min_c), int(max_c))
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def lambda_handler(event, context):
    body = event.get('body')
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except Exception:
            body = {}
    elif not isinstance(body, dict):
        body = {}

    # Check both 'url' and 'long_url' in the body, plus queryStringParameters as fallback
    long_url = (
        body.get('url') or 
        body.get('long_url') or 
        (event.get('queryStringParameters') or {}).get('url') or
        (event.get('queryStringParameters') or {}).get('long_url')
    )

    if not long_url:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Missing 'url' or 'long_url' in request payload."})
        }

    short_id = generate_short_id(os.environ.get('MIN_CHAR', 12), os.environ.get('MAX_CHAR', 16))
    app_url = os.environ.get('APP_URL', '')
    short_url = f"{app_url}{short_id}"

    # Calculate TTL (7 days)
    now_epoch = int(time.time())
    ttl = now_epoch + (7 * 24 * 60 * 60)

    # Store in DynamoDB
    table.put_item(
        Item={
            'short_id': short_id,
            'long_url': str(long_url),
            'short_url': short_url,
            'hits': 0,
            'ttl': ttl,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'analytics': {
                'source_ip': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown'),
                'user_agent': event.get('requestContext', {}).get('identity', {}).get('userAgent', 'unknown'),
                'xray_trace_id': event.get('headers', {}).get('X-Amzn-Trace-Id', 'unknown')
            }
        }
    )

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "short_url": short_url,
            "short_id": short_id
        })
    }