---
name: Bug Report
about: Report a bug or issue with Media Ingest Pi
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description
A clear and concise description of what the bug is.

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. Plug in device '...'
4. See error

## Expected Behavior
A clear and concise description of what you expected to happen.

## Actual Behavior
A clear and concise description of what actually happened.

## Environment
- **Device**: (e.g., Raspberry Pi 4 Model B, 4GB RAM)
- **OS**: (e.g., Raspberry Pi OS 12 Bookworm)
- **Python Version**: (output of `python3 --version`)
- **Media Ingest Pi Version**: (git commit hash or release version)
- **Installation Method**: (systemd service / manual)

## Configuration
Please provide relevant parts of your configuration (remove sensitive info):

```yaml
# config/settings.yaml
# Paste relevant sections here
```

## Logs
Please provide relevant logs:

```
# If running as service:
sudo journalctl -u media-ingest -n 50

# If running manually:
# Paste console output here
```

## Screenshots
If applicable, add screenshots to help explain your problem.

## Additional Context
Add any other context about the problem here.



