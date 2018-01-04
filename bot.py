import json
import logging
import requests
import requests.exceptions
import sys
from typing import List, Union, Optional

from bot_logger import create_logger
from savestate import SavedState


def create_reply_keyboard_markup(
        buttons_texts: List[List[str]],
        resize_keyboard: bool = False,
        one_time_keyboard: bool = False,
        selective: bool = False) -> str:
    markup = dict()
    markup['keyboard'] = []
    markup['selective'] = selective
    markup['resize_keyboard'] = resize_keyboard
    markup['one_time_keyboard'] = one_time_keyboard
    for button_row in buttons_texts:
        button_row2 = []
        for button_text in button_row:
            keyboard_button = {
                'text': button_text
            }
            button_row2.append(keyboard_button)
        markup['keyboard'].append(button_row2)
    return json.dumps(markup)


class ZKBBot:
    def __init__(self, token: str):
        self.token = token
        self.last_update_id = 0
        self.chats = {}
        self.chats_notify = []
        self.savestate_filename = 'saved_state.json'
        self.log = create_logger(__name__, level=logging.DEBUG, stream=sys.stdout, filename='bot.log')

    def load_state(self) -> bool:
        ss = SavedState()
        if ss.load(self.savestate_filename):
            self.chats_notify = ss.involved_chatids
            self.log.debug('Loaded save state, involved chats: {}'.format(self.chats_notify))
            return True
        self.log.debug('Could not load save state')
        return False

    def save_state(self) -> bool:
        ss = SavedState()
        ss.involved_chatids = self.chats_notify
        ok = ss.save(self.savestate_filename)
        self.log.debug('Saving state... ok={}'.format(ok))

    def tg_bot_api_call_method_get(self, method_name: str, params: dict = None) -> Optional[requests.Response]:
        url = 'https://api.telegram.org/bot{}/{}'.format(self.token, method_name)
        # self.log.debug('Requesting url: {}'.format(url))
        # headers = {
        #    'content-type', ''
        # }
        try:
            response = requests.get(url, params=params, timeout=15)
            # response.raise_for_status()
            rjson = response.json()
            if not rjson['ok']:
                self.log.error('Request "{}" error: {}'.format(method_name, rjson['description']))
                return None
            return response
        except requests.exceptions.RequestException as re:
            self.log.exception('Exception during telegram API call', exc_info=True)
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

    def send_message_text(self, chat_id: Union[str, int], text: str, parse_mode: str = 'Markdown',
                          disable_web_page_preview: bool = False, disable_notification: bool = False,
                          reply_to_message_id: int = 0, reply_markup: str = None) -> bool:
        """
        See full description: https://core.telegram.org/bots/api#sendmessage
        :param chat_id:
        :param text:
        :param parse_mode:
        :param disable_web_page_preview:
        :param disable_notification:
        :param reply_to_message_id:
        :param reply_markup:
        :return:
        """

        text_parts = []

        if len(text) > 4096:
            while len(text) > 4096:
                text_part = text[0:4096]
                text_parts.append(text_part)
                text = text[4096:]

        text_parts.append(text)

        for a_text in text_parts:
            params = {
                'chat_id': chat_id,
                'text': a_text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': disable_web_page_preview,
                'disable_notification': disable_notification
            }
            if reply_to_message_id > 0:
                params['reply_to_message_id'] = reply_to_message_id
            if reply_markup is not None:
                params['reply_markup'] = reply_markup
            r = self.tg_bot_api_call_method_get('sendMessage', params=params)
            if r is None:
                return False
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
                self.log.debug('new chat id={} type={}'.format(chat['id'], chat['type']))
                self.chats[chat['id']] = chat
            if 'text' in message:
                if message['text'].startswith('/start'):
                    text = 'Hello! You can register to receive notifications from ZKillboard using /reg ' \
                           'command, and unregister using /unreg command.'
                    reply_markup = create_reply_keyboard_markup(
                        [['/reg', '/unreg']], resize_keyboard=True)
                    self.send_message_text(chat['id'], text, 'Markdown', True, False, 0, reply_markup)
                if message['text'] == '/help':
                    text = 'ZKillboard notifications bot.\n' \
                           'Commands: \n' \
                           '/reg - Register to receive notifications\n' \
                           '/unreg - Unregister from receiving notifications\n' \
                           '/help - This help message.'
                    self.send_message_text(chat['id'], text)
                if message['text'].startswith('/reg'):
                    if chat['id'] not in self.chats_notify:
                        self.log.info('registered new chat to notify: {}'.format(chat['id']))
                        self.chats_notify.append(chat['id'])
                        self.save_state()
                if message['text'].startswith('/unreg'):
                    if chat['id'] in self.chats_notify:
                        self.log.info('unregistered chat {}'.format(chat['id']))
                        self.chats_notify.remove(chat['id'])
                        self.save_state()
            else:
                self.log.debug('Got message with no text: {}'.format(message))
