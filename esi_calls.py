import json
import os
import os.path
import requests


class ESIException(Exception):
    def __init__(self, msg: str = ''):
        self.msg = msg

    def error_string(self) -> str:
        return self.msg


def analyze_esi_response_headers(headers: dict) -> None:
    """
    Keep track of ESI headers: watch for deprecated endpoints
    and error rate limiting
    :param headers: requests's resonse headers dict
    :return:
    """
    lines_to_log = []
    if 'warning' in headers:
        lines_to_log.append('warning header: {}'.format(headers['warning']))
    if 'X-ESI-Error-Limit-Remain' in headers:
        errors_remain = int(headers['X-ESI-Error-Limit-Remain'])
        if errors_remain < 10:
            lines_to_log.append('X-ESI-Error-Limit-Remain < {} !!!'.format(errors_remain))
    if len(lines_to_log) < 1:
        return
    try:
        # auto-create logs subdir
        if not os.path.isdir('logs'):
            os.mkdir('logs')
        fn = './logs/esi-warnings.log'
        with open(fn, mode='at', encoding='utf-8') as f:
            f.writelines(lines_to_log)
    except IOError:
        pass


class ESICalls:
    def __init__(self):
        self.ESI_BASE_URL = 'https://esi.tech.ccp.is/latest'
        self.SSO_USER_AGENT = 'ESI python agent, alexey.min@gmail.com'

    def characters_names(self, ids_list: list) -> list:
        ret = []
        error_str = ''
        if len(ids_list) < 0:
            return ret
        try:
            # https://esi.tech.ccp.is/latest/#!/Character/get_characters_names
            # This route is cached for up to 3600 seconds
            url = '{}/characters/names/'.format(self.ESI_BASE_URL)
            ids_str = ''
            for an_id in set(ids_list):
                if len(ids_str) > 0:
                    ids_str += ','
                ids_str += str(an_id)
            r = requests.get(url,
                             params={'character_ids': ids_str},
                             headers={
                                 'Content-Type': 'application/json',
                                 'Accept': 'application/json',
                                 'User-Agent': self.SSO_USER_AGENT
                             },
                             timeout=20)
            response_text = r.text
            if r.status_code == 200:
                ret = json.loads(response_text)
                analyze_esi_response_headers(r.headers)
            else:
                obj = json.loads(response_text)
                if 'error' in obj:
                    error_str = 'ESI error: {}'.format(obj['error'])
                else:
                    error_str = 'Error connecting to ESI server: HTTP status {}'.format(r.status_code)
        except requests.exceptions.RequestException as e:
            error_str = 'Error connection to ESI server: {}'.format(str(e))
        except json.JSONDecodeError:
            error_str = 'Failed to parse response JSON from CCP ESI server!'
        if error_str != '':
            raise ESIException(error_str)
        return ret

    def corporations_names(self, ids_list: list) -> list:
        ret = []
        error_str = ''
        if len(ids_list) < 0:
            return ret
        try:
            # https://esi.tech.ccp.is/latest/#!/Corporation/get_corporations_names
            # This route is cached for up to 3600 seconds
            url = '{}/corporations/names/'.format(self.ESI_BASE_URL)
            ids_str = ''
            for an_id in set(ids_list):
                if len(ids_str) > 0:
                    ids_str += ','
                ids_str += str(an_id)
            r = requests.get(url,
                             params={'corporation_ids': ids_str},
                             headers={
                                 'Content-Type': 'application/json',
                                 'Accept': 'application/json',
                                 'User-Agent': self.SSO_USER_AGENT
                             },
                             timeout=20)
            response_text = r.text
            if r.status_code == 200:
                ret = json.loads(response_text)
                analyze_esi_response_headers(r.headers)
            else:
                obj = json.loads(response_text)
                if 'error' in obj:
                    error_str = 'ESI error: {}'.format(obj['error'])
                else:
                    error_str = 'Error connecting to ESI server: HTTP status {}'.format(r.status_code)
        except requests.exceptions.RequestException as e:
            error_str = 'Error connection to ESI server: {}'.format(str(e))
        except json.JSONDecodeError:
            error_str = 'Failed to parse response JSON from CCP ESI server!'
        if error_str != '':
            raise ESIException(error_str)
        return ret

    def alliances_names(self, ids_list: list) -> list:
        ret = []
        error_str = ''
        if len(ids_list) < 0:
            return ret
        try:
            # https://esi.tech.ccp.is/latest/#!/Alliance/get_alliances_names
            # This route is cached for up to 3600 seconds
            url = '{}/alliances/names/'.format(self.ESI_BASE_URL)
            ids_str = ''
            for an_id in set(ids_list):
                if len(ids_str) > 0:
                    ids_str += ','
                ids_str += str(an_id)
            r = requests.get(url,
                             params={'alliance_ids': ids_str},
                             headers={
                                 'Content-Type': 'application/json',
                                 'Accept': 'application/json',
                                 'User-Agent': self.SSO_USER_AGENT
                             },
                             timeout=20)
            response_text = r.text
            if r.status_code == 200:
                ret = json.loads(response_text)
            else:
                obj = json.loads(response_text)
                if 'error' in obj:
                    error_str = 'ESI error: {}'.format(obj['error'])
                else:
                    error_str = 'Error connecting to ESI server: HTTP status {}'.format(r.status_code)
        except requests.exceptions.RequestException as e:
            error_str = 'Error connection to ESI server: {}'.format(str(e))
        except json.JSONDecodeError:
            error_str = 'Failed to parse response JSON from CCP ESI server!'
        if error_str != '':
            raise ESIException(error_str)
        return ret
