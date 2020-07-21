import datetime
import re
from pathlib import Path
from typing import List, Optional

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
    text = text.encode("ascii", errors="ignore").decode().lower()
    text = text.strip("_")
    return text


def generate_migration_module(
    fp,
    name: str,
    description: str = "Migration description here!",
    dependencies: Optional[List[str]] = None,
):
    dependencies = dependencies or []

    content = MIGRATION_MODULE_TMPL.format(
        name=name, description=description, dependencies=dependencies
    )
    fp.write(content)


def generate_migration_module_in_dir(
    migration_dir: Path, name: str = "", *args, **kwargs
) -> Path:
    now = datetime.datetime.utcnow()
    if not name:
        name = f"{now:%Y%m%d%H%M%S}"
        description = kwargs.get("description")
        if description:
            name = f"{name}_{slugify(description)}"
        name = name[:MAX_NAME_LEN]
    file_path = migration_dir / f"{name}.py"
    if file_path.exists():
        raise FileExistsError(f"{file_path} already exists")

    with file_path.open("w") as f:
        generate_migration_module(f, name=name, *args, **kwargs)  # type: ignore
    return file_path
