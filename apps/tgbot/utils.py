#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from functools import wraps

from django.conf import settings


def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in settings.TGBOT_LIST_OF_ADMINS:
            logging.info("Unauthorized access denied for {}.".format(user_id))
            return
        return func(update, context, *args, **kwargs)

    return wrapped


def send_action(action):
    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return func(update, context, *args, **kwargs)

        return command_func

    return decorator


from telegram.error import (TelegramError, Unauthorized, BadRequest,
                            TimedOut, ChatMigrated, NetworkError)


def error_callback(update, context):
    try:
        raise context.error
    except Unauthorized:
        pass
    except BadRequest:
        pass
    except TimedOut:
        pass
    except NetworkError:
        pass
    except ChatMigrated as e:
        pass
    except TelegramError:
        pass


class TG:
    def __init__(self, update, context):
        self.update = update
        self.context = context

    def replyMessage(self, text, reply_markup=None):
        return self.context.bot.send_message(chat_id=self.update.effective_chat.id,
                                             reply_to_message_id=self.update.message.message_id,
                                             text=text,
                                             reply_markup=reply_markup)
