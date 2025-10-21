# LED Strip Progress Indicator - Quick Reference

## Visual States

```
🔵 IDLE (No Transfer)
████████████████████████████████████
Breathing blue animation
```

```
🟢 PROGRESS (25% Complete)
████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░
Green fill showing 25% progress
```

```
🟢 PROGRESS (75% Complete)
███████████████████████████░░░░░░░░░
Green fill showing 75% progress
```

```
✅ SUCCESS (Completed)
████████████████████████████████████
Pulsing green animation (3 times)
Then returns to idle
```

```
❌ ERROR (Failed)
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
Flashing red animation (6 times)
Then returns to idle
```

## Quick Settings Reference

| Setting | Default | Range | Description |
|---------|---------|-------|-------------|
| Enabled | `false` | `true`/`false` | Enable LED strip |
| GPIO Pin | `18` | `0-27` | BCM pin number |
| LED Count | `144` | `1-1000` | Number of LEDs |
| Brightness | `128` | `0-255` | Overall brightness |
| Idle Color | `[0,50,255]` | RGB | Blue breathing |
| Progress Color | `[0,255,0]` | RGB | Green fill bar |
| Success Color | `[0,255,0]` | RGB | Green pulse |
| Error Color | `[255,0,0]` | RGB | Red flash |

## Pin Reference (BCM Mode)

| BCM Pin | Physical Pin | Notes |
|---------|--------------|-------|
| GPIO 18 | Pin 12 | **Recommended** (Hardware PWM) |
| GPIO 12 | Pin 32 | Alternative PWM pin |
| GPIO 13 | Pin 33 | Alternative PWM pin |
| GPIO 19 | Pin 35 | Alternative PWM pin |

## Web UI Location

```
http://<raspberry-pi-ip>/settings
└── LED Strip Progress Indicator section
```

## Common Commands

```bash
# Restart service
sudo systemctl restart media-ingest

# View logs
sudo journalctl -u media-ingest -f

# Check status
sudo systemctl status media-ingest
```

## Power Requirements

| LED Count | Current @ Full Brightness | Recommended Supply |
|-----------|---------------------------|-------------------|
| 30 LEDs | ~1.8A | 5V 2A |
| 60 LEDs | ~3.6A | 5V 5A |
| 144 LEDs | ~8.6A | 5V 10A |
| 300 LEDs | ~18A | 5V 20A |

*At 50% brightness (128), divide current by ~2*

## Wiring Quick Reference

```
Pi GPIO 18 (Pin 12) ──► LED Data In
Pi GND (Any GND) ────┬─► LED GND
                     └─► Power Supply GND
Power Supply 5V ──────► LED 5V
```

**⚠️ IMPORTANT**: Common ground connection is required!

## Color Examples

| Color | RGB Values | Use Case |
|-------|------------|----------|
| Blue | `[0, 50, 255]` | Default idle |
| Cyan | `[0, 255, 255]` | Alternative idle |
| Green | `[0, 255, 0]` | Progress/Success |
| Yellow | `[255, 255, 0]` | Warning |
| Orange | `[255, 128, 0]` | Alternative warning |
| Red | `[255, 0, 0]` | Error |
| Purple | `[128, 0, 255]` | Alternative idle |
| White | `[255, 255, 255]` | High power usage! |

## Troubleshooting Quick Tips

| Problem | Solution |
|---------|----------|
| No lights | Check power supply, verify ground connection |
| Flickering | Reduce brightness, check power supply capacity |
| Wrong colors | Check data line connection, verify pin number |
| Only first LED works | Check if connected to DIN (not DOUT) |
| Permission errors | Service must run as root (handled by systemd) |

## Configuration File Location

Settings are stored in:
```
/home/<user>/media-ingest-pi/config/settings.yaml
```

Example LED section:
```yaml
led:
  enabled: true
  pin: 18
  led_count: 144
  brightness: 128
  idle_color: [0, 50, 255]
  progress_color: [0, 255, 0]
  success_color: [0, 255, 0]
  error_color: [255, 0, 0]
```

## Safety Checklist

- [ ] Power supply matches LED count requirements
- [ ] Common ground connected between Pi and power supply
- [ ] 5V NOT connected directly to Pi
- [ ] Data line connected to correct GPIO pin
- [ ] All connections are secure
- [ ] LED strip polarity is correct (check DIN/DOUT arrows)

## Performance Tips

1. **Lower brightness**: 64-128 is usually plenty bright indoors
2. **Shorter strips**: Easier to power and more responsive
3. **Quality power**: Use a good quality 5V supply
4. **Short wires**: Keep data line short (< 1 meter if possible)
5. **Add resistor**: 470Ω on data line improves reliability

## Animation Timing

| State | Duration | Loop |
|-------|----------|------|
| Idle breathing | ~4 seconds | Continuous |
| Progress update | Immediate | Per file |
| Success pulse | 3 seconds | Once |
| Error flash | 3 seconds | Once |

