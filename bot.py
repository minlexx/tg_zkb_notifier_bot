import requests
import requests.exceptions
import sys


class ZKBBot:
    def __init__(self, token: str):
        self.token = token
        self.last_update_id = 0
        self.chats = {}
        self.chats_notify = []

    def tg_bot_api_call_method_get(self, method_name: str, params: dict = None) -> requests.Response:
        url = 'https://api.telegram.org/bot{}/{}'.format(self.token, method_name)
        print('Requesting url: {}'.format(url))
        # headers = {
        #    'content-type', ''
        # }
        try:
            response = requests.get(url, params=params, timeout=15)
            # response.raise_for_status()
            rjson = response.json()
            if not rjson['ok']:
                print('Request "{}" error: {}'.format(method_name, rjson['description']), file=sys.stderr)
                return None
            return response
        except requests.exceptions.RequestException as re:
            print(str(re))
        return None

    def get_updates(self, last_update_id: int = -1) -> list:
        ret = []
        r = self.tg_bot_api_call_method_get('getUpdates', params={
            'timeout': 5,
            'offset': last_update_id + 1
        })
        if r is None:
            return ret
        reply = r.json()
        ret = reply['result']
        return ret

    def send_message_text(self, chat_id: [str or int], text: str, parse_mode: str = 'Markdown',
                          disable_web_page_preview: bool = False, disable_notification: bool = False,
                          reply_to_message_id: int = 0) -> bool:
        """
        See full description: https://core.telegram.org/bots/api#sendmessage
        :param chat_id:
        :param text:
        :param parse_mode:
        :param disable_web_page_preview:
        :param disable_notification:
        :param reply_to_message_id:
        :return:
        """
        params = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': disable_web_page_preview,
            'disable_notification': disable_notification
        }
        if reply_to_message_id > 0:
            params['reply_to_message_id'] = reply_to_message_id
        r = self.tg_bot_api_call_method_get('sendMessage', params=params)
        return True

    def handle_message(self, message: dict) -> None:
        # 'message': {
        #     'chat': {'id': 137769336, 'first_name': 'Alexey', 'last_name': 'Minnekhanov',
        #             'type': 'private', 'username': 'minlexx'},
        #     'message_id': 2, 'date': 1514457525,
        #     'from': {'id': 137769336, 'first_name': 'Alexey', 'last_name': 'Minnekhanov',
        #             'username': 'minlexx', 'is_bot': False, 'language_code': 'en'},
        #     'text': 'еее'
        # }
        if 'chat' in message:
            chat = message['chat']
            if chat['id'] not in self.chats:
                print('Bot: handle_message: new chat id={} type={}'.format(chat['id'], chat['type']))
                self.chats[chat['id']] = chat
            if message['text'] == '/start':
                if chat['id'] not in self.chats_notify:
                    self.chats_notify.append(chat['id'])
            if message['text'] == '/stop':
                self.chats_notify.remove(chat['id'])
