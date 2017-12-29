import json
import sys


class SavedState:
    def __init__(self):
        self.involved_chatids = []

    def load(self, filename: str) -> bool:
        try:
            with open(filename, 'rt', encoding='utf-8') as fp:
                cfg = json.load(fp)
            if 'involved_chatids' not in cfg:
                print('Failed to load saved state: Incorrect format!', file=sys.stderr)
                return False
            self.involved_chatids = cfg['involved_chatids']
        except IOError as e:
            print('Failed to load saved state: {}'.format(str(e)), file=sys.stderr)
            return False
        return True

    def save(self, filename: str) -> bool:
        try:
            with open(filename, 'wt', encoding='utf-8') as fp:
                cfg = {
                    'involved_chatids': self.involved_chatids
                }
                json.dump(cfg, indent=True)
        except IOError as e:
            print('Failed to save state: {}'.format(str(e)), file=sys.stderr)
            return False
        return True
