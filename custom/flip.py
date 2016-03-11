#!/sevabot

# -*- coding: utf-8 -*-

"""
Simple chat parsing for FlipBot
"""
from __future__ import unicode_literals

import logging
import Skype4Py
import time
import os, random, math, io
from sevabot.bot.stateful import StatefulSkypeHandler
from sevabot.utils import ensure_unicode

from threading import Thread

logger = logging.getLogger('Chat')

# Set to debug only during dev
logger.setLevel(logging.INFO)

logger.debug('Chat module level load import')

base_command = "flip"

admins = ['impaction123']
non_admin_commands = ["dica"]

global chat
global chat_thread
global enable_chat

HELP_TEXT = """Chat module allows you to control the bot chat behavior.

Commands:

!"""+base_command+""": Shows this help text

!"""+base_command+""" start: Starts the bot chat routine with default delay.

!"""+base_command+""" end: Stops the bot chat routine.

!"""+base_command+""" delay val: Sets the minimum delay for bot reply. 0 means no delay.

!"""+base_command+""" dica: Requests a classic reply from bot.
"""


class ChatHandler(StatefulSkypeHandler):

    """
    Skype message handler class for the chat parsing
    """

    def __init__(self):
        """
        Use `init` method to initialize a handler.
        """

        logger.debug('Call handler constructed')

    def init(self, sevabot):
        """
        Set-up our state. This is called every time module is (re)loaded.

        :param skype: Handle to Skype4Py instance
        """
        global enable_chat
        logger.debug('Chat handler init')

        self.skype = sevabot.getSkype()
        self.quotes = []
        self.num_quotes = 0
        self.parse_quotes('/home/ordep/sevabot/custom/flip.txt')
        self.timeToSpeak = False
        self.delay = 300
        enable_chat = False
        self.commands = {'help': self.help, 'start': self.start_chat, 'stop': self.stop_chat, 'delay': self.set_delay, 'dica': self.dica}

    def handle_message(self, msg, status):
        """
        Override this method to customize a handler.
        """

        body = ensure_unicode(msg.Body)

        logger.debug('Chat handler got: {}'.format(body))

        # If the separators are not specified, runs of consecutive
        # whitespace are regarded as a single separator
        words = body.split()

        if not len(words):
            return False

        if words[0] != '!'+base_command+'':
            return False

        if len(words) > 1 and words[1] not in non_admin_commands:
            if msg.Sender.Handle not in admins:
                msg.Chat.SendMessage('Nao mandas em mim.')
                return True

        args = words[1:]
        #msg.Chat.SendMessage(args)

        if not len(args):
            # shows help
            self.help(msg, status, args)
            return True

        for name, cmd in self.commands.items():
            if name == args[0]:
                cmd(msg, status, args)
                return True

        msg.Chat.SendMessage(args[0]+' not a valid command. [start, stop, delay, dica]')
        return True

    def shutdown():
        """
        Called when the module is reloaded.
        """
        logger.debug('Call handler shutdown')

    def help(self, msg, status, args):
        """
        Show help message to the sender.
        """
        msg.Chat.SendMessage(HELP_TEXT)

    def chat_loop(self):
        global chat
        global enable_chat
        while True:
            if enable_chat and chat:
                 self.random()
                 time.sleep(self.delay)
            else:
                 time.sleep(1)

    def start_chat(self, msg, status, args):
        global chat
        global chat_thread
        global enable_chat
        msg.Chat.SendMessage('Chat mode should start');
        enable_chat = True
        chat = msg.Chat
        chat_thread = Thread(target=self.chat_loop)
        chat_thread.daemon = 1
        chat_thread.start()

    def stop_chat(self, msg, status, args):
        global enable_chat
        msg.Chat.SendMessage('Chat mode should stop');
        enable_chat = False
#        chat_thread.
        
    def set_delay(self, msg, status, args):
        self.delay = int(args[1])
        msg.Chat.SendMessage('Delay set');

    def dica(self, msg, status, args):
        r = math.ceil(random.random()*self.num_quotes) - 1
        msg.Chat.SendMessage(self.quotes[int(r)]);

    def random(self):
        global chat
        r = math.ceil(random.random()*self.num_quotes) - 1
        chat.SendMessage(self.quotes[int(r)])

    def parse_quotes(self,filename):
        file = open(filename, 'r')
        for line in file:
            if line[0] == '-':
                self.quotes.append(line[1:])
        self.num_quotes = len(self.quotes)
        #print 'parsed '+string(self.num_quotes)+' quotes'
        file.close()


# Export the instance to Sevabot
sevabot_handler = ChatHandler()

__all__ = ['sevabot_handler']
