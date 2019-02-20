"""Draw migrations graph"""

from io import StringIO
from typing import TextIO

from pymongo_migrate.migrations import MigrationsGraph


def dump(graph: MigrationsGraph, output_file: TextIO):
    output_file.write("// Migrations\n")
    output_file.write("digraph {\n")
    for migration in graph.migrations.values():
        for dependency_name in migration.dependencies:
            dependency = graph.migrations[dependency_name]
            output_file.write(f"\t{dependency.name!r} -> {migration.name!r}\n")
    output_file.write("}\n")


def dumps(graph: MigrationsGraph) -> str:
    with StringIO() as f:
        dump(graph, f)
        return f.getvalue()
