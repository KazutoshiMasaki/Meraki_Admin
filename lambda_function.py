import json
import os
import re
import time
import logging
from meraki import DashboardAPI

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 環境変数から設定を読み込む
meraki_api_key = os.environ['MERAKI_API_KEY']
slack_bot_token = os.environ['SLACK_BOT_TOKEN']
organization_id = os.environ['MERAKI_ORGANIZATION_ID']
slack_channel_id = os.environ['SLACK_CHANNEL_ID']
last_run_timestamp = os.environ.get('LAST_RUN_TIMESTAMP', '0')

# Meraki API クライアントの初期化
dashboard = DashboardAPI(meraki_api_key)

def get_admin_id_by_email(email):
    logger.info(f"Fetching admin ID for email: {email}")
    admins = dashboard.organizations.getOrganizationAdmins(organization_id)
    
    for admin in admins:
        if admin['email'] == email:
            logger.info(f"Found admin ID: {admin['id']} for email: {email}")
            return admin['id']
    
    logger.warning(f"No admin found with email: {email}")
    return None

def update_meraki_admin_permission(admin_id, permission):
    logger.info(f"Updating permission for admin ID: {admin_id} to {permission}")
    try:
        response = dashboard.organizations.updateOrganizationAdmin(
            organization_id, admin_id, 
            orgAccess=permission
        )
        logger.info(f"Successfully updated admin ID: {admin_id}, Response: {response}")
        return True
    except Exception as e:
        logger.error(f"Failed to update admin ID: {admin_id}, Error: {str(e)}")
        return False

def post_message_to_slack(message):
    logger.info(f"Posting message to Slack: {message}")
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
    success = response.status == 200
    if success:
        logger.info("Successfully posted message to Slack")
    else:
        logger.error(f"Failed to post message to Slack, Response: {data}")
    return success

def lambda_handler(event, context):
    global last_run_timestamp
    
    current_timestamp = time.time()
    
    # 直近の実行から60秒以内の場合、重複実行を防ぐ
    if current_timestamp - float(last_run_timestamp) < 60:
        logger.warning("Duplicate event detected, skipping execution.")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Duplicate event detected, skipping execution.'})
        }
    
    # 環境変数に現在のタイムスタンプを保存
    os.environ['LAST_RUN_TIMESTAMP'] = str(current_timestamp)

    # Slackからのイベントをパース
    body = json.loads(event['body'])
    event_text = body['event']['text']
    
    logger.info(f"Received event: {event_text}")
    
    # 正規表現を使ってメールアドレスと権限を抽出
    email_match = re.search(r"<mailto:([^|]+)\|[^>]+>", event_text)
    permission_match = re.search(r"\*権限\*([^\*]+)", event_text)
    
    # 抽出結果をログに出力
    if email_match:
        logger.info(f"Extracted email: {email_match.group(1).strip()}")
    else:
        logger.error("Failed to extract email from event text.")
    
    if permission_match:
        logger.info(f"Extracted permission: {permission_match.group(1).strip()}")
    else:
        logger.error("Failed to extract permission from event text.")

    if email_match and permission_match:
        email = email_match.group(1).strip()  # 前後の空白を取り除く
        permission = permission_match.group(1).strip()  # 前後の空白を取り除く

        logger.info(f"Extracted email: {email} and permission: {permission}")

        # Meraki APIを使用してAdmin IDを取得
        admin_id = get_admin_id_by_email(email)
        if not admin_id:
            logger.error(f"No admin found with email: {email}")
            return {
                'statusCode': 400,
                'body': json.dumps({'message': f'No admin found with email: {email}'})
            }

        # Meraki APIを使用してAdmin権限を変更
        if update_meraki_admin_permission(admin_id, permission):
            message = f"{email}の権限を変更しました。 権限： {permission}."
        else:
            message = "Failed to update admin permission."
        
        # Slackにメッセージを投稿
        post_message_to_slack(message)

        # 応答メッセージを返す
        return {
            'statusCode': 200,
            'body': json.dumps({'message': message})
        }
    else:
        logger.error("Failed to parse email or permission from Slack event.")
        # 名前や権限が見つからなかった場合のエラーメッセージ
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Failed to parse email or permission from Slack event(エラーなので確認してね)'})
        }
