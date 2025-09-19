# Changelog

## [Unreleased]
### Changed
- Inlined Docker Compose environment configuration so the stack runs without a `.env` file.
- Added an explicit `server.utility` package initializer to guarantee direct imports succeed.

## [0.1.0] - 2025-02-14
### Added
- Initial implementation of the MCP human handoff server with Flask UI and in-memory TTL question storage.
- Docker and packaging assets, including Docker Compose workflow.
- Automated tests for MCP tools, Flask routes, and utility helpers.

