from dataclasses import asdict, dataclass
from datetime import datetime

from pymongo.collection import Collection


@dataclass
class MigrationState:
    migration_name: str
    started_at: datetime = None
    ended_at: datetime = None

    @property
    def successfully_applied(self):
        return self.started_at and self.ended_at


@dataclass
class StateManager:
    collection: Collection

    def _serialize(self, state: MigrationState):
        return asdict(state)

    def _deserialize(self, state_json: dict):
        state_json = {
            field: value
            for field, value in state_json.items()
            if not field.startswith("_")
        }
        return MigrationState(**state_json)

    def get(self, migration_name: str):
        state_json = self.collection.find_one({"migration_name": migration_name})
        del state_json["_id"]
        return MigrationState(**state_json)

    def set(self, state: MigrationState):
        state_json = asdict(state)
        self.collection.replace_one(
            filter={"migration_name": state_json["migration_name"]},
            replacement=state_json,
            upsert=True,
        )

    def __iter__(self):
        for state_json in self.collection.find():
            yield self._deserialize(state_json)
