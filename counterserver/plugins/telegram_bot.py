import logging
from datetime import datetime
from io import BytesIO

import telepot

from counterserver import config, plugin_categories

BOT_AUTH_TOKEN = config.config.get("telegram", "AuthToken")
SUBSCRIBE_CMD = config.config.get("telegram", "SubscribeCommand")


class TelegramBot(plugin_categories.IEventReceiverPlugin):
    bot = telepot.Bot(BOT_AUTH_TOKEN)
    offset = None
    subscribers = set()

    def on_event(self, event_time, event_type, event_image=None, node_id=None):
        try:
            updates = self.bot.getUpdates(offset=self.offset)
        except telepot.exception.TelegramError as e:
            logging.error(e)
            return
        if len(updates) > 0:
            subscribe_requests = filter(
                lambda u: SUBSCRIBE_CMD == u["message"].get("text"),
                updates
            )
            chat_ids = {u["message"]["chat"]["id"] for u in subscribe_requests}
            self.subscribers |= chat_ids
            self.offset = 1 + max([u["update_id"] for u in updates])

        for s in self.subscribers:
            text = "Event received: time={}, type={}, node_id={}".format(
                datetime.fromtimestamp(event_time),
                event_type,
                node_id
            )
            try:
                if event_image is None:
                    self.bot.sendMessage(s, text)
                else:
                    self.bot.sendPhoto(s, BytesIO(event_image), text)
            except telepot.exception.TelegramError as e:
                logging.error(e)
                return

        logging.info("Sent a message to {} user(s)".format(
            len(self.subscribers))
        )
