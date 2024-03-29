import urllib3
import json
import os

# urllib3を使う場合は証明書の警告を無視する設定を追加することも一般的です
# urllib3.disable_warnings()

http = urllib3.PoolManager()
webhook_url = os.environ['webhookURL']

def lambda_handler(event, context):
    # リクエストがチャレンジリクエストかどうかを確認
    if 'challenge' in event:
        return {
            'statusCode': 200,
            'body': json.dumps({
                'challenge': event.get('challenge')
            })
        }
    # チャレンジリクエストではない場合は、Slackにメッセージを送信
    msg = {
        "channel": "#team-nw開発lab",
        "username": "Meraki_Admin権限依頼",
        "text": "これはテストメッセージです",
        "icon_emoji": ":robot_face:"
    }
    encoded_msg = json.dumps(msg).encode('utf-8')
    resp = http.request('POST', webhook_url, body=encoded_msg)
    print({
        "message": "これはログに行くやつです",
        "status_code": resp.status,
        "response": resp.data
    })
    
    print(event)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Message sent to Slack'})
    }