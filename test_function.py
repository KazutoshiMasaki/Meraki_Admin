import os
import json
import urllib3

# 環境変数からトークンを取得
SLACK_BOT_TOKEN = os.environ['SLACK_BOT_TOKEN']
http = urllib3.PoolManager()

def lambda_handler(event, context):
    # Slackからのイベントをパース
    slack_event = json.loads(event['body'])

    # トップレベルのタイプで処理を分岐
    if slack_event.get('type') == 'url_verification':  # チャレンジ応答
        return {
            'statusCode': 200,
            'body': json.dumps({
                'challenge': slack_event['challenge']
            })
        }

    # モーダルを開くためのリクエスト
    if slack_event['event']['type'] == 'app_mention':  # または 'message' と slack_event['event']['text'] の特定のキーワード
        trigger_id = slack_event['event']['trigger_id']
        open_modal(trigger_id)
        return {'statusCode': 200}

    # ユーザーがモーダルで情報を送信したときのイベント
    if slack_event['event']['type'] == 'view_submission':
        user_id = slack_event['event']['user']['id']
        # Block IDとAction IDに基づいて値を取得します。
        user_input = slack_event['event']['view']['state']['values']['input_block']['input']['value']
        channel_id = slack_event['event']['view']['private_metadata']
        send_message_to_channel(channel_id, user_id, user_input)
        return {'statusCode': 200}

    return {'statusCode': 200, 'body': 'Event received'}

def open_modal(trigger_id):
   # モーダルを構築するためのJSONペイロード
   modal_view = {
       "type": "modal",
       "title": {
           "type": "plain_text",
           "text": "Meraki Access Request"
       },
       "blocks": [
           {
               "type":"input",
               "block_id": "input_block",
               "element": {
                   "type": "plain_text_input",
                   "action_id": "input",
                   "placeholder": {
                       "type": "plain_text",
                       "text": "Enter the name"
                   }
               },
               "label": {
                   "type": "plain_text",
                   "text": "対象者名"
               }
           }
       ],
       "submit": {
           "type": "plain_text",
           "text": "Submit"
       }
   }
   # モーダルを開くためのリクエストを送信
   headers = {
       'Authorization': f'Bearer {SLACK_BOT_TOKEN}',
       'Content-Type': 'application/json'
   }
   response = http.request(
       'POST',
       'https://slack.com/api/views.open',
       body=json.dumps({"trigger_id": trigger_id, "view": modal_view}).encode('utf-8'),
       headers=headers
   )
   print({'status_code': response.status, 'response': response.data})
def send_message_to_channel(channel_id, user_id, user_input):
   # メッセージを構築
   message = {
       "channel": channel_id,
       "text": f"対象者：<@{user_id}>さんがMeraki権限をリクエストしました。対象者は {user_input} です。"
   }
   # チャンネルにメッセージを送信
   headers = {
       'Authorization': f'Bearer {SLACK_BOT_TOKEN}',
       'Content-Type': 'application/json'
   }
   response = http.request(
       'POST',
       'https://slack.com/api/chat.postMessage',
       body=json.dumps(message).encode('utf-8'),
       headers=headers
   )
   print({'status_code': response.status, 'response': response.data})