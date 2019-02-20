"""
Initial migration

Adds 1000 numbers to numbers collection.
"""
dependencies = []


def upgrade(db):
    db.numbers_collection.insert_many([{"i": i} for i in range(1000)])


def downgrade(db):
    db.numbers_collection.drop()
