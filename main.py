import configparser
import time

from zkillboard import ZKB
from bot import ZKBBot


def load_config() -> dict:
    ret = {
        'token': '',
        'corp_id': 0,
        'refresh_interval_secs': 300
    }
    ini = configparser.ConfigParser()
    ini.read(['bot.ini'], 'utf-8')
    if ini.has_section('auth'):
        if 'token' in ini['auth']:
            ret['token'] = ini['auth']['token']
    if ini.has_section('zkb'):
        if 'corp_id' in ini['zkb']:
            ret['corp_id'] = int(ini['zkb']['corp_id'])
        if 'refresh_interval_secs' in ini['zkb']:
            ret['refresh_interval_secs'] = int(ini['zkb']['refresh_interval_secs'])
    return ret


def main():
    cfg = load_config()
    if cfg['token'] == '':
        raise ValueError('Cannot function without a token! Check ini file.')
    if cfg['corp_id'] == 0:
        raise ValueError('Cannot function without a corp_id given! Check ini file.')

    token = cfg['token']
    corp_id = cfg['corp_id']
    zkb_refresh_interval_secs = cfg['refresh_interval_secs']
    # safety check
    if zkb_refresh_interval_secs < 15:
        zkb_refresh_interval_secs = 15  # wait at least 15 seconds between requests to ZKB...

    should_stop = False
    displayed_killids = []
    last_zkb_refresh_time = int(time.time())

    zkb = ZKB({'debug': True})
    bot = ZKBBot(token)

    # get initial ZKB kills
    zkb.clear_url()
    zkb.add_corporation(corp_id)
    zkb.add_limit(10)
    kills = zkb.go()
    for kill in kills:
        displayed_killids.append(kill['killmail_id'])
    print('Loaded and ignored {} initial kills.'.format(len(kills)))

    # Main loop
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

            cur_time = int(time.time())
            # get next ZKB kills
            if cur_time - last_zkb_refresh_time > zkb_refresh_interval_secs:
                last_zkb_refresh_time = cur_time
                # restart request
                zkb.clear_url()
                # zkb.add_corporation(corp_id)
                zkb.add_wspace()
                zkb.add_limit(10)
                kills = zkb.go()
                # filter only kills that were not posted yet
                kills_to_process = []
                for kill in kills:
                    if kill['killmail_id'] not in displayed_killids:
                        kills_to_process.append(kill)

                print('{} new kill(s) to show.'.format(len(kills_to_process)))

                # collect all new kills to a single long text message to avoid spam
                full_text = ''
                for kill in kills_to_process:
                    text = 'Kill: https://zkillboard.com/kill/{}/ at {}.'.format(
                        kill['killmail_id'], kill['killmail_time'])
                    if len(full_text) > 0:
                        full_text += '\n\n'
                    full_text += text
                    displayed_killids.append(kill['killmail_id'])

                # patiently send full text to all involved chats
                if len(full_text) > 0:
                    for chat_id in bot.chats_notify:
                        bot.send_message_text(chat_id, full_text, 'Markdown', True)
                        time.sleep(1)

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
