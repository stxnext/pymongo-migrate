# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2023-06-30

### Added

- Official support for Python 3.11
- Add support for specifying database for migration while authenticating against different database #41

### Fixed

- Ensure that the generate command creates files that pass mypy checks #40

### Removed

- Removed support for Python 3.7 and older as they reach [End of Life](https://endoflife.date/python).

