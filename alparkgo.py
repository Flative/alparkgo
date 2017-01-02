from slacker import Slacker

import settings

slack = Slacker(settings.SLACK_API_TOKEN)

slack.chat.post_message(settings.RECEIVER, 'Hello fellow slackers!', as_user=True)
