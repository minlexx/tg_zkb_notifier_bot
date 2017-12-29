import datetime
import json
import requests


class ZKB:
    def __init__(self, options: dict=None):
        self.HOURS = 3600
        self.DAYS = 24 * self.HOURS
        self._BASE_URL_ZKB = 'https://zkillboard.com/api/'
        self._headers = dict()
        self._headers['accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        self._headers['accept-encoding'] = 'gzip, deflate'
        self._headers['user-agent'] = 'Python/ZKB agent'
        self._url = ''
        self._modifiers = ''
        self._cache = None
        self._debug = False
        self.request_count = 0
        self.max_requests = 0
        self.clear_url()
        # parse options
        if options:
            if 'debug' in options:
                self._debug = options['debug']
            if 'user_agent' in options:
                self._headers['user-agent'] = options['user_agent']

    def clear_url(self):
        self._url = self._BASE_URL_ZKB
        self._modifiers = ''

    def add_modifier(self, mname, mvalue=None):
        self._url += mname
        self._url += '/'
        self._modifiers += mname
        self._modifiers += '_'
        if mvalue:
            self._url += str(mvalue)
            self._url += '/'
            self._modifiers += str(mvalue)
            self._modifiers += '_'

    # startTime and endTime is datetime timestamps, in the format YmdHi..
    #  Example 2012-11-25 19:00 is written as 201211251900
    def add_startTime(self, st=datetime.datetime.now()):
        self.add_modifier('startTime', st.strftime('%Y%m%d%H%M'))

    # startTime and endTime is datetime timestamps, in the format YmdHi..
    #  Example 2012-11-25 19:00 is written as 201211251900
    def add_endTime(self, et=datetime.datetime.now()):
        self.add_modifier('endTime', et.strftime('%Y%m%d%H%M'))

    #  pastSeconds returns only kills that have happened in the past x seconds.
    #  pastSeconds can maximum go up to 7 days (604800 seconds)
    def add_pastSeconds(self, s):
        self.add_modifier('pastSeconds', s)

    def add_year(self, y):
        self.add_modifier('year', y)

    def add_month(self, m):
        self.add_modifier('month', m)

    def add_week(self, w):
        self.add_modifier('week', w)

    # If the /limit/ modifier is used, then /page/ is unavailable.
    def add_limit(self, limit):
        self.add_modifier('limit', str(limit))

    # Page reqs over 10 are only allowed for characterID, corporationID and allianceID
    def add_page(self, page):
        self.add_modifier('page', page)

    def add_beforeKillID(self, killID):
        self.add_modifier('beforeKillID', killID)

    def add_afterKillID(self, killID):
        self.add_modifier('afterKillID', killID)

    # To get combined /kills/ and /losses/, don't pass either /kills/ or /losses/
    def add_kills(self):
        self.add_modifier('kills')

    # To get combined /kills/ and /losses/, don't pass either /kills/ or /losses/
    def add_losses(self):
        self.add_modifier('losses')

    #  /w-space/ and /solo/ can be combined with /kills/ and /losses/
    def add_wspace(self):
        self.add_modifier('w-space')

    #  /w-space/ and /solo/ can be combined with /kills/ and /losses/
    def add_solo(self):
        self.add_modifier('solo')

    # If you do not paass /killID/ then you must pass at least two
    #  of the following modifiers. /w-space/, /solo/ or any of the /xID/ ones.
    #  (characterID, allianceID, factionID etc.)
    def add_killID(self, killID):
        self.add_modifier('killID', killID)

    def add_orderAsc(self):
        self.add_modifier('orderDirection', 'asc')

    def add_orderDesc(self):
        self.add_modifier('orderDirection', 'desc')

    def add_noItems(self):
        self.add_modifier('no-items')

    def add_noAttackers(self):
        self.add_modifier('no-attackers')

    def add_character(self, charID):
        self.add_modifier('characterID', charID)

    def add_corporation(self, corpID):
        self.add_modifier('corporationID', corpID)

    def add_alliance(self, allyID):
        self.add_modifier('allianceID', allyID)

    def add_faction(self, factionID):
        self.add_modifier('factionID', factionID)

    def add_shipType(self, shipTypeID):
        self.add_modifier('shipTypeID', shipTypeID)

    def add_group(self, groupID):
        self.add_modifier('groupID', groupID)

    def add_solarSystem(self, solarSystemID):
        self.add_modifier('solarSystemID', solarSystemID)

    # Default cache lifetime set to 1 hour (3600 seconds)
    def go(self):
        zkb_kills = []
        ret = ''
        # first, try to get from cache
        if self._cache:
            ret = self._cache.get_json(self._modifiers)
        if (ret is None) or (ret == ''):
            # either no cache exists or cache read error :( send request
            try:
                if self._debug:
                    print('ZKB: Sending request! {0}'.format(self._url))
                r = requests.get(self._url, headers=self._headers)
                if r.status_code == 200:
                    ret = r.text
                    if 'x-bin-request-count' in r.headers:
                        self.request_count = int(r.headers['x-bin-request-count'])
                    if 'x-bin-max-requests' in r.headers:
                        self.max_requests = int(r.headers['x-bin-max-requests'])
                    if self._debug:
                        print('ZKB: We are making {0} requests of {1} allowed per hour.'.
                              format(self.request_count, self.max_requests))
                elif r.status_code == 403:
                    # If you get an error 403, look at the Retry-After header.
                    retry_after = r.headers['retry-after']
                    if self._debug:
                        print('ZKB: ERROR: we got 403, retry-after: {0}'.format(retry_after))
                else:
                    if self._debug:
                        print('ZKB: ERROR: HTTP response code: {0}'.format(r.status_code))
            except requests.exceptions.RequestException as e:
                if self._debug:
                    print(str(e))
            # request done, see if we have a response
            if ret != '':
                if self._cache:
                    self._cache.save_json(self._modifiers, ret)
        # parse response JSON, if we have one
        if (ret is not None) and (ret != ''):
            try:
                zkb_kills = json.loads(ret)
            except ValueError:
                # skip JSON parse errors
                pass
            utcnow = datetime.datetime.utcnow()
            try:
                for a_kill in zkb_kills:
                    # fix new keys format to old format, becuase templates use old keys
                    a_kill['killID'] = a_kill['killmail_id']
                    # init a kill datetime with an empty date
                    a_kill['kill_dt'] = datetime.datetime.fromtimestamp(0)
                    a_kill['killTime'] = a_kill['killmail_time']  # compatibility with old API
                    # guess time format, ZKB has changed it over time
                    # ValueError: time data '2015.07.08 01:11:00' does not match format '%Y-%m-%d %H:%M:%S'
                    # current ZKB has a totallly different time format: "2017-06-07T17:02:57Z"
                    try:
                        a_kill['kill_dt'] = datetime.datetime.strptime(a_kill['killmail_time'], '%Y-%m-%dT%H:%M:%SZ')
                    except ValueError:
                        # some older formats
                        try:
                            a_kill['kill_dt'] = datetime.datetime.strptime(a_kill['killmail_time'], '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            a_kill['kill_dt'] = datetime.datetime.strptime(a_kill['killmail_time'], '%Y.%m.%d %H:%M:%S')
                    # now calculate how long ago it happened
                    delta = utcnow - a_kill['kill_dt']
                    a_kill['days_ago'] = delta.days
                    # convert to integers (zkillboard sends strings) and also initialize all keys used by templates
                    a_kill['victim']['characterID'] = 0
                    a_kill['victim']['characterName'] = ''
                    a_kill['victim']['corporationID'] = 0
                    a_kill['victim']['corporationName'] = ''
                    a_kill['victim']['allianceID'] = 0
                    a_kill['victim']['allianceName'] = ''
                    a_kill['victim']['shipTypeID'] = 0
                    a_kill['victim']['shipTypeName'] = ''
                    # fix character_id => characterID
                    if 'character_id' in a_kill['victim']:
                        a_kill['victim']['characterID'] = int(a_kill['victim']['character_id'])
                    # fix alliance_id => allianceID
                    if 'alliance_id' in a_kill['victim']:
                        a_kill['victim']['allianceID'] = int(a_kill['victim']['alliance_id'])
                    # fix corporation_id => corporationID
                    if 'corporation_id' in a_kill['victim']:
                        a_kill['victim']['corporationID'] = int(a_kill['victim']['corporation_id'])
                    # fix ship_type_id => shipTypeID
                    if 'ship_type_id' in a_kill['victim']:
                        a_kill['victim']['shipTypeID'] = int(a_kill['victim']['ship_type_id'])
                        a_kill['victim']['shipTypeName'] = ''
                    # process attackers
                    for atk in a_kill['attackers']:
                        atk['characterID'] = 0
                        atk['characterName'] = ''
                        atk['corporationID'] = 0
                        atk['corporationName'] = ''
                        atk['allianceID'] = 0
                        atk['allianceName'] = ''
                        atk['shipTypeID'] = 0
                        atk['shipTypeName'] = ''
                        atk['finalBlow'] = atk['final_blow']
                        atk['factionID'] = 0
                        atk['factionName'] = ''
                        if 'character_id' in atk:
                            atk['characterID'] = atk['character_id']
                        if 'alliance_id' in atk:
                            atk['allianceID'] = atk['alliance_id']
                        if 'corporation_id' in atk:
                            atk['corporationID'] = atk['corporation_id']
                        if 'ship_type_id' in atk:
                            atk['shipTypeID'] = atk['ship_type_id']
                        if 'faction_id' in atk:
                            # this is an NPC kill
                            atk['factionID'] = atk['faction_id']
                            # NPC is not a character, zero out char name/id
                            atk['characterID'] = 0
                            atk['characterName'] = ''
                    finalBlow_attacker = dict()
                    for atk in a_kill['attackers']:
                        if atk['final_blow'] == True:
                            finalBlow_attacker = atk
                    a_kill['finalBlowAttacker'] = finalBlow_attacker
                    # fix solar system id
                    a_kill['solarSystemID'] = a_kill['solar_system_id']
                    a_kill['solarSystemName'] = ''
                    # kill price in ISK
                    if 'zkb' in a_kill:
                        if 'totalValue' in a_kill['zkb']:
                            a_kill['zkb']['totalValueM'] = round(float(a_kill['zkb']['totalValue']) / 1000000.0)
            except KeyError as k_e:
                if self._debug:
                    print('It is possible that ZKB API has chabged (again).')
                    print(str(k_e))
        return zkb_kills
