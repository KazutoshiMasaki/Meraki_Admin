import json
import os
import requests

# 環境変数から設定を読み込む
meraki_api_key = os.environ['MERAKI_API_KEY']
slack_bot_token = os.environ['SLACK_BOT_TOKEN']
organization_id = os.environ['MERAKI_ORGANIZATION_ID']
slack_channel_id = os.environ['SLACK_CHANNEL_ID']

def update_meraki_admin_permission(admin_id, name, permission):
    url = f"https://api.meraki.com/api/v1/organizations/{organization_id}/admins/{admin_id}"
    headers = {
        'X-Cisco-Meraki-API-Key': meraki_api_key,
        'Content-Type': 'application/json'
    }
    payload = {
        'name': name,
        'orgAccess': permission  # 例: 'full', 'read-only', 'none' など
    }
    response = requests.put(url, headers=headers, json=payload)
    return response.status_code == 200

def post_message_to_slack(message):
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        'Authorization': f'Bearer {slack_bot_token}',
        'Content-Type': 'application/json'
    }
    payload = {
        'channel': slack_channel_id,
        'text': message
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.status_code == 200

def lambda_handler(event, context):
    # Slackからのイベントをパース
    body = json.loads(event['body'])
    admin_id = body['admin_id']  # Slackワークフローから送信される想定の管理者ID
    name = body['name']  # Slackワークフローから送信される想定の名前
    permission = body['permission']  # Slackワークフローから送信される想定の権限
    
    # Meraki APIを使用してAdmin権限を変更
    if update_meraki_admin_permission(admin_id, name, permission):
        message = f"Admin {name}'s permission updated to {permission}."
        post_message_to_slack(message)
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Permission update successful'})
        }
    else:
        message = f"Failed to update Admin {name}'s permission."
        post_message_to_slack(message)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Permission update failed'})
        }