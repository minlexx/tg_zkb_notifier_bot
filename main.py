import configparser
import requests
import requests.exceptions
import sys
import time


def load_config() -> dict:
    ret = {
        'token': ''
    }
    ini = configparser.ConfigParser()
    ini.read(['token.ini'], 'utf-8')
    if ini.has_section('auth'):
        if 'token' in ini['auth']:
            ret['token'] = ini['auth']['token']
    return ret


def tg_bot_api_call_method_get(token: str, method_name: str, params: dict = None) -> requests.Response:
    url = 'https://api.telegram.org/bot{}/{}'.format(token, method_name)
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


def get_updates(token: str, last_update_id: int = -1) -> list:
    ret = []
    r = tg_bot_api_call_method_get(token, 'getUpdates', params=
        {
            'timeout': 5,
            'offset': last_update_id + 1
        })
    if r is None:
        return ret
    reply = r.json()
    ret = reply['result']
    return ret


def main():
    cfg = load_config()
    if cfg['token'] == '':
        raise ValueError('Cannot function without a token!')
    token = cfg['token']

    last_update_id = 0
    should_stop = False

    while not should_stop:
        updates_list = get_updates(token, last_update_id)
        i = 0
        for update in updates_list:
            i += 1
            print('Update {}: {}'.format(i, str(update)))
            update_id = update['update_id']
            if update_id > last_update_id:
                last_update_id = update_id
                print('    new last_update_id = {}'.format(last_update_id))

        time.sleep(5)


if __name__ == '__main__':
    main()


# [{
#   'update_id': 683048427,
#   'message': {
#     'chat': {'id': 137769336, 'first_name': 'Alexey', 'last_name': 'Minnekhanov',
#             'type': 'private', 'username': 'minlexx'},
#     'message_id': 2, 'date': 1514457525,
#     'from': {'id': 137769336, 'first_name': 'Alexey', 'last_name': 'Minnekhanov',
#             'username': 'minlexx', 'is_bot': False, 'language_code': 'en'},
#     'text': 'еее'
#   }
# }]
