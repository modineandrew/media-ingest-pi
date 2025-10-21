# WS2812B LED Strip Setup Guide

This guide will help you set up an addressable LED strip for visual progress indication.

## Hardware Requirements

- **LED Strip**: WS2812B, WS2811, SK6812, or compatible addressable LED strip
- **Power Supply**: 5V DC power supply (capacity depends on LED count)
  - Calculate: ~60mA per LED at full white brightness
  - Example: 144 LEDs × 60mA = 8.64A → use a 10A 5V supply
  - For lower brightness (128/255), you can use a smaller supply
- **Wiring**: 
  - Data line from LED strip → GPIO 18 (Physical Pin 12) on Raspberry Pi
  - Ground from LED power supply → Ground on Raspberry Pi (common ground)
  - 5V from power supply → 5V on LED strip (NOT the Pi's 5V!)

## Wiring Diagram

```
Raspberry Pi                    LED Strip
┌─────────────┐                ┌──────────┐
│             │                │          │
│  GPIO 18 ───┼────────────────┤ DATA IN  │
│  (Pin 12)   │                │          │
│             │                │          │
│  GND     ───┼────┬───────────┤ GND      │
│  (Pin 6)    │    │           │          │
└─────────────┘    │           └──────────┘
                   │
        Power Supply (5V)
        ┌──────────────┐
        │              │
        │   5V   ──────┼────────────┤ 5V
        │   GND  ──────┘
        │              │
        └──────────────┘
```

## Important Wiring Notes

1. **Common Ground**: Always connect the ground of your power supply to the Raspberry Pi ground
2. **Don't power from Pi**: Don't connect the LED strip's 5V directly to the Pi's 5V pin (unless you have very few LEDs, < 10)
3. **Data Line**: The data line goes directly from the Pi's GPIO to the LED strip
4. **Level Shifting** (optional): For long runs or reliability, consider a 3.3V → 5V level shifter for the data line

## Pin Configuration

The default configuration uses:
- **GPIO 18** (BCM numbering) = **Physical Pin 12**

You can change this in the settings, but GPIO 18 is recommended as it supports hardware PWM.

## Compatible GPIO Pins

The following GPIO pins support PWM for LED control:
- GPIO 18 (Pin 12) - **Recommended**
- GPIO 12 (Pin 32) - Alternative
- GPIO 13 (Pin 33) - Alternative
- GPIO 19 (Pin 35) - Alternative

## Software Setup

The LED strip support is already included in the requirements. If you need to install manually:

```bash
sudo pip3 install rpi-ws281x
```

**Important**: The WS2812B library requires root access to `/dev/mem` for precise timing control. The service is configured to run as root automatically when installed via the install script. If you installed manually, ensure the systemd service file has `User=root` and `Group=root`.

## Configuration

1. Navigate to the **Settings** page in the web interface
2. Scroll to the **LED Strip Progress Indicator** section
3. Configure:
   - **Enable LED Strip**: Check to enable
   - **GPIO Pin**: 18 (or your chosen pin)
   - **Number of LEDs**: Enter your strip's LED count
   - **Brightness**: Adjust 0-255 (128 is a good starting point)
   - **Colors**: Customize the RGB colors for different states

4. Click **Save Settings**
5. Restart the service for changes to take effect:
   ```bash
   sudo systemctl restart media-ingest
   ```

## LED Animations

The LED strip displays different animations based on the system state:

### Idle State
- **Color**: Blue (default)
- **Animation**: Breathing effect
- **When**: No active transfers

### Progress
- **Color**: Green (default)
- **Animation**: Fill bar from left to right
- **When**: File transfer in progress
- **Shows**: Percentage of files transferred

### Success
- **Color**: Green (default)
- **Animation**: Pulsing effect (3 pulses)
- **When**: Transfer completed successfully
- **Duration**: 3 seconds, then returns to idle

### Error
- **Color**: Red (default)
- **Animation**: Flashing effect (6 flashes)
- **When**: Transfer failed or error occurred
- **Duration**: 3 seconds, then returns to idle

## Troubleshooting

### LEDs don't light up
1. Check power supply is connected and turned on
2. Verify common ground connection
3. Check GPIO pin number matches your wiring
4. Ensure service is running with sufficient privileges: `sudo systemctl status media-ingest`
5. Check data line connection - try wiggling the connector

### LEDs flicker or show wrong colors
1. Reduce brightness in settings
2. Check power supply capacity
3. Add a 470Ω resistor on the data line (between Pi and LED strip)
4. Add a large capacitor (1000µF) across power supply terminals

### Only first LED works
1. Check if data line is connected to "DIN" (not "DOUT")
2. Verify LED strip is not damaged
3. Check voltage at the strip (should be ~5V)

### Permission errors
**Solution**: The service needs to run as root for GPIO/LED access. Check your service file:
```bash
# Verify service is running as root
sudo systemctl cat media-ingest | grep "User="
# Should show: User=root

# If not, update the service file
sudo nano /etc/systemd/system/media-ingest.service
# Change: User=<your-user> to User=root
# Change: Group=<your-group> to Group=root
# Save, then:
sudo systemctl daemon-reload
sudo systemctl restart media-ingest
```

## Customization Tips

- **Adjust brightness**: Lower brightness (64-128) is often more pleasant and uses less power
- **Longer strips**: Use multiple power injection points for strips longer than 2 meters
- **Different colors**: Experiment with RGB values in the settings for your preferred look
- **Multiple projects**: Different transfer jobs can all use the same LED strip

## Safety Notes

- Always use an appropriately rated power supply
- Don't exceed the LED strip's current rating
- Ensure proper ventilation if strip gets warm
- Use proper gauge wire for power connections
- Double-check all connections before powering on

## Example Configurations

### Small Strip (30 LEDs)
- Power: 5V 2A power supply
- Brightness: 128-255
- Can power from USB power supply

### Medium Strip (60-144 LEDs)
- Power: 5V 5-10A power supply
- Brightness: 64-128
- Use dedicated power supply

### Large Strip (144+ LEDs)
- Power: 5V 10A+ power supply
- Brightness: 32-128
- Consider multiple power injection points
- May need level shifter for data line

## Additional Resources

- [WS2812B Datasheet](https://cdn-shop.adafruit.com/datasheets/WS2812B.pdf)
- [rpi_ws281x Library Documentation](https://github.com/rpi-ws281x/rpi-ws281x-python)
- [Raspberry Pi GPIO Pinout](https://pinout.xyz/)

## Need Help?

If you encounter issues:
1. Check the service logs: `sudo journalctl -u media-ingest -f`
2. Verify wiring against the diagram
3. Test with a minimal LED count first (e.g., 8 LEDs)
4. Open an issue on GitHub with details about your setup

