"""
Initial migration

Adds 1000 numbers to numbers collection.
"""
name = "20150612230153"
dependencies = []


def upgrade(db):
    db.numbers_collection.insert_many([{"i": i} for i in range(1000)])


def downgrade(db):
    db.numbers_collection.drop()
