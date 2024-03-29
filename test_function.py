import json
import os
import re
import urllib3
from urllib.parse import unquote_plus

http = urllib3.PoolManager()
webhook_url = os.environ['webhookURL']
slack_bot_token = os.environ['SLACK_BOT_TOKEN']

def lambda_handler(event, context):
    # まず、eventオブジェクト内に 'body' キーが存在するかどうかを確認します。
    if 'body' not in event:
        # 'body' キーが存在しない場合は、エラーをログに記録します。
        print("[ERROR] No 'body' in event")
        return {'statusCode': 400, 'body': json.dumps({'error': "Bad Request"})}
    
    print(event) #ログ確認のためevent出力
    
    # 'body' キーが存在する場合、その内容をデコードします。
    # SlackからのペイロードはURLエンコードされている可能性があるため、unquote_plusを使用してデコードします。
    body = unquote_plus(event['body'])
    
    # ペイロードがbase64エンコードされている場合があるので、必要に応じてデコードします。
    if event.get('isBase64Encoded', False):
        body = base64.b64decode(body).decode('utf-8')
    
    # デコードしたペイロードをJSONオブジェクトに変換します。
    slack_event = json.loads(body)

    # ここにSlackイベントに応じた処理を記述します。
    # 例えば、メッセージイベントを処理する場合は、以下のようにします。
    if slack_event.get('type') == 'event_callback':
        # Slackイベントから 'text' フィールドを抽出
        message_text = slack_event['event']['text']
        
        # メッセージから 'mailto:' を含む部分を抽出
        email_addresses = re.findall(r'mailto:([^\s|]*)', message_text)
        if email_addresses:
            # 抽出したメールアドレスをSlackメッセージとして送信
            send_slack_message(slack_bot_token, webhook_url, "#team-nw開発lab", 
                               f"抽出されたメールアドレス: {', '.join(email_addresses)}")
        
        # 他のSlackイベントタイプに対する処理があれば、ここに記述します。
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Request processed successfully'})
    }

def send_slack_message(token, url, channel, text):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    message = {
        'channel': channel,
        'text': text
    }
    response = http.request('POST', url, body=json.dumps(message), headers=headers)
    print({
        "message": "Message sent to Slack",
        "status_code": response.status,
        "response": response.data.decode('utf-8')
    })