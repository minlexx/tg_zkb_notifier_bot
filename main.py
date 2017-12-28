import configparser
import time

from zkillboard import ZKB
from bot import ZKBBot


def load_config() -> dict:
    ret = {
        'token': '',
        'corp_id': 0
    }
    ini = configparser.ConfigParser()
    ini.read(['bot.ini'], 'utf-8')
    if ini.has_section('auth'):
        if 'token' in ini['auth']:
            ret['token'] = ini['auth']['token']
    if ini.has_section('zkb'):
        if 'corp_id' in ini['zkb']:
            ret['corp_id'] = int(ini['zkb']['corp_id'])
    return ret


def main():
    cfg = load_config()
    if cfg['token'] == '':
        raise ValueError('Cannot function without a token! Check ini file.')
    if cfg['corp_id'] == 0:
        raise ValueError('Cannot function without a corp_id given! Check ini file.')

    token = cfg['token']
    corp_id = cfg['corp_id']

    should_stop = False
    displayed_killids = []
    zkb = ZKB({'debug': True})
    bot = ZKBBot(token)

    # get initial ZKB kills
    zkb.clear_url()
    zkb.add_corporation(corp_id)
    zkb.add_limit(10)
    kills = zkb.go()
    ##for kill in kills:
    #    displayed_killids.append(kill['killmail_id'])

    print(kills)

    try:
        while not should_stop:
            updates_list = bot.get_updates(bot.last_update_id)
            i = 0
            for update in updates_list:
                i += 1
                print('Update {}: {}'.format(i, str(update)))
                update_id = update['update_id']
                if update_id > bot.last_update_id:
                    bot.last_update_id = update_id
                    print('    new last_update_id = {}'.format(bot.last_update_id))
                # place to process updates (messages)
                if 'message' in update:
                    bot.handle_message(update['message'])

            # get next ZKB kills
            zkb.clear_url()
            zkb.add_corporation(corp_id)
            zkb.add_limit(10)
            kills = zkb.go()
            kills_to_process = []
            for kill in kills:
                if kill['killmail_id'] not in displayed_killids:
                    kills_to_process.append(kill)

            print('{} new kill(s) to show.'.format(len(kills_to_process)))
            for kill in kills_to_process:
                for chat_id in bot.chats_notify:
                    text = 'Kill: https://zkillboard.com/kill/{}/ at {}.'.format(
                        kill['killmail_id'], kill['killmail_time'])
                    bot.send_message_text(chat_id, text)
                    time.sleep(1)
                    displayed_killids.append(kill['killmail_id'])

            time.sleep(5)

    # exit on Ctrl+C
    except KeyboardInterrupt:
        print('Exiting by user request.')


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
