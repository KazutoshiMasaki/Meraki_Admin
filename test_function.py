import urllib3
import json
import os
http = urllib3.PoolManager()

webhookURL = os.environ['webhookURL']

def lambda_handler(event, context):
    url = "https://hooks.slack.com/services/" + webhookURL
    msg = {
        "channel": "#team-nw開発lab",
        "username": "Meraki_Admin権限依頼",
        "text": "Hello From Lambda",
        "icon_emoji": ""
    }

    encoded_msg = json.dumps(msg).encode('utf-8')
    resp = http.request('POST', url, body=encoded_msg)
    print({
        "message": "Hello From Lambda", 
        "status_code": resp.status, 
        "response": resp.data
    })