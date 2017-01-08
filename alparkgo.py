import json
from queue import Queue

import websocket
from slacker import Slacker

import settings


class Message(object):
    def __init__(self, text, channel, user):
        self.text = text
        self.channel = channel
        self.user = user


class Alparkgo(object):
    def __init__(self, api_token):
        self.slack = Slacker(api_token)
        self.messages_queue = Queue()
        self.dm_channels = {}
        self.usernames = {}
        self.receiver_channel_id = ''
        self.bot_user_id = ''
        self.bot_mention_string = ''

    def run(self):
        slack_response = self.slack.rtm.start().body
        self._parse_slack_information(slack_response)

        websocket_url = slack_response['url']
        ws = websocket.WebSocketApp(websocket_url,
                                    on_message=self._on_message(),
                                    on_error=self._on_error(),
                                    on_close=self._on_close())
        ws.on_open = self._on_open()
        ws.run_forever()

    def post_message(self, channel, message):
        self.slack.chat.post_message(channel, message, as_user=True)

    def _parse_slack_information(self, slack_response):
        self.bot_user_id = slack_response['self']['id']
        self.bot_mention_string = ''.join(['@', self.bot_user_id])
        self.usernames = {user_info['id']: user_info['name'] for user_info in slack_response['users']}
        self.dm_channels = {im_info['user']: im_info['id'] for im_info in slack_response['ims']}

        for user_id, username in self.usernames.items():
            if username == settings.RECEIVER.replace('@', ''):
                self.receiver_channel_id = self.dm_channels[user_id]
                break

    def _on_error(self):
        def on_error(ws, error):
            self.slack.chat.post_message(settings.RECEIVER,
                                         'Alparkgo가 아파합니다.\n{error}'.format(error=error),
                                         as_user=True)

        return on_error

    def _on_close(self):
        def on_close(ws):
            self.slack.chat.post_message(settings.RECEIVER, 'Alparkgo가 꺼졌습니다.', as_user=True)
        return on_close

    def _on_open(self):
        def on_open(ws):
            self.slack.chat.post_message(settings.RECEIVER,
                                         'Alparkgo가 켜졌습니다. '
                                         'Alparkgo에게 DM을 보내시면 메세지를 받은 순서대로 답장합니다.',
                                         as_user=True)
        return on_open

    def _on_message(self):
        def on_message(ws, ws_message):
            slack_message = json.loads(ws_message)
            if slack_message.get('type') == 'message':
                self._receive_message(ws, slack_message)
        return on_message

    def _receive_message(self, ws, slack_message):
        if self._is_not_alparkgo(slack_message['user']):
            if self._is_message_from_receiver(slack_message):
                self._response(ws, slack_message)
            elif self._is_message_to_alparkgo(slack_message):
                self._redirect_message_to_receiver(ws, slack_message)

    def _response(self, ws, slack_message):
        if not self.messages_queue.empty():
            message = self.messages_queue.get()
            response = {
                'type': 'message',
                'channel': message.channel,
                'text': '<@{user}>, `{question}` 에 대한 답변입니다.\n'
                        '```{answer}```'.format(user=self.usernames[message.user],
                                                question=message.text,
                                                answer=slack_message['text'])
            }
            ws.send(json.dumps(response))

    def _redirect_message_to_receiver(self, ws, slack_message):
        message = Message(slack_message['text'],
                          slack_message['channel'],
                          slack_message['user'])
        self.messages_queue.put(message)
        alert_to_receiver = {
            'type': 'message',
            'channel': self.receiver_channel_id,
            'text': '새로운 메세지가 왔습니다.\n ```{message}```'.format(message=message.text)
        }
        ws.send(json.dumps(alert_to_receiver))

    def _is_not_alparkgo(self, user_id):
        return user_id != self.bot_user_id

    def _is_message_from_receiver(self, slack_message):
        return slack_message['channel'] == self.receiver_channel_id

    def _is_message_to_alparkgo(self, slack_message):
        return slack_message['channel'] in self.dm_channels.values() \
                    or self.bot_mention_string in slack_message['text']


