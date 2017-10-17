import logging
from io import BytesIO

import cognitive_face

from counterserver import config, plugin_categories

API_KEY = config.config.get("emotions", "ApiKey")
ATTRIBUTES = "age,gender,smile,facialHair,glasses,emotion"


class EmotionAnalyserPlugin(plugin_categories.IEventReceiverPlugin):
    def __init__(self):
        cognitive_face.Key.set(API_KEY)

    def on_event(self, event_time, event_type, event_image=None, node_id=None):
        if event_image is None:
            return
        try:
            img = BytesIO(event_image)
            res = cognitive_face.face.detect(img, False, False, ATTRIBUTES)
            logging.info(res)
            if len(res) > 0 and "faceAttributes" in res[0]:
                return res[0]["faceAttributes"]
        except cognitive_face.util.CognitiveFaceException as e:
            logging.error(e)
