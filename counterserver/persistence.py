import logging
from datetime import datetime

import pymongo
from bson.binary import Binary
from bson.objectid import ObjectId

TIME_KEY = "time"
TYPE_KEY = "type"
NODE_KEY = "node_id"
IMAGE_KEY = "image"


class PersistenceManager():
    def __init__(self, uri):
        self.client = pymongo.MongoClient(uri, socketKeepAlive=True)
        self.events = self.client.countmein.events
        self.events.create_index([(TIME_KEY, pymongo.DESCENDING)])
        self.granularity_format = {
            "month": "%Y-%m",
            "week": "%YW%U",
            "day": "%Y-%m-%d",
            "hour": "%Y-%m-%dT%H:00"
        }

    def _cast_document(self, document):
        if document is not None and "_id" in document:
            document["_id"] = str(document["_id"])
        return document

    def add(self, event_time, event_type, event_image=None, node_id=None):
        """Store an event with the specified properties."""
        new_event = {
            TIME_KEY: datetime.fromtimestamp(event_time),
            TYPE_KEY: event_type
        }
        if event_image is not None:
            new_event[IMAGE_KEY] = Binary(event_image)
        if node_id is not None:
            new_event[NODE_KEY] = node_id
        inserted_id = self.events.insert_one(new_event).inserted_id
        logging.info("Added document with _id=" + str(inserted_id))
        return inserted_id

    def get_one_event(self, id):
        """Get the properties of the specified event id."""
        event = self.events.find_one(ObjectId(id))
        return self._cast_document(event)

    def attach_info(self, id, attachment):
        """Attach additional info to the specified event id."""
        if isinstance(attachment, dict):
            update = {"$addToSet": {"attachment": attachment}}
            filt = {"_id": ObjectId(id)}
            self.events.find_one_and_update(filt, update)

    def get_events(self, from_time=0, to_time=None, granularity=None,
                   limit=None, has_image=None):
        """
        Filter and return the events matching the specified query, optionally
        aggregated and counted according to a time granularity (month, week,
        day, hour).
        """
        if isinstance(from_time, int):
            from_time = datetime.fromtimestamp(from_time)
        if isinstance(to_time, int):
            to_time = datetime.fromtimestamp(to_time)

        pipeline = []

        # Match stage
        match_dict = {TIME_KEY: {"$gt": from_time}}
        if to_time is not None:
            match_dict[TIME_KEY]["$lt"] = to_time
        if has_image is not None:
            match_dict[IMAGE_KEY] = {"$exists": has_image}
        pipeline.append({"$match": match_dict})

        # Group stage
        if granularity is None:
            # replace image with a boolean: images must be retrieved one by one
            pipeline.append({
                "$project": {
                    IMAGE_KEY: {"$cond": ["$"+IMAGE_KEY, True, False]},
                    TYPE_KEY: 1,
                    TIME_KEY: 1
                }
            })
            pipeline.append({
                "$sort": {TIME_KEY: pymongo.DESCENDING}
            })
        else:
            project_dict = {
                "datelabel": {
                    "$dateToString": {
                        "format": self.granularity_format[granularity],
                        "date": "$time"
                    }
                }
            }
            group_dict = {"_id": "$datelabel", "count": {"$sum": 1}}
            sort_dict = {"_id": pymongo.ASCENDING}
            pipeline.append({"$project": project_dict})
            pipeline.append({"$group": group_dict})
            pipeline.append({"$sort": sort_dict})

        # Limit stage
        if limit is not None:
            pipeline.append({"$limit": limit})
        return map(self._cast_document, list(self.events.aggregate(pipeline)))
