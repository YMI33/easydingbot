# MIT License

# Copyright (c) 2020 Seniverse

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import time
import hmac
import hashlib
import base64
import urllib.parse
import traceback
import json
from datetime import (datetime, 
                      timedelta, 
                      timezone)

import requests
import fire

from .config import *

class Dingbot:
    def __init__(self, dingbot_id='default'):
        try:
            configs[dingbot_id]
        except KeyError:
            raise ConfigNotFound(f'The {dingbot_id} is not in config, '
                                 'you can use command line "easydingbot add-dingbot" to add it.')

        self.webhook = configs[dingbot_id]['webhook']
        self.secret = configs[dingbot_id]['secret']

    @property
    def sign(self):
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, self.secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        self.signstring = sign
        self.timestamp = timestamp

    @property
    def url(self):
        self.sign
        return '&'.join([self.webhook, 
                         '&'.join([f'timestamp={self.timestamp}', 
                                   f'sign={self.signstring}'])])

    def send_msg(self, title, text):
        data = {
            'msgtype': 'markdown',
            'markdown': {
            'title': title,
            'text': '### {0}\n\n{1}'.format(title, text)
            }
        }
        return requests.post(url = self.url, headers = {
            'Content-Type': 'application/json'
            }, data = json.dumps(data))


def inform(dingbot_id='default', title='TASK NAME', text='TEXT'):
    """Send message to dingbot

    Args:
        dingbot_id (str, optional): Dingbot id that you setted in config, 
                                    if you don't know, use the command line "easydingbot-ls-dingbot" to list all dingbots ids.
                                    Defaults to 'default'.
        title (str, optional): The title showing in dingbot. Defaults to 'TASK NAME'.
        text (str, optional): The text showing in dingbot, it support markdown syntax. Defaults to 'TEXT'.
    """
    dingbot = Dingbot(dingbot_id)
    return dingbot.send_msg(title, text)


def feedback(dingbot_id='default', title='TASK NAME'):
    """A decorator to send feedback message

    Args:
        dingbot_id (str, optional): Dingbot id that you set in config. Defaults to 'default'.
        title (str, optional): The title you showing in dingbot, usually you should pass the task's identity here. 
                               Defaults to 'TASK NAME'.
    """
    def decorator_func(function):
        def wrapper(*args, **kwargs):
            dingbot = Dingbot(dingbot_id)
            init_dt = datetime.utcnow()
            init_timestr = (init_dt + timedelta(hours=8)).isoformat()
            start_text = '\n\n'.join([
                    f'**TIME**: {init_timestr}',
                    '**STATUS**: START RUNNING'
                    ]
            )
            dingbot.send_msg(title, start_text)
            try:
                result = function(*args, **kwargs)
            except:
                timestr = datetime.now(timezone(timedelta(hours=8))).isoformat()
                tb = traceback.format_exc()
                failed_text = '\n\n'.join([
                    f'**TIME**: {timestr}',
                    '**STATUS**: CRASHED',
                    '**TRACKBACK**:',
                    f'`{tb}`'
                ])
                dingbot.send_msg(title, failed_text)
                raise
            else:
                finished_dt = datetime.utcnow()
                elapsed_time = finished_dt - init_dt
                timestr = datetime.now(timezone(timedelta(hours=8))).isoformat()
                succeed_text = '\n\n'.join([
                    f'**TIME**: {timestr}',
                    '**STATUS**: FINISHED',
                    f'**ELAPSED TIME**: {elapsed_time}',
                ])
                dingbot.send_msg(title, succeed_text)
                return result
        return wrapper
    return decorator_func


def touch_once(dingbot_id='default'):
    """Touch once to test whether it work"""
    resp = json.loads(inform(dingbot_id).text)
    if resp['errcode'] == 300001:
        TokenError('Token not exists, please check your webhook.')
    elif resp['errcode'] == 310000:
        SecretError('Sign not match, please check your secret code.')
    elif resp['errcode'] == 404:
        URLError('URI not exists, please check your webhook.')
    elif resp['errcode'] == 0:
        print(f'Dingbot of {dingbot_id}\'s status is normal.')


def cli():
    fire.Fire({
        'add-dingbot': add_dingbot,
        'ls-dingbot': list_dingbots,
        'rm-dingbot': remove_dingbot,
        'touch': touch_once
    })


if __name__ == '__main__':
    pass