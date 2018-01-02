import configparser
import datetime
import time

from zkillboard import ZKB
from bot import ZKBBot
from eve_names_resolver import EveNamesDb

DEBUG = False
MODE = 'all'


def load_config() -> dict:
    ret = {
        'token': '',
        'mode': 'all',
        'corp_id': 0,
        'refresh_interval_secs': 300,
        'debug': False
    }
    ini = configparser.ConfigParser()
    ini.read(['bot.ini'], 'utf-8')
    if ini.has_section('auth'):
        if 'token' in ini['auth']:
            ret['token'] = ini['auth']['token']
    if ini.has_section('zkb'):
        if 'mode' in ini['zkb']:
            ret['mode'] = ini['zkb']['mode']
        if 'corp_id' in ini['zkb']:
            ret['corp_id'] = int(ini['zkb']['corp_id'])
        if 'refresh_interval_secs' in ini['zkb']:
            ret['refresh_interval_secs'] = int(ini['zkb']['refresh_interval_secs'])
        if 'debug' in ini['zkb']:
            ret['debug'] = ini.getboolean('zkb', 'debug')
    return ret


def zkb_get_kills(zkb: ZKB, corp_id: int) -> list:
    global MODE
    zkb.clear_url()
    if MODE == 'all':
        zkb.add_limit(50)
    elif MODE == 'w-space':
        zkb.add_wspace()
        zkb.add_limit(30)
    elif MODE == 'corp':
        zkb.add_corporation(corp_id)
        zkb.add_limit(20)
    else:
        raise ValueError('Mode should be one of: all, w-space, corp. Check ini file.')
    return zkb.go()


def format_isk_value(value: float) -> str:
    if value > 1000000000:
        return str(round(value / 1000000000)) + ' Bil'
    if value > 1000000:
        return str(round(value / 1000000)) + ' Mil'
    if value > 1000:
        return str(round(value / 1000)) + ' K'
    return str(value)


def main():
    global DEBUG, MODE
    cfg = load_config()
    if cfg['token'] == '':
        raise ValueError('Cannot function without a token! Check ini file.')
    if cfg['mode'] not in ['all', 'w-space', 'corp']:
        raise ValueError('Mode should be one of: all, w-space, corp. Check ini file.')
    if cfg['mode'] == 'corp':
        if cfg['corp_id'] == 0:
            raise ValueError('Cannot function without a corp_id given! Check ini file.')

    token = cfg['token']
    MODE = cfg['mode']
    corp_id = cfg['corp_id']
    zkb_refresh_interval_secs = cfg['refresh_interval_secs']
    DEBUG = cfg['debug']
    # safety check
    if zkb_refresh_interval_secs < 15:
        zkb_refresh_interval_secs = 15  # wait at least 15 seconds between requests to ZKB...

    should_stop = False
    displayed_killids = []
    last_zkb_refresh_time = int(time.time())

    zkb = ZKB({'debug': DEBUG})
    bot = ZKBBot(token)
    bot.load_state()

    eve_names = EveNamesDb('eve_names.db')

    # get initial ZKB kills
    kills = zkb_get_kills(zkb, corp_id)
    for kill in kills:
        displayed_killids.append(kill['killmail_id'])
    print('Loaded and ignored {} initial kills.'.format(len(kills)))

    # remind all saved chats that they are registered
    if len(bot.chats_notify) > 0:
        for chatid in bot.chats_notify:
            text = 'Bot started. You are registered to receive notifications, ' \
                   'type /unreg to cancel.'
            bot.send_message_text(chatid, text)
            time.sleep(1)

    # Main loop
    try:
        while not should_stop:
            updates_list = bot.get_updates(bot.last_update_id)
            i = 0
            for update in updates_list:
                i += 1
                update_id = update['update_id']
                if update_id > bot.last_update_id:
                    bot.last_update_id = update_id
                # place to process updates (messages)
                if 'message' in update:
                    bot.handle_message(update['message'])

            cur_time = int(time.time())
            # get next ZKB kills
            if cur_time - last_zkb_refresh_time > zkb_refresh_interval_secs:
                last_zkb_refresh_time = cur_time
                # send request
                kills = zkb_get_kills(zkb, corp_id)
                # filter only kills that were not posted yet
                kills_to_process = []
                for kill in kills:
                    if kill['killmail_id'] not in displayed_killids:
                        kills_to_process.append(kill)

                print('{} new kill(s) to show.'.format(len(kills_to_process)))

                kills_to_process = eve_names.fill_names_in_zkb_kills(kills_to_process)

                # collect all new kills to a single long text message to avoid spam
                full_text = ''
                for kill in kills_to_process:
                    text = ''
                    text += '*{}* '.format(kill['victim']['characterName'])
                    if kill['victim']['allianceName'] != '':
                        text += '({} / {})'.format(
                            kill['victim']['corporationName'], kill['victim']['allianceName'])
                    else:
                        text += '({})'.format(kill['victim']['corporationName'])
                    text += ' lost a *{}*'.format(kill['victim']['shipTypeName'])
                    text += ' to *{}* attacker(s) in *{}*'.format(
                        len(kill['attackers']), kill['solarSystemName'])
                    # kill time
                    killtime_full = kill['kill_dt'].strftime('%Y-%m-%d %H:%M:%S')
                    killtime_time = kill['kill_dt'].strftime('%H:%M:%S')
                    days_ago = kill['days_ago']
                    if days_ago == 0:
                        text += ' today at {}.'.format(killtime_time)
                    elif days_ago == 1:
                        text += ' yesterday at {}.'.format(killtime_time)
                    else:
                        text += ' at {}.'.format(killtime_full)
                    text += '\n'
                    text += 'Value: *{}* ISK. '.format(format_isk_value(kill['zkb']['totalValue']))
                    text += 'https://zkillboard.com/kill/{}/'.format(kill['killmail_id'])
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

    bot.save_state()


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
