#!/usr/bin/python
# -*- coding: utf-8 -*-

from telegram import ChatAction
from telegram.ext import CommandHandler, Updater
from telegram.ext.dispatcher import run_async

from .utils import send_action, restricted, error_callback, TG
from django.conf import settings


@run_async
@send_action(ChatAction.TYPING)
def start(update, context):
    reply_message = 'Django SSPanel'
    tg = TG(update, context)
    tg.replyMessage(reply_message)


@restricted
@run_async
@send_action(ChatAction.TYPING)
def getChat(update, context):
    reply_message = f'chat \n{update.effective_chat}'
    tg = TG(update, context)
    tg.replyMessage(reply_message)


if __name__ == '__main__':
    updater = Updater(token=settings.TGBOT_TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('getChat', getChat))
    dispatcher.add_error_handler(error_callback)
    updater.start_polling()
    updater.idle()
