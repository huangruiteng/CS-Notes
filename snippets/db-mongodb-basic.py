from pymongo import MongoClient
from bson import ObjectId
from pprint import pprint

client = MongoClient("mongodb://localhost:27017")
db = client["demo"]
coll = db["people"]

def seed():
    coll.drop()
    coll.insert_many([
        {"user_id": "bcd001", "age": 45, "status": "A"},
        {"user_id": "xyz002", "age": 30, "status": "A"},
        {"user_id": "lmn003", "age": 25, "status": "D"},
    ])

def create_one():
    r = coll.insert_one({"user_id": "new004", "age": 28, "status": "A"})
    return r.inserted_id

def read_range():
    cur = coll.find({"age": {"$gt": 25, "$lte": 50}}, {"user_id": 1, "status": 1, "_id": 0})
    return list(cur)

def update_many():
    r = coll.update_many({"status": "A"}, {"$inc": {"age": 3}})
    return r.modified_count

def delete_many():
    r = coll.delete_many({"status": "D"})
    return r.deleted_count

def ensure_indexes():
    coll.create_index([("user_id", 1)], unique=True)
    coll.create_index([("age", 1)])
    return coll.index_information()

places = db["places"]

def ensure_geo():
    places.drop()
    places.create_index([("location", "2dsphere")])
    places.insert_many([
        {"name": "A", "location": {"type": "Point", "coordinates": [116.397, 39.908]}},
        {"name": "B", "location": {"type": "Point", "coordinates": [116.404, 39.915]}},
    ])

def nearby(lng: float, lat: float, max_m: int = 1000):
    cur = places.find({
        "location": {
            "$near": {
                "$geometry": {"type": "Point", "coordinates": [lng, lat]},
                "$maxDistance": max_m,
            }
        }
    })
    return list(cur)

def create_timeseries(name: str):
    try:
        db.create_collection(name, timeseries={"timeField": "ts", "metaField": "meta"})
    except Exception:
        pass
    return db[name]

def agg_unique_items():
    pipeline = [
        {"$project": {"user_id": 1, "item_id": 1, "_id": 0}},
        {"$group": {"_id": "$user_id", "unique_items": {"$addToSet": "$item_id"}}},
        {"$addFields": {"unique_item_count": {"$size": "$unique_items"}}},
        {"$project": {"user_id": "$_id", "unique_item_count": 1, "_id": 0}},
    ]
    return list(db["logs"].aggregate(pipeline, allowDiskUse=True))

if __name__ == "__main__":
    seed()
    pprint(create_one())
    pprint(read_range())
    pprint(update_many())
    pprint(delete_many())
    pprint(ensure_indexes())
    ensure_geo()
    pprint(nearby(116.404, 39.915, 2000))
    ts = create_timeseries("metrics")
    ts.insert_one({"ts": 1734518400, "meta": {"device": "d1"}, "value": 1})
    pprint(list(ts.find({}, {"_id": 0})))
