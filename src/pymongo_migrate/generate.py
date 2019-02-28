import datetime
import re
from pathlib import Path
from typing import List

MIGRATION_MODULE_TMPL = '''\
"""
{description}
"""
name = {name!r}
dependencies = {dependencies!r}


def upgrade(db: "pymongo.database.Database"):
    pass


def downgrade(db: "pymongo.database.Database"):
    pass

'''
MAX_NAME_LEN = 60


def slugify(text: str) -> str:
    text = re.sub(r"[\W_]+", "_", text)
    text = text.encode("ascii", errors="skip").decode().lower()
    return text


def generate_migration_module(
    fp,
    name: str,
    description: str = "Migration description here!",
    dependencies: List[str] = (),
):
    dependencies = list(dependencies)

    content = MIGRATION_MODULE_TMPL.format(
        name=name, description=description, dependencies=dependencies
    )
    fp.write(content)


def generate_migration_module_in_dir(
    migration_dir: Path, name: str = "", description: str = "", *args, **kwargs
):
    now = datetime.datetime.utcnow()
    if not name:
        name = f"{now:%Y%m%H%M%s}"
        if description:
            name = f"{name}_{slugify(description)}"
        name = name[:MAX_NAME_LEN]
    with (migration_dir / f"{name}.py").open("w") as f:
        generate_migration_module(
            f, name=name, description=description, *args, **kwargs
        )
