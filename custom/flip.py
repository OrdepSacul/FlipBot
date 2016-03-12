#!/sevabot

# -*- coding: utf-8 -*-

"""
Simple chat parsing for FlipBot
"""
from __future__ import unicode_literals

import logging
import Skype4Py
import time
import os, random, math, io, string
from sevabot.bot.stateful import StatefulSkypeHandler
from sevabot.utils import ensure_unicode

from threading import Thread

logger = logging.getLogger('Chat')

# Set to debug only during dev
logger.setLevel(logging.INFO)

logger.debug('Chat module level load import')

base_command = "flip"

admins = ['impaction123', 'ordep.sevabot']
non_admin_commands = ["dica"]

#chat object, after starting either chat modes
global chat

#random chat mode
global chat_thread
global enable_chat
global timeToChat

#smart chat
global smart_chat_thread
global enable_smart_chat
global timeToSmartChat
global timeToChatUserSpecific

#quote dictionary keys, values and items
# global quote_keys
# global quote_values
# global quote_items


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
        global enable_chat, enable_smart_chat, timeToSmartChat, timeToChat, timeToChatUserSpecific
        logger.debug('Chat handler init')

        self.skype = sevabot.getSkype()
        self.quotes = []
        self.quote_dictionary = {}
        self.quote_keys = []
        self.quote_values = []
        self.quote_items = []
        self.keyword_dictionary = {}
        self.current_category = ''
        self.num_quotes = 0
        self.parse_quotes('/home/ordep/sevabot/custom/flip.txt')
        self.parse_quotes_dictionary('/home/ordep/sevabot/custom/flip.txt')
        self.delay = 300
        self.smart_delay = 20
        timeToChat = False
        timeToSmartChat = False
        timeToChatUserSpecific = False
        enable_chat = False
        enable_smart_chat = False
        self.commands = {'help': self.help,
                         'start': self.start_chat, 
                         'start_smart': self.start_smart_chat, 
                         'stop': self.stop_chat, 
                         'stop_smart': self.stop_smart_chat, 
                         'delay': self.set_delay, 
                         'delay_smart': self.set_smart_delay, 
                         'dica': self.dica,
                         'categories': self.show_categories
                         }

    def handle_message(self, msg, status):
        """
        Override this method to customize a handler.
        """
        global timeToSmartChat, timeToChatUserSpecific
        body = ensure_unicode(msg.Body)

        logger.debug('Chat handler got: {}'.format(body))

        # If the separators are not specified, runs of consecutive
        # whitespace are regarded as a single separator
        words = body.split()

        if not len(words):
            return False

        if words[0] == '!'+base_command+'':
            commandCalled = False
            if len(words) > 1:
                if words[1] not in non_admin_commands:
                    if msg.Sender.Handle not in admins:
                        msg.Chat.SendMessage('Nao mandas em mim.')
                        return True
                args = words[1:] #start_smart
                for name, cmd in self.commands.items():
                    if name == args[0]:
                        cmd(msg, status, args)
                        commandCalled = True
                        return True
                if not commandCalled:
                    msg.Chat.SendMessage(args[0]+' not a valid command for FlipBot. See !flip')
                    return True
            elif len(words) == 1:
                self.help(msg, status, words[1:])
                return True
        elif words[0][0] != '!':
            if timeToSmartChat:
                self.try_reply(msg,status,words)
            #if timeToChatUserSpecific:
            #    self.try_reply_user(msg,status,words)
            #return True

        return False

    def shutdown(self):
        """
        Called when the module is reloaded.
        """
        logger.debug('Call handler shutdown')

    def help(self, msg, status, args):
        """
        Show help message to the sender.
        """
        msg.Chat.SendMessage(HELP_TEXT)

    def try_reply(self,msg,status,words):
        #f = open('/home/ordep/sevabot/custom/cat.txt','w')
        global timeToSmartChat
        for w in words:
            for cat, keywords in self.keyword_dictionary.items():
                #f.write(str(cat)+'\n')
                if w in keywords:
                    self.dica_category(msg,status,str(cat).strip())
                    timeToSmartChat = False
        #f.close()

    def try_reply_user(self,msg,status,words):
        #f = open('/home/ordep/sevabot/custom/cat.txt','w')
        sender = str(msg.Sender.Handle).strip()
        msg.Chat.SendMessage(sender)
        global timeToChatUserSpecific
        for cat, keywords in self.keyword_dictionary.items():
            #f.write(str(cat)+'\n')
            if sender in keywords:
                self.dica_category(msg,status,str(cat).strip())
                timeToChatUserSpecific = False
        #f.close()

    def chat_loop(self):
        global chat
        global enable_chat
        while True:
            if enable_chat and chat:
                 self.random()
                 time.sleep(self.delay)
            else:
                 time.sleep(1)

    def smart_chat_loop(self):
        global chat
        global enable_smart_chat
        global timeToSmartChat
        while True:
            if enable_smart_chat and chat:
                 timeToSmartChat = True
                 timeToChatUserSpecific = True;
                 time.sleep(self.smart_delay)
                 #chat.SendMessage('loop');
            else:
                 time.sleep(1)

    def start_smart_chat(self, msg, status, args):
        global chat
        global smart_chat_thread
        global enable_smart_chat
        msg.Chat.SendMessage('Smart chat started')
        enable_smart_chat = True
        if 'chat' not in globals():
            chat = msg.Chat
        smart_chat_thread = Thread(target=self.smart_chat_loop)
        smart_chat_thread.daemon = 1
        smart_chat_thread.start()

    def start_chat(self, msg, status, args):
        global chat
        global chat_thread
        global enable_chat
        msg.Chat.SendMessage('Chat mode should start')
        enable_chat = True
        if 'chat' not in globals():
            chat = msg.Chat
        chat_thread = Thread(target=self.chat_loop)
        chat_thread.daemon = 1
        chat_thread.start()

    def stop_chat(self, msg, status, args):
        global enable_chat
        msg.Chat.SendMessage('Chat mode should stop')
        enable_chat = False


    def stop_smart_chat(self, msg, status, args):
        global enable_smart_chat
        msg.Chat.SendMessage('Smart chat stopped')
        enable_chat = False

        
    def set_delay(self, msg, status, args):
        self.delay = int(args[1])
        msg.Chat.SendMessage('Delay set to '+str(delf.delay)+'s')

    def set_smart_delay(self, msg, status, args):
        self.smart_delay = int(args[1])
        msg.Chat.SendMessage('Smart delay set to '+str(self.smart_delay)+'s')

    def random(self):
        global chat
        r = random.randint(0, self.num_quotes-1) #math.ceil(random.random()*self.num_quotes) - 1
        chat.SendMessage(self.quotes[int(r)])

    def parse_quotes(self,filename):
        self.current_category = 0
        file = open(filename, 'r')
        for line in file:
            if line[0] == '-':
                self.quotes.append(line[1:])
        self.num_quotes = len(self.quotes)
        #print 'parsed '+string(self.num_quotes)+' quotes'
        file.close()

    def parse_quotes_dictionary(self,filename):
#        global quote_keys, quote_values, quote_items
        self.current_category = 0
        file = open(filename, 'r')
        for line in file:
            if line[0] == '-':
                #self.quotes.append(line[1:])
                self.quote_dictionary[self.current_category].append(line[1:])			
            elif line[0] == '$':
                self.new_quote_category(line)
        #print 'parsed '+string(self.num_quotes)+' quotes'
        file.close()
        self.quote_keys = self.quote_dictionary.keys()
        self.quote_values = self.quote_dictionary.values()
        self.quote_items = self.quote_dictionary.items()


    def new_quote_category(self, line):
        #file = open('/home/ordep/sevabot/custom/parse.txt','w')
        cat = line.split(':')[0][1:].strip()
        keywords = line.replace(':',' ').replace(',',' ').split()[1:]
        self.keyword_dictionary[cat] = keywords
        #file.write(cat+'\n')
        #for k in keywords:
        #    file.write(str(k)+'\n')
        self.quote_dictionary[cat] = []
        self.current_category = cat
        #file.close()

    def dica(self, msg, status, args):
 #       global quote_keys, quote_values, quote_items
        if len(args) == 1:
            #msg.Chat.SendMessage(self.quote_dictionary['random'][0])
            r = random.randint(0,len(self.quote_keys)-1) #rand category
            dic_quotes = self.quote_dictionary[self.quote_keys[r]]
            r2 = random.randint(0, len(dic_quotes)-1)
            msg.Chat.SendMessage(dic_quotes[r2])
        elif len(args) > 1:
            try:
                dic_quotes = self.quote_dictionary[args[1].strip()]
                r = random.randint(0, len(dic_quotes)-1)
                msg.Chat.SendMessage(dic_quotes[r])
            except KeyError:
                msg.Chat.SendMessage('Category is not defined.')

    def dica_category(self, msg, status, args):
#        global quote_keys, quote_values, quote_items
        if args == '':
            #msg.Chat.SendMessage(self.quote_dictionary['random'][0])
            r = random.randint(0,len(self.quote_keys)-1) #rand category
            dic_quotes = self.quote_dictionary[self.quote_keys[r]]
            r2 = random.randint(0, len(dic_quotes)-1)
            msg.Chat.SendMessage(dic_quotes[r2])
        else:
            try:
                dic_quotes = self.quote_dictionary[args.strip()]
                r = random.randint(0, len(dic_quotes)-1)
                msg.Chat.SendMessage(dic_quotes[r])
            except KeyError, e:
                msg.Chat.SendMessage('Category is not defined: '+str(e))

    def show_categories(self, msg, status, args):
        res = 'Categories: '
        for cat in self.quote_keys:
            res+=str(cat)+', '
        res = res.strip()
        msg.Chat.SendMessage(res.rstrip(',')+'.')

# Export the instance to Sevabot
sevabot_handler = ChatHandler()

__all__ = ['sevabot_handler']
