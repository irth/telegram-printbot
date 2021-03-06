#!/usr/bin/env python3

import subprocess
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, PicklePersistence, Filters


class Bot:
    def __init__(self, token, admin, device):
        # Admin contains the ID of the user that can allow other users to print
        self.admin = admin
        # Device is the CUPS printer name from `lpstat -e`
        self.device = device

        # Using a pickle in ./ to persist the allowlist
        self.persistence = PicklePersistence(filename='data.pickle')

        # Setting up python-telegram-bot
        self.updater = Updater(
            token=token, use_context=True, persistence=self.persistence)

        # Registering command handlers
        self.dispatcher = self.updater.dispatcher
        self.dispatcher.add_handler(CommandHandler('start', self.cmd_start))
        self.dispatcher.add_handler(CommandHandler('add', self.cmd_add))
        self.dispatcher.add_handler(CommandHandler('deny', self.cmd_deny))

        # This message handler will only trigger on PDF files
        self.dispatcher.add_handler(MessageHandler(
            Filters.document.pdf, self.on_message))

    def ensure_bot_data(self, context):
        """
        A helper function to ensure that the schema of bot_data is correct.
        """
        if "allowed" not in context.bot_data:
            context.bot_data["allowed"] = {}

    def is_admin(self, user, context):
        """
        Returns true if the user is an admin.
        """
        return user.id == self.admin

    def is_allowed(self, user, context):
        """
        Returns true if the user is allowed to print.
        """
        self.ensure_bot_data(context)
        return self.is_admin(user, context) or (user.id in context.bot_data["allowed"])

    def allow(self, user_id, context):
        """
        Adds the user_id to the allowlist.
        """
        self.ensure_bot_data(context)
        context.bot_data["allowed"][user_id] = True

    def deny(self, user_id, context):
        """
        Removes the user_id from the allowlist if the user is in it.
        """
        self.ensure_bot_data(context)
        context.bot_data["allowed"].pop(user_id, None)

    def cmd_start(self, update, context):
        """
        /start - the first command that the user runs. Telegram gives you a
        button to run it instead of a text input when you first interact with
        the bot.
        """
        user = update.effective_user

        message = "Hello. "
        if self.is_allowed(user, context):
            message += "You can print by sending a PDF file to this bot."
            if self.is_admin(user, context):
                message += " You are an administrator. Add people to the bot using /add <numerical_ID>."
        else:
            message += f"You are not allowed to print. Ask the admin to add you. Your ID is: {user.id}."

        context.bot.send_message(
            chat_id=update.effective_chat.id, text=message)

    def cmd_add(self, update, context):
        if not self.is_admin(update.effective_user, context):
            context.bot.send_message(
                chat_id=update.effective_chat.id, text="You are not an admin.")
            return
        argv = update.effective_message.text.split(" ")
        if len(argv) != 2:
            context.bot.send_message(
                chat_id=update.effective_chat.id, text="Usage: /add <numerical user ID>")
            return
        try:
            self.allow(int(argv[1]), context)
            context.bot.send_message(
                chat_id=update.effective_chat.id, text="Allowed. Use /deny <ID> to remove.")
        except ValueError:
            context.bot.send_message(
                chat_id=update.effective_chat.id, text="Provided user ID is invalid.")

    def cmd_deny(self, update, context):
        if not self.is_admin(update.effective_user, context):
            context.bot.send_message(
                chat_id=update.effective_chat.id, text="You are not an admin.")
            return
        argv = update.effective_message.text.split(" ")
        if len(argv) != 2:
            context.bot.send_message(
                chat_id=update.effective_chat.id, text="Usage: /deny <numerical user ID>")
            return
        try:
            self.deny(int(argv[1]), context)
            context.bot.send_message(
                chat_id=update.effective_chat.id, text="Denied.")
        except ValueError:
            context.bot.send_message(
                chat_id=update.effective_chat.id, text="Provided user ID is invalid.")

    def on_message(self, update, context):
        if not self.is_allowed(update.effective_user, context):
            message = f"You are not allowed to print. Ask the admin to add you. Your ID is: {update.effective_user.id}."
            context.bot.send_message(
                chat_id=update.effective_chat.id, text=message)
            return
        doc = update.effective_message.document
        if doc is None:
            return
        f = doc.get_file()

        if f.file_size >= 20*1024*1024:
            context.bot.send_message(
                chat_id=update.effective_chat.id, text="Unfortunately, Telegram bots cannot receive files over 20MiB.")
            return

        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Attempting to print...")

        with subprocess.Popen(["lp", "-d", self.device], stdin=subprocess.PIPE) as proc:
            f.download(out=proc.stdin)
            try:
                proc.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                context.bot.send_message(
                    chat_id=update.effective_chat.id, text="30 second timeout reached. Killing the process.")
                proc.kill()
                proc.communicate()
            if proc.returncode == 0:
                context.bot.send_message(
                    chat_id=update.effective_chat.id, text="Job sent to the printer.")
            else:
                context.bot.send_message(
                    chat_id=update.effective_chat.id, text=f"`lp` returned an error: {proc.returncode}.")

    def start(self):
        self.updater.start_polling()


Bot(os.getenv("TELEGRAM_TOKEN"), int(os.getenv("TELEGRAM_ADMIN")),
    os.getenv("CUPS_DEVICE")).start()
