# pymongo-migrate

[![Build Status](https://travis-ci.org/stxnext/pymongo-migrate.svg?branch=master)](https://travis-ci.org/stxnext/pymongo-migrate)

Mongodb migrations using Python.

Since mongodb is schema-less most of the time you can do without data migrations.
Sometimes tho you want to create some new entities, or migrate old data instead adding another IF statement to your code.
This is where `pymongo-migrate` comes in.

## Alternatives

ATM there seem only two active python projects like this:
 * https://github.com/DoubleCiti/mongodb-migrations
 * https://github.com/skynyrd/cikilop
 
So if something already existed, why then another project?

Goals of this project, where at least one of them were not fullfilled by above:
 * tests and CI pipeline for ensuring that tool indeed works
 * keeping it usable both as standalone tool and as python dependency
 * use of modern Python version

## Inspiration and design

Other than Alternatives mentioned above, both `alembic` and `django` were used as references when designing this tool.

For now only linear revision history is supported.
The support for squash migrations is planned.
