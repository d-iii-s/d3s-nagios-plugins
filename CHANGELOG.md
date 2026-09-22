# D3S Nagios Plugins change log

All notable changes to D3S Nagios Plugins will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Fixed

### Added

* `check_sssd` for checking SSSD domain status

### Changed

### Deprecated

### Removed


## v2.0.1 - 2026-08-13

### Fixed

* `os_updates`: correctly print amount of updatable packages


## v2.0.0 - 2026-08-13

### Added

* Add basic unit tests
* Argument processing for plugins
* `os_updates`: support for CentOS
* `os_updates`: parameters for limits
* `os_updates`: set status based on amount of security updates
* CI: run pytest suite

### Changed

* Get Fedora EOL from endoflife.date API
* `os_updates` can trigger earlier (when security updates are available)


## v1.0.4 - 2025-08-01

### Added

* SPEC file for RPM packages
* Add setup.py for backwards compatibility

## v1.0.3 - 2025-08-01

* Testing release

## v1.0.2 - 2025-08-01

* Testing release

## v1.0.1 - 2024-03-20

### Fixed

* Release script (@vhotspur)

## v1.0.0 - 2024-03-20

### Changed

* Packaging setup (@vhotspur)
* Move changelog to a more structured format (@vhotspur)

### Added

* Automated releases (@vhotspur)
