python
import json
import os
import requests

# 環境変数からAPIキーを取得
MERAKI_API_KEY = os.environ['MERAKI_API_KEY']
SLACK_BOT_TOKEN = os.environ['SLACK_BOT_TOKEN']

# Meraki APIのベースURL
MERAKI_BASE_URL = 'https://api.meraki.com/api/v1'

# SlackのポストメッセージAPIエンドポイント
SLACK_POST_MESSAGE_URL = 'https://slack.com/api/chat.postMessage'

def lambda_handler(event, context):
    # Slackのイベントを解析する
    slack_event = json.loads(event['body'])
    
    # 仮にオーガニゼーションIDと権限レベルを固定で設定しています。
    # 本番環境では、これらの値を動的に扱う必要があります。
    organization_id = 'your-organization-id'
    admin_id = slack_event['user_id']
    desired_privilege = slack_event['text']  # "full" または "readonly"

    # Meraki APIを呼び出して権限を変更する
    meraki_response = change_meraki_privilege(organization_id, admin_id, desired_privilege)
    
    # Slackに通知を送る
    slack_response = post_to_slack(slack_event['channel'], meraki_response)
    
    return {
        'statusCode': 200,
        'body': json.dumps(slack_response)
    }

def change_meraki_privilege(organization_id, admin_id, privilege):
    # MerakiのAPIエンドポイントに対してPUTリクエストを実行する
    url = f'{MERAKI_BASE_URL}/organizations/{organization_id}/admins/{admin_id}'
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }
    # Meraki APIによっては、権限レベルを設定するための正確なデータ構造が異なる場合があるため、
    # 公式のAPIドキュメントを確認して適切なデータ構造を用いる必要があります。
    data = {
        'orgAccess': privilege
    }
    response = requests.put(url, headers=headers, json=data)
    return response.json()

def post_to_slack(channel, message):
    # Slack APIを使用してメッセージをチャンネルに送信する
    headers = {
        'Authorization': f'Bearer {SLACK_BOT_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'channel': channel,
        'text': f'Meraki privilege change response: {message}'
    }
    response = requests.post(SLACK_POST_MESSAGE_URL, headers=headers, json=data)
    return response.json()

# Lambda関数をローカルでテストするためのコード
if __name__ == "__main__":
    fake_event = {
        'body': json.dumps({
            'user_id': 'example_admin_id',
            'channel': 'channel_id',
            'text': 'full'  # 権限変更の例
        })
    }
    result = lambda_handler(fake_event, None)
    print(result)