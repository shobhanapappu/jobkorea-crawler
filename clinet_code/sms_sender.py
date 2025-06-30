"""SENS SMS 발송 모듈"""

import time
import uuid
import hmac
import hashlib
import base64
import json
import requests
import configparser
from urllib.parse import urlparse


def _make_signature(timestamp: str, access_key: str, secret_key: str, method: str, url: str) -> str:
    parsed = urlparse(url)
    uri = parsed.path
    message = f"{method} {uri}\n{timestamp}\n{access_key}"
    signing_key = bytes(secret_key, "utf-8")
    message = bytes(message, "utf-8")
    hmac_hash = hmac.new(signing_key, message, hashlib.sha256).digest()
    return base64.b64encode(hmac_hash).decode()


def send_sms(to_number: str, content: str, cfg: configparser.ConfigParser) -> bool:
    """SENS를 통해 SMS를 발송합니다.
    
    Args:
        to_number: 수신번호 (이미 테스트 모드 처리가 완료된 번호)
        content: 메시지 내용
        cfg: 설정 객체
        
    Returns:
        bool: 발송 성공 여부
    """
    sens_cfg = cfg["sens"]
    access_key = sens_cfg.get("access_key")
    secret_key = sens_cfg.get("secret_key")
    service_id = sens_cfg.get("service_id")
    sender = sens_cfg.get("sender")

    # 테스트 모드 처리는 이미 호출하는 곳에서 완료됨

    api_url = f"https://sens.apigw.ntruss.com/sms/v2/services/{service_id}/messages"

    timestamp = str(int(time.time() * 1000))
    signature = _make_signature(timestamp, access_key, secret_key, "POST", f"/sms/v2/services/{service_id}/messages")

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "x-ncp-apigw-timestamp": timestamp,
        "x-ncp-iam-access-key": access_key,
        "x-ncp-apigw-signature-v2": signature,
    }

    body = {
        "type": "SMS",
        "contentType": "COMM",
        "countryCode": "82",
        "from": sender,
        "content": content,
        "messages": [
            {"to": to_number, "content": content}
        ],
    }

    try:
        print(f"[DEBUG] SMS API URL: {api_url}")
        print(f"[DEBUG] Headers: {headers}")
        print(f"[DEBUG] Body: {json.dumps(body, ensure_ascii=False, indent=2)}")
        
        resp = requests.post(api_url, headers=headers, data=json.dumps(body))
        print(f"[DEBUG] Response Status: {resp.status_code}")
        print(f"[DEBUG] Response Text: {resp.text}")
        
        if resp.status_code == 202:
            return True
        print("SMS send failed:", resp.status_code, resp.text)
    except Exception as e:
        print("SMS send exception:", e)
    return False
