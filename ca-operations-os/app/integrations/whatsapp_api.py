import requests


class WhatsAppService:
    def __init__(self, api_url, token):
        self.api_url = api_url
        self.token = token

    def send_message(self, mobile, message):
        payload = {
            "mobile": mobile,
            "message": message
        }

        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        response = requests.post(
            self.api_url,
            json=payload,
            headers=headers
        )

        return {
            "status_code": response.status_code,
            "response": response.text
        }
