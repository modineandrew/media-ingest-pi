# Pre-Release Checklist

Before making the repository public, go through this checklist:

## 📸 Screenshots
- [ ] Add `dashboard.png` to the `screenshots/` directory
- [ ] Add `devices.png` to the `screenshots/` directory  
- [ ] Add `history.png` to the `screenshots/` directory
- [ ] Remove or update `screenshots/README.md` if needed

## 📝 Documentation
- [ ] Review README.md for accuracy
- [ ] Check that all GitHub links point to `bscholer/media-ingest-pi` (should be done)
- [ ] Verify installation instructions are clear
- [ ] Review CONTRIBUTING.md
- [ ] Check LICENSE file is appropriate

## 🔧 Configuration
- [ ] Ensure `config/settings.example.yaml` exists (should be present)
- [ ] Ensure `config/devices.example.yaml` exists (should be present)
- [ ] Verify that actual config files (`settings.yaml`, `devices.yaml`) are in `.gitignore` (should be done)
- [ ] Test that the app creates default configs on first run

## 🧪 Testing
- [ ] Test the one-liner installer on a fresh Raspberry Pi
- [ ] Test manual installation process
- [ ] Verify web interface loads correctly
- [ ] Test creating a device profile through the UI
- [ ] Test modifying settings through the UI
- [ ] Test USB device detection (if possible)
- [ ] Verify systemd service starts correctly
- [ ] Check logs for any errors

## 🔒 Security
- [ ] Remove any sensitive data from config files in repo
- [ ] Verify no hardcoded passwords or tokens
- [ ] Check that database files are gitignored (should be done)
- [ ] Review systemd service security settings

## 🎨 Polish
- [ ] Check for any TODO comments in code
- [ ] Remove any debug print statements
- [ ] Ensure code is well-commented
- [ ] Verify all functions have docstrings
- [ ] Check for consistent code style

## 📦 Repository Setup (GitHub)
- [ ] Enable GitHub Discussions (for community support)
- [ ] Add repository topics/tags (raspberry-pi, python, flask, media-management, usb, sd-card, home-assistant, mqtt)
- [ ] Set repository description
- [ ] Add a website link (if you have documentation hosted elsewhere)
- [ ] Set up GitHub Pages (optional, for documentation)
- [ ] Configure repository settings (issues, discussions, etc.)

## 🚀 Release
- [ ] Create a release/tag (e.g., v1.0.0)
- [ ] Write release notes
- [ ] Test the installer URL works correctly
- [ ] Share on relevant communities (r/homeassistant, r/raspberry_pi, etc.)

## ✅ Final Checks
- [ ] Run `bash -n install.sh` to check syntax (should pass)
- [ ] Verify all links work in README
- [ ] Check that issue templates work on GitHub
- [ ] Test pull request template
- [ ] Review all files for typos

---

**Note**: Most items in this checklist have already been completed. Focus on screenshots, testing, and repository setup on GitHub!



