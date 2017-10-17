import imghdr
import logging
import tempfile

from counterserver import plugin_categories

logging.basicConfig(level=logging.INFO)


class SaveImagesPlugin(plugin_categories.IEventReceiverPlugin):
    def on_event(self, event_time, event_type, event_image=None, node_id=None):
        if event_image is None:
            return

        ext = imghdr.what(None, h=event_image)
        logging.info(ext)
        if ext in ["png", "jpeg"]:
            with tempfile.NamedTemporaryFile(suffix="."+ext) as image_file:
                image_file.write(event_image)
                logging.info(image_file.name)
