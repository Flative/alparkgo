import websocket
from slacker import Slacker

import settings
import json

slack = Slacker(settings.SLACK_API_TOKEN)
messages_queue = []
dm_channel = 'D3KNC1EGY'
bot_user_id = ''


def on_message(ws, message):
    message_dict = json.loads(message)
    print(message)
    if message_dict.get('type') == 'message':
        channel = message_dict['channel']
        if channel == dm_channel:
            if message_dict['user'] != bot_user_id:
                response = {'type': 'message', 'channel': channel, 'text': 'response from alparkgo'}
                ws.send(json.dumps(response))
        elif bot_user_id in message_dict['text']:
            print('yo!')


def on_error(ws, error):
    slack.chat.post_message(settings.RECEIVER,
                            'Alparkgo가 아파합니다.\n{error}'.format(error=error),
                            as_user=True)


def on_close(ws):
    slack.chat.post_message(settings.RECEIVER, 'Alparkgo가 꺼졌습니다.', as_user=True)


def on_open(ws):
    slack.chat.post_message(settings.RECEIVER,
                            'Alparkgo가 켜졌습니다. Alparkgo에게 DM을 보내시면 메세지를 받은 순서대로 답장합니다.',
                            as_user=True)


if __name__ == '__main__':
    rtm = slack.rtm.start()
    print(json.dumps(rtm.body))
    bot_user_id = rtm.body['self']['id']
    websocket_url = slack.rtm.start().body['url']
    ws = websocket.WebSocketApp(websocket_url,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()
