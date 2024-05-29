import http.client
import json
import logging
import os
import re

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 環境変数から設定を読み込む
meraki_api_key = os.environ["MERAKI_API_KEY"]
slack_bot_token = os.environ["SLACK_BOT_TOKEN"]
organization_id = os.environ["MERAKI_ORGANIZATION_ID"]
slack_channel_id = os.environ["SLACK_CHANNEL_ID"]
last_processed_event_ts = os.environ.get("LAST_PROCESSED_EVENT_TS", "")


def get_admin_info_by_email(email):
    conn = http.client.HTTPSConnection("api.meraki.com")
    headers = {
        "X-Cisco-Meraki-API-Key": meraki_api_key,
        "Content-Type": "application/json",
    }
    conn.request(
        "GET",
        f"/api/v1/organizations/{organization_id}/admins",
        headers=headers,
    )
    response = conn.getresponse()
    data = response.read()
    admins = json.loads(data)
    conn.close()

    for admin in admins:
        if admin["email"] == email:
            return admin

    return None


def update_meraki_admin_permission(admin_info, permission):
    admin_id = admin_info["id"]
    name = admin_info["name"]
    conn = http.client.HTTPSConnection("api.meraki.com")
    url = f"/api/v1/organizations/{organization_id}/admins/{admin_id}"
    payload = json.dumps({"name": name, "orgAccess": permission})
    headers = {
        "X-Cisco-Meraki-API-Key": meraki_api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    conn.request("PUT", url, body=payload, headers=headers)
    response = conn.getresponse()
    data = response.read().decode("utf-8")
    conn.close()

    success = response.status == 200
    if success:
        logger.info(f"Successfully updated admin ID: {admin_id}")
    else:
        logger.error(
            f"Failed to update admin ID: {admin_id}, Response: {data}"
        )
    return success


def post_message_to_slack(message):
    try:
        conn = http.client.HTTPSConnection("slack.com")
        url = "/api/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {slack_bot_token}",
            "Content-Type": "application/json",
        }
        payload = json.dumps({"channel": slack_channel_id, "text": message})
        conn.request("POST", url, body=payload, headers=headers)
        response = conn.getresponse()
        data = response.read().decode("utf-8")
        conn.close()
        if response.status == 200:
            logger.info("Successfully posted message to Slack")
            return True
        else:
            logger.error(f"Failed to post message to Slack, Response: {data}")
            logger.error(f"Response Status: {response.status}")
    except Exception as e:
        logger.error(f"Exception occurred while posting to Slack: {str(e)}")
    return False


def lambda_handler(event, context):
    global last_processed_event_ts
    body = json.loads(event["body"])
    event_ts = body.get("event", {}).get("event_ts", "")

    if not event_ts:
        logger.error("No event_ts found in the event payload")
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"message": "No event_ts found in the event payload"}
            ),
        }

    # イベントタイムスタンプの重複チェック
    if event_ts == last_processed_event_ts:
        logger.warning(
            f"Duplicate event detected: {event_ts}, skipping execution."
        )
        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": "Duplicate event detected, skipping execution."}
            ),
        }
    os.environ["LAST_PROCESSED_EVENT_TS"] = event_ts
    last_processed_event_ts = event_ts

    logger.info(f"Processing event TS: {event_ts}")

    # Slackからのイベントをパース
    event_text = body["event"]["text"]

    # 正規表現を使ってメールアドレスと権限を抽出
    email_match = re.search(r"<mailto:([^|]+)\|[^>]+>", event_text)
    permission_match = re.search(r"\*権限\*([^\*]+)", event_text)

    if email_match and permission_match:
        email = email_match.group(1).strip()  # 前後の空白を取り除く
        permission = permission_match.group(1).strip()  # 前後の空白を取り除く

        # Meraki APIを使用してAdmin情報を取得
        admin_info = get_admin_info_by_email(email)
        if not admin_info:
            logger.error(f"No admin found with email: {email}")
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"message": f"No admin found with email: {email}"}
                ),
            }

        # Meraki APIを使用してAdmin権限を変更
        if update_meraki_admin_permission(admin_info, permission):
            message = f"{email}の権限を変更しました。 権限： {permission}."
        else:
            message = "Failed to update admin permission."

        # Slackにメッセージを投稿
        if not post_message_to_slack(message):
            logger.error(
                "Failed to notify Slack after updating admin permission."
            )
            message = "Failed to update admin permission and notify Slack."

        # 応答メッセージを返す
        return {"statusCode": 200, "body": json.dumps({"message": message})}
    else:
        logger.error("Failed to parse email or permission from Slack event.")
        # 名前や権限が見つからなかった場合のエラーメッセージ
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "message": "Failed to parse email or permission from Slack event(エラーなので確認してね)"
                }
            ),
        }
