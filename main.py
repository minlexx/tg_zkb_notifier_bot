import configparser


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


def main():
    cfg = load_config()
    if cfg['token'] == '':
        raise ValueError('Cannot function without a token!')
    print('Read token: {}'.format(cfg['token']))


if __name__ == '__main__':
    main()
