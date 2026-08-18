## Why

The managed Python host currently accepts only one parser request per process, while service installation assumes the Python package and native service always share a release number. Batching parser work and discovering independently released compatible services removes unnecessary process pressure and allows each repository to release on its own cadence.

## What Changes

- Add a typed batch-inspection host operation that returns one ordered parser result per requested commit message while retaining one-request process isolation.
- Change remote installation and upgrade to discover the newest published stable native-service release whose protocol and schema exactly match the Python client's supported values.
- Keep explicit, configured, packaged, and PATH binary sources ahead of remote discovery.
- Continue verifying strict release manifests, platform coverage, artifact size, SHA-256, native identity, staged host assembly, and replacement health before activation.
- Record independent Python host and native binary versions in the managed runtime instead of requiring equal version text.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `python-extensions`: Add deterministic typed batch inspection for service-side attention selection.
- `service-management`: Replace exact Python-version release lookup with newest-compatible stable native release discovery and independent runtime version metadata.

## Impact

This changes the extension-host protocol implementation, GitHub release discovery, runtime metadata, service installation and upgrade behavior, and their public verification surfaces. It coordinates with the native `zmem-cache` change of the same name, which owns supervision, deadlines, caching, and transactional application.
