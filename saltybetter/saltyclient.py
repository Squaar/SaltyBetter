import requests
import logging
import json
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

# TODO: Use saltydb types here


class SaltyClient:
    _LOGIN_URL = 'http://saltybet.com/authenticate?signin=1'
    _BET_URL = 'http://saltybet.com/ajax_place_bet.php'
    _HEADERS = {
        'Connection': 'keep-alive',
        'Host': 'www.saltybet.com',
    }

    def __init__(self):
        self.spoof_enabled = False

    def spoof_login(self, spoof_cookie, user_agent):
        self._clean_session()
        self._HEADERS['Cookie'] = spoof_cookie
        self._HEADERS['User-Agent'] = user_agent
        log.info('User Agent: %s' % user_agent)
        try:
            cookies = spoof_cookie.split('; ')
            for cookie in cookies:
                cookie = cookie.split('=')
                self.session.cookies.update({cookie[0]: cookie[1]})
            self.spoof_enabled = True
            log.info("Spoof'd cookie '%s'" % spoof_cookie)
        except IndexError:
            log.error('Invalid cookie format. Please use format "id0=foo; id1=bar"')

    def login(self, email, password):
        payload = {
            'email': email,
            'pword': password,
            'authenticate': 'signin'
        }
        self._clean_session()
        response = self.session.post(self._LOGIN_URL, data=payload)
        self.spoof_enabled = False
        log.info('Logged in as %s' % format(email))

    def _clean_session(self):
        if 'Cookie' in self._HEADERS:
            del self._HEADERS['Cookie']
        self.session = requests.Session()
        self.session.headers.update(self._HEADERS)

    # TODO: Ajax doesn't work for some reason
    def get_wallet_balance(self):
        ajax_response = self.session.get('http://saltybet.com/ajax_tournament_end.php')
        page_response = self.session.get('http://saltybet.com')
        clean_html = page_response.text.strip().strip('<!DOCTYPE html">')

        soup = BeautifulSoup(clean_html, 'html.parser')
        page_balance = soup.find_all(id='b')[0]['value']

        # import pdb; pdb.set_trace()
        try:
            return {
                'ajax': None if not ajax_response.text else int(ajax_response.text),
                'page': None if not page_balance else int(page_balance)
            }
        except ValueError as e:
            raise AuthError('Not logged in! - %s' % repr(e))

    def place_bet(self, player, amount):
        amount = int(amount)
        if player not in [1, 2]:
            raise RuntimeError('Player to bet on must be in [1, 2]: %s' % player)
        payload = {
            'selectedplayer': 'player%s' % player,
            'wager': amount
        }
        response = self.session.post(self._BET_URL, data=payload)
        log.info('Bet %s on player %s' % (amount, player))

    def get_tournament_balance(self):
        response = self.session.get('http://saltybet.com/ajax_tournament_start.php')
        return int(response.text)

    def get_state(self):
        response = self.session.get('http://saltybet.com/state.json')
        state = json.loads(response.text)
        return state

class AuthError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message