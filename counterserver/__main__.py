import imghdr
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import falcon
import hug
from hug import types
from yapsy.PluginManager import PluginManager

from . import config, dashboard, detect_faces_frame, persistence
from .plugin_categories import IEventReceiverPlugin

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(module)s] %(message)s"
)
# logging.getLogger('yapsy').setLevel(logging.DEBUG)


@hug.post("/events", versions=1)
def post_event(response, event_time: types.GreaterThan(0)=None,
               event_type: types.GreaterThan(-1)=0, event_image=None,
               node_id: types.GreaterThan(0)=None):
    """
    Post an event.

    Args:
        event_time: the Unix timestamp of the event; if no value provided, the
            server will use its current time.
        event_type: an integer that identifies the kind of the event: 0=enter
            (default), 1=exit. Custom types can be given (e.g. a number >1 for
            "walk by" event).
        event_image: an optional image associate with the event.
    """
    if event_time is None:
        event_time = int(time.time())

    if event_image is not None \
       and imghdr.what(None, h=event_image) not in ["png", "jpeg", "jpg"]:
        logging.warning("Error reading image")
        response.status = falcon.HTTP_415
        return

    evt_id = persistence_mgr.add(event_time, event_type, event_image, node_id)
    for p in plugin_mgr.getPluginsOfCategory(IEventReceiverPlugin.__name__):
        future = executor.submit(p.plugin_object.on_event, event_time,
                                 event_type, event_image, node_id)
        future.add_done_callback(partial(plugins_callback, evt_id))

    response.status = falcon.HTTP_201
    return str(evt_id)


@hug.get("/events/{id}", version=1, output=hug.output_format.pretty_json)
def get_one_event(id):
    """Return the individual entry that matches the specified event id."""
    return persistence_mgr.get_one_event(id)


@hug.get("/events/search", version=1)
def get_search(response,
               from_time: types.GreaterThan(0)=0,
               to_time: types.GreaterThan(0)=None,
               limit: types.GreaterThan(0)=None,
               has_image: types.OneOf(("0", "1"))=None):
    """
    Search events with the specified time interval. Results can be filtered
    setting has_image=1.
    """
    return persistence_mgr.get_events(from_time, to_time, None, limit,
                                      has_image)


@hug.get("/events/stats", version=1)
def get_stats(response,
              granularity: types.OneOf(("month", "week", "day", "hour")),
              from_time: types.GreaterThan(0)=0,
              to_time: types.GreaterThan(0)=None,
              limit: types.GreaterThan(0)=None):
    """
    Aggregate and count events with the specified granularity (one of: month,
    week, day, hour) and time range.
    """
    return persistence_mgr.get_events(from_time, to_time, granularity, limit)


@hug.post("/frame", versions=1)
def post_frame(response, frame):
    """
    Upload a photo, tipically a frame from a camera and return face locations.
    """
    response.status = falcon.HTTP_200
    return detect_faces_frame.detect_faces(frame)


@hug.get("/", output=hug.output_format.html)
def get_root(response):
    return dashboard.on_get(persistence_mgr)


def plugins_callback(event_id, future):
    """Attach the value returned by a plugin to the associated event."""
    return_val = future.result(0)
    if return_val is not None:
        persistence_mgr.attach_info(event_id, return_val)


mongodb_uri = config.config.get("server", "MongoDBUri")
persistence_mgr = persistence.PersistenceManager(mongodb_uri)
executor = ThreadPoolExecutor()

plugin_mgr = PluginManager()
plugin_mgr.setPluginPlaces(["./counterserver/plugins"])
plugin_mgr.setCategoriesFilter({
    IEventReceiverPlugin.__name__: IEventReceiverPlugin,
})
plugin_mgr.collectPlugins()

for p in plugin_mgr.getAllPlugins():
    logging.info("Plugin '" + p.name + "' loaded")

if __name__ == '__main__':
    hug.API(__name__).http.serve()
