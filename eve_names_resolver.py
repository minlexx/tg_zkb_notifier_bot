import sqlite3
import threading

from esi_calls import ESICalls, ESIException


class EsiNamesResolver:
    def __init__(self):
        self.error_str = ''
        self.esi_calls = ESICalls()

    def resolve_characters_names(self, ids_list: list) -> list:
        ret = []
        try:
            ret = self.esi_calls.characters_names(ids_list)
        except ESIException as ex:
            self.error_str = ex.error_string()
        return ret

    def resolve_corporations_names(self, ids_list: list) -> list:
        ret = []
        try:
            ret = self.esi_calls.corporations_names(ids_list)
        except ESIException as ex:
            self.error_str = ex.error_string()
        return ret

    def resolve_alliances_names(self, ids_list: list) -> list:
        ret = []
        try:
            ret = self.esi_calls.alliances_names(ids_list)
        except ESIException as ex:
            self.error_str = ex.error_string()
        return ret

    def resolve_solarsystem_name(self, ssid: int) -> str:
        ret = ''
        try:
            reply = self.esi_calls.get_universe_solarsystem(ssid)
            if 'name' in reply:
                ret = reply['name']
            # sec_status = reply['security_status']
        except ESIException as ex:
            self.error_str = ex.error_string()
        return ret

    def resolve_type_name(self, typeid: int) -> str:
        ret = ''
        try:
            reply = self.esi_calls.get_universe_type(typeid)
            if 'name' in reply:
                ret = reply['name']
        except ESIException as ex:
            self.error_str = ex.error_string()
        return ret


class EveNamesDb:
    def __init__(self, names_db_filename: str):
        self.names_db_filename = names_db_filename
        self._conn = sqlite3.connect(self.names_db_filename, check_same_thread=False)
        self._write_lock = threading.Lock()
        self._resolver = EsiNamesResolver()
        self.check_tables()

    def check_tables(self):
        """
        Automatically create needed tables if not exist
        :return: None
        """
        self._write_lock.acquire()
        existing_tables = []
        cur = self._conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for row in cur:
            existing_tables.append(row[0])
        cur.close()
        if 'charnames' not in existing_tables:
            cur = self._conn.cursor()
            cur.execute('CREATE TABLE charnames (id INTEGER PRIMARY KEY NOT NULL, name TEXT)')
            self._conn.commit()
            cur.close()
        if 'corpnames' not in existing_tables:
            cur = self._conn.cursor()
            cur.execute('CREATE TABLE corpnames (id INTEGER PRIMARY KEY NOT NULL, name TEXT)')
            self._conn.commit()
            cur.close()
        if 'allynames' not in existing_tables:
            cur = self._conn.cursor()
            cur.execute('CREATE TABLE allynames (id INTEGER PRIMARY KEY NOT NULL, name TEXT)')
            self._conn.commit()
            cur.close()
        if 'solarsystems' not in existing_tables:
            cur = self._conn.cursor()
            cur.execute('CREATE TABLE solarsystems (id INTEGER PRIMARY KEY NOT NULL, name TEXT)')
            self._conn.commit()
            cur.close()
        if 'types' not in existing_tables:
            cur = self._conn.cursor()
            cur.execute('CREATE TABLE types (id INTEGER PRIMARY KEY NOT NULL, name TEXT)')
            self._conn.commit()
            cur.close()
        self._write_lock.release()

    def get_char_name(self, iid: int) -> str:
        if iid <= 0:
            return ''
        cur = self._conn.cursor()
        cur.execute('SELECT name FROM charnames WHERE id = ?', (iid,))
        row = cur.fetchone()
        cur.close()
        if row is not None:
            return row[0]
        return ''

    def get_corp_name(self, iid: int) -> str:
        if iid <= 0:
            return ''
        cur = self._conn.cursor()
        cur.execute('SELECT name FROM corpnames WHERE id = ?', (iid,))
        row = cur.fetchone()
        cur.close()
        if row is not None:
            return row[0]
        return ''

    def get_ally_name(self, iid: int) -> str:
        if iid <= 0:
            return ''
        cur = self._conn.cursor()
        cur.execute('SELECT name FROM allynames WHERE id = ?', (iid,))
        row = cur.fetchone()
        cur.close()
        if row is not None:
            return row[0]
        return ''

    def get_solarsystem_name(self, iid: int) -> str:
        if iid <= 0:
            return ''
        cur = self._conn.cursor()
        cur.execute('SELECT name FROM solarsystems WHERE id = ?', (iid,))
        row = cur.fetchone()
        cur.close()
        if row is not None:
            return row[0]
        return ''

    def get_type_name(self, iid: int) -> str:
        if iid <= 0:
            return ''
        cur = self._conn.cursor()
        cur.execute('SELECT name FROM types WHERE id = ?', (iid,))
        row = cur.fetchone()
        cur.close()
        if row is not None:
            return row[0]
        return ''

    def set_char_name(self, iid: int, name: str) -> None:
        if iid <= 0:
            return
        self._write_lock.acquire()
        cur = self._conn.cursor()
        cur.execute('INSERT OR REPLACE INTO charnames (id, name) VALUES (?, ?)', (iid, name))
        self._conn.commit()
        cur.close()
        self._write_lock.release()

    def set_corp_name(self, iid: int, name: str) -> None:
        if iid <= 0:
            return
        self._write_lock.acquire()
        cur = self._conn.cursor()
        cur.execute('INSERT OR REPLACE INTO corpnames (id, name) VALUES (?, ?)', (iid, name))
        self._conn.commit()
        cur.close()
        self._write_lock.release()

    def set_ally_name(self, iid: int, name: str) -> None:
        if iid <= 0:
            return
        self._write_lock.acquire()
        cur = self._conn.cursor()
        cur.execute('INSERT OR REPLACE INTO allynames (id, name) VALUES (?, ?)', (iid, name))
        self._conn.commit()
        cur.close()
        self._write_lock.release()

    def set_solarsystem_name(self, iid: int, name: str) -> None:
        if iid <= 0:
            return
        self._write_lock.acquire()
        cur = self._conn.cursor()
        cur.execute('INSERT OR REPLACE INTO solarsystems (id, name) VALUES (?, ?)', (iid, name))
        self._conn.commit()
        cur.close()
        self._write_lock.release()

    def set_type_name(self, iid: int, name: str) -> None:
        if iid <= 0:
            return
        self._write_lock.acquire()
        cur = self._conn.cursor()
        cur.execute('INSERT OR REPLACE INTO types (id, name) VALUES (?, ?)', (iid, name))
        self._conn.commit()
        cur.close()
        self._write_lock.release()

    def fill_names_in_zkb_kills(self, kills: list) -> list:
        # 1. collect unknown IDs
        unknown_charids = []
        unknown_corpids = []
        unknown_allyids = []
        unknown_ssids = []
        unknown_typeids = []
        for kill in kills:
            if 'character_id' in kill['victim']:
                char_id = int(kill['victim']['character_id'])
                char_name = self.get_char_name(char_id)
                if (char_name == '') and (char_id > 0):  # add to unknowns
                    unknown_charids.append(char_id)
            if 'corporation_id' in kill['victim']:
                corp_id = int(kill['victim']['corporation_id'])
                corp_name = self.get_corp_name(corp_id)
                if (corp_name == '') and (corp_id >= 0):
                    unknown_corpids.append(corp_id)
            if 'alliance_id' in kill['victim']:
                ally_id = int(kill['victim']['alliance_id'])
                ally_name = self.get_ally_name(ally_id)
                if (ally_name == '') and (ally_id >= 0):
                    unknown_allyids.append(ally_id)
            if 'solar_system_id' in kill:
                ssid = int(kill['solar_system_id'])
                ssname = self.get_solarsystem_name(ssid)
                if (ssid > 0) and (ssname == ''):
                    unknown_ssids.append(ssid)
            if 'ship_type_id' in kill['victim']:
                typeid = int(kill['victim']['ship_type_id'])
                typename = self.get_type_name(typeid)
                if (typeid > 0) and (typename == ''):
                    unknown_typeids.append(typeid)
            for atk in kill['attackers']:
                if 'character_id' in atk:
                    char_id = int(atk['character_id'])
                    char_name = self.get_char_name(char_id)
                    if (char_name == '') and (char_id >= 0):
                        unknown_charids.append(char_id)
                if 'corporation_id' in atk:
                    corp_id = int(atk['corporation_id'])
                    corp_name = self.get_corp_name(corp_id)
                    if (corp_name == '') and (corp_id >= 0):
                        unknown_corpids.append(corp_id)
                if 'alliance_id' in atk:
                    ally_id = int(atk['alliance_id'])
                    ally_name = self.get_ally_name(ally_id)
                    if (ally_name == '') and (ally_id >= 0):
                        unknown_allyids.append(ally_id)

        # 2. issue a single request to get all names at once
        names = self._resolver.resolve_characters_names(unknown_charids)
        for obj in names:
            self.set_char_name(obj['character_id'], obj['character_name'])
        names = self._resolver.resolve_corporations_names(unknown_corpids)
        for obj in names:
            self.set_corp_name(obj['corporation_id'], obj['corporation_name'])
        names = self._resolver.resolve_alliances_names(unknown_allyids)
        for obj in names:
            self.set_ally_name(obj['alliance_id'], obj['alliance_name'])
        # 2.1 issue several requests, each for every solarsystem
        for ssid in unknown_ssids:
            ssname = self._resolver.resolve_solarsystem_name(ssid)
            if ssname != '':
                self.set_solarsystem_name(ssid, ssname)
        # 2.2 issue several requests, each for every typeid
        for typeid in unknown_typeids:
            typename = self._resolver.resolve_type_name(typeid)
            if typename != '':
                self.set_type_name(typeid, typename)

        # 3. fill in gathered information
        for kill in kills:
            if 'solar_system_id' in kill:
                ssname = self.get_solarsystem_name(kill['solar_system_id'])
                if ssname != '':
                    kill['solarSystemName'] = ssname
            victim = kill['victim']
            if 'character_id' in victim:
                char_id = int(victim['character_id'])
                if char_id > 0:
                    char_name = self.get_char_name(char_id)
                    if char_name != '':
                        victim['characterName'] = char_name
            if 'corporation_id' in victim:
                corp_id = int(victim['corporation_id'])
                if corp_id > 0:
                    corp_name = self.get_corp_name(corp_id)
                    if corp_name != '':
                        victim['corporationName'] = corp_name
            if 'alliance_id' in victim:
                ally_id = int(victim['alliance_id'])
                if ally_id > 0:
                    ally_name = self.get_ally_name(ally_id)
                    if ally_name != '':
                        victim['allianceName'] = ally_name
            if 'ship_type_id' in victim:
                ship_typeid = int(victim['ship_type_id'])
                if ship_typeid > 0:
                    ship_typename = self.get_type_name(ship_typeid)
                    if ship_typename != '':
                        victim['shipTypeName'] = ship_typename
            for atk in kill['attackers']:
                if 'character_id' in atk:
                    char_id = int(atk['character_id'])
                    if char_id > 0:
                        char_name = self.get_char_name(char_id)
                        if char_name != '':
                            atk['characterName'] = char_name
                if 'corporation_id' in atk:
                    corp_id = int(atk['corporation_id'])
                    if corp_id > 0:
                        corp_name = self.get_corp_name(corp_id)
                        if corp_name != '':
                            atk['corporationName'] = corp_name
                if 'alliance_id' in atk:
                    ally_id = int(atk['alliance_id'])
                    if ally_id > 0:
                        ally_name = self.get_ally_name(ally_id)
                        if ally_name != '':
                            atk['allianceName'] = ally_name
                if 'ship_type_id' in atk:
                    ship_typeid = int(atk['ship_type_id'])
                    if ship_typeid > 0:
                        ship_typename = self.get_type_name(ship_typeid)
                        if ship_typename != '':
                            atk['shipTypeName'] = ship_typename

        return kills
