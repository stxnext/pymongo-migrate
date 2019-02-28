"""
We decided we don't like numbers <=500 anymore
"""
name = "20181123000000_gt_500"
dependencies = ["20150612230153"]


def upgrade(db):
    db.numbers_collection.delete_many({"i": {"$lt": 501}})


def downgrade(db):
    db.numbers_collection.insert_many([{"i": i} for i in range(501)])
