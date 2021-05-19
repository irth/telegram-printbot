import os
from telegram.ext import Updater, CommandHandler, MessageHandler, PicklePersistence, Filters


class Bot:
    def __init__(self, token, admin):
        self.admin = admin
        self.persistence = PicklePersistence(filename='data.pickle')
        self.updater = Updater(
            token=token, use_context=True, persistence=self.persistence)
        self.dispatcher = self.updater.dispatcher
        self.dispatcher.add_handler(CommandHandler('start', self.cmd_start))
        self.dispatcher.add_handler(CommandHandler('add', self.cmd_add))
        self.dispatcher.add_handler(CommandHandler('deny', self.cmd_deny))

        self.dispatcher.add_handler(MessageHandler(
            Filters.document.pdf, self.on_message))

    def ensure_bot_data(self, context):
        if "allowed" not in context.bot_data:
            context.bot_data["allowed"] = {}

    def is_admin(self, user, context):
        return user.id == self.admin

    def is_allowed(self, user, context):
        self.ensure_bot_data(context)
        return self.is_admin(user, context) or (user.id in context.bot_data["allowed"])

    def allow(self, user_id, context):
        self.ensure_bot_data(context)
        context.bot_data["allowed"][user_id] = True

    def deny(self, user_id, context):
        self.ensure_bot_data(context)
        context.bot_data["allowed"].pop(user_id, None)

    def cmd_start(self, update, context):
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
        f.download(custom_path=f"/tmp/{update.effective_user.id}.pdf")

    def start(self):
        self.updater.start_polling()


Bot(os.getenv("TELEGRAM_TOKEN"), int(os.getenv("TELEGRAM_ADMIN"))).start()
