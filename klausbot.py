import os
import re
from time import sleep
from threading import Thread
from slackclient import SlackClient

BOT_NAME = 'klausbot'
BOT_ID = ''
slack_client = SlackClient(os.environ['SLACK_BOT_TOKEN'])

links = {}
save_pattern = re.compile('^save\s(?P<name>[a-zA-Z]+)\s(?P<link>\S+)$')
get_pattern = re.compile('^get\s(?P<name>[a-zA-Z]+)\s?((?P<minutes>\d+)m)?\s?((?P<seconds>\d+)s)?$')


def get_bot_id():
    api_call = slack_client.api_call('users.list')
    if api_call.get('ok'):
        users = api_call.get('members')
        for user in users:
            if user.get('name') == BOT_NAME:
                global BOT_ID
                BOT_ID = '<@{}>'.format(user.get('id'))


def parse_message(message):
    text = message['text']
    if text.startswith(BOT_ID):
        text = text.split(BOT_ID)[1].strip().lower()
        if save_pattern.match(text):
            handle_save_command(message, save_pattern.match(text))
        elif get_pattern.match(text):
            handle_get_command(message, get_pattern.match(text))
        else:
            post_message('Command not found', message['channel'])


def handle_save_command(message, match):
    name = match.group('name')
    link = match.group('link')
    links[name] = link
    response = '{} saved to {}'.format(link, name)
    post_message(response, message['channel'])


def calculate_time(match):
    minutes = match.group('minutes') or 0
    seconds = match.group('seconds') or 0
    return int(minutes) * 60 + int(seconds)


def handle_get_command(message, match):
    name = match.group('name')
    print("Handling get")
    if name not in links:
        error_message = '{} not found'.format(name)
        post_message(error_message, message['channel'])
    else:
        sleep_time = calculate_time(match)
        sleep(sleep_time)
        post_message(links[name], message['channel'])


def handle_messages_read(messages):
    if messages is not None:
        for message in messages:
            if message and 'text' in message:
                parse_message(message)


def post_message(message, channel='#general'):
    slack_client.api_call(
        'chat.postMessage',
        channel=channel,
        text=message,
        as_user=True
    )


if __name__ == '__main__':
    if slack_client.rtm_connect():
        print('KlausBot started and running')
        get_bot_id()
        while True:
            messages = slack_client.rtm_read()
            handle_message_thread = Thread(target=handle_messages_read, args=(messages,))
            handle_message_thread.start()
            sleep(0.1)
    else:
        print('Could not connect')
