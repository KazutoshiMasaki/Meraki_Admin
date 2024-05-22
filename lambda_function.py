import json
import os
import http.client
import re  # 正規表現モジュールをインポート

# 環境変数から設定を読み込む
meraki_api_key = os.environ['MERAKI_API_KEY']
slack_bot_token = os.environ['SLACK_BOT_TOKEN']
organization_id = os.environ['MERAKI_ORGANIZATION_ID']
admin_id = os.environ['MERAKI_ADMIN_ID']
slack_channel_id = os.environ['SLACK_CHANNEL_ID']

def update_meraki_admin_permission(name, permission):
    conn = http.client.HTTPSConnection("api.meraki.com")
    headers = {
        'X-Cisco-Meraki-API-Key': meraki_api_key,
        'Content-Type': 'application/json'
    }
    payload = json.dumps({
        'name': name,
        'orgAccess': permission
    })
    conn.request("PUT", f"/api/v1/organizations/{organization_id}/admins/{admin_id}", payload, headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return response.status == 200

def post_message_to_slack(message):
    conn = http.client.HTTPSConnection("slack.com")
    headers = {
        'Authorization': f'Bearer {slack_bot_token}',
        'Content-Type': 'application/json'
    }
    payload = json.dumps({
        'channel': slack_channel_id,
        'text': message
    })
    conn.request("POST", "/api/chat.postMessage", payload, headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return response.status == 200

def lambda_handler(event, context):
    # Slackからのイベントをパース
    body = json.loads(event['body'])
    event_text = body['event']['text']
    
    # 正規表現を使って名前と権限を抽出
    name_match = re.search(r"\*名前\*([^\*]+)", event_text)
    permission_match = re.search(r"\*権限\*([^\*]+)", event_text)
    
    if name_match and permission_match:
        name = name_match.group(1).strip()  # 前後の空白を取り除く
        permission = permission_match.group(1).strip()  # 前後の空白を取り除く

    # Meraki APIを使用してAdmin権限を変更
    if update_meraki_admin_permission(name, permission):
        message = f" {name}の権限を変更しました。 権限： {permission}."
    else:
        # 名前や権限が見つからなかった場合のエラーメッセージ
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Failed to parse name or permission from Slack event(エラーなので確認してね)'})
        }

    # Slackにメッセージを投稿
    post_message_to_slack(message)

    # 応答メッセージを返す
    return {
        'statusCode': 200 if message.startswith("Admin") else 500,
        'body': json.dumps({'message': message})
    }