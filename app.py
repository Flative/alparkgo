import settings

from alparkgo import Alparkgo

if __name__ == '__main__':
    alparkgo = Alparkgo(settings.SLACK_API_TOKEN)
    alparkgo.run()
