# 3.0.0(2026-1-30)
## Release Summary
First documented version. Complete overhaul and new working implementation on Linux of the original engine, all of which is documented in the new `docs/DeveloperGuide.md` file to help future developers. Currently developed and tested on Linux Mint 22.2 only.

## Changes
- Removed original installation structure via **payload.sh**
- Updated README to match changes
- Scoring engine overhaul
- Configurator revamp
- ***NEW*** docs/DeveloperGuide.md

## Planned update
- Service testing(installing as a service via service_setup.py)
- Ubuntu Compatibility

### Note:
Please follow this format for future updates. Add any extra notes here.

#### Update By @joshkimchifriedrice
- Assisted by @naqibnetlab

# 3.0.1(2026-1-31)
## Release Summary
README and configurator changes to ensure smooth setup for new virtual machines

## Changes
- Removed service setup portion from configurator temporarily
- Updated README to change setup order to include service portion

#### Update By @joshkimchifriedrice

# 3.0.2(2026-2-2)
## Release Summary
Updated update check period and check hosts vulnerabilities to be more robust.

## Changes
- Added proper error handling to update check period
- Fixed "check hosts" to record a hit for a non-empty but default file(Linux Mint 22.2 compatible)

#### Update By @joshkimchifriedrice