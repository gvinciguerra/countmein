import base64
import os
from datetime import datetime, timedelta

import jinja2

loader = jinja2.FileSystemLoader(os.path.dirname(__file__))
template_env = jinja2.Environment(loader=loader)


def on_get(persistence_mgr):
    time_24h_ago = datetime.now() - timedelta(days=1)
    time_10d_ago = datetime.now() - timedelta(days=10)

    last_24h = persistence_mgr.get_events(time_24h_ago, None, "hour")
    last_10d = persistence_mgr.get_events(time_10d_ago, None, "day")

    last_15faces = []
    events_w_face = persistence_mgr.get_events(time_10d_ago, None, None,
                                               15, True)
    for f in events_w_face:
        image_bytes = persistence_mgr.get_one_event(f["_id"])["image"]
        image_b64 = base64.b64encode(image_bytes).decode("ascii")
        last_15faces.append((f["_id"], image_b64))

    template = template_env.get_template("dashboard.html")
    templateVars = {
        "last_24h": list(last_24h),
        "last_10d": list(last_10d),
        "last_15faces": last_15faces
    }
    return template.render(templateVars)
