#!/usr/bin/env python3
"""Quick LED strip test script - Run with sudo"""

import sys
import time

print("LED Strip Test Script")
print("=" * 50)

# Test 1: Check if library is available
print("\n1. Checking rpi_ws281x library...")
try:
    from rpi_ws281x import PixelStrip, Color
    print("   ✓ Library found")
except ImportError as e:
    print(f"   ✗ Library not found: {e}")
    print("   Install with: sudo pip3 install rpi_ws281x")
    sys.exit(1)

# Test 2: Initialize strip
print("\n2. Initializing LED strip...")
LED_COUNT = 144        # Number of LED pixels (adjust to your strip)
LED_PIN = 18          # GPIO pin (BCM numbering)
LED_BRIGHTNESS = 128  # Brightness (0-255)

try:
    strip = PixelStrip(LED_COUNT, LED_PIN, brightness=LED_BRIGHTNESS)
    strip.begin()
    print(f"   ✓ Strip initialized ({LED_COUNT} LEDs on GPIO {LED_PIN})")
except Exception as e:
    print(f"   ✗ Initialization failed: {e}")
    print("\n   Troubleshooting:")
    print("   - Are you running with sudo?")
    print("   - Is GPIO 18 already in use?")
    print("   - Check wiring connections")
    sys.exit(1)

# Test 3: Light up LEDs
print("\n3. Testing LEDs...")
print("   This will cycle through: Red → Green → Blue → Off")

colors = [
    (Color(255, 0, 0), "Red"),
    (Color(0, 255, 0), "Green"),
    (Color(0, 0, 255), "Blue"),
]

try:
    for color, name in colors:
        print(f"   → {name}...", end='', flush=True)
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, color)
        strip.show()
        time.sleep(1.5)
        print(" OK")
    
    # Turn off
    print("   → Off...", end='', flush=True)
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()
    print(" OK")
    
    print("\n" + "=" * 50)
    print("✓ LED strip test PASSED!")
    print("\nIf you saw the colors, your hardware is working.")
    print("Make sure to enable the LED strip in the web settings.")
    print("=" * 50)

except KeyboardInterrupt:
    print("\n\nTest interrupted")
except Exception as e:
    print(f"\n   ✗ Test failed: {e}")
    sys.exit(1)
finally:
    # Cleanup
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()



