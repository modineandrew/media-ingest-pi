"""LED strip controller for WS2812B progress indication."""

import threading
import time
from typing import Optional, Tuple


class LEDController:
    """Controller for WS2812B LED strip to display transfer progress."""
    
    def __init__(self, settings: dict):
        """Initialize LED controller.
        
        Args:
            settings: LED settings dictionary containing:
                - enabled: Whether LED strip is enabled
                - pin: GPIO pin number
                - led_count: Number of LEDs in strip
                - brightness: Brightness level (0-255)
                - idle_color: RGB tuple for idle state
                - progress_color: RGB tuple for progress indication
                - success_color: RGB tuple for successful completion
                - error_color: RGB tuple for errors
        """
        self.settings = settings
        self.enabled = settings.get('enabled', False)
        self._strip = None
        self._lock = threading.RLock()
        self._current_progress = 0
        self._animation_thread = None
        self._animation_running = False
        
        if self.enabled:
            try:
                self._init_strip()
            except Exception as e:
                print(f"Warning: Could not initialize LED strip: {e}")
                self.enabled = False
    
    def _init_strip(self):
        """Initialize the LED strip hardware."""
        try:
            from rpi_ws281x import PixelStrip, Color
            
            pin = self.settings.get('pin', 18)
            led_count = self.settings.get('led_count', 144)
            brightness = self.settings.get('brightness', 128)
            
            # Create NeoPixel object with appropriate configuration
            # Note: ws.SK6812_STRIP_RGBW for RGBW strips, ws.WS2812_STRIP for RGB
            self._strip = PixelStrip(
                led_count,
                pin,
                freq_hz=800000,
                dma=10,
                invert=False,
                brightness=brightness,
                channel=0
            )
            
            # Initialize the library (must be called once before other functions)
            self._strip.begin()
            
            # Set to idle state
            self.show_idle()
            
            print(f"✓ LED strip initialized: {led_count} LEDs on GPIO {pin}")
            
        except ImportError:
            print("Warning: rpi_ws281x library not found. LED support disabled.")
            print("Install with: sudo pip3 install rpi_ws281x")
            self.enabled = False
        except Exception as e:
            print(f"Error initializing LED strip: {e}")
            self.enabled = False
    
    def show_idle(self):
        """Display idle animation (breathing effect)."""
        if not self.enabled or not self._strip:
            return
        
        self._stop_animation()
        self._animation_running = True
        self._animation_thread = threading.Thread(target=self._idle_animation, daemon=True)
        self._animation_thread.start()
    
    def show_progress(self, percent: float):
        """Display progress as a percentage.
        
        Args:
            percent: Progress percentage (0-100).
        """
        if not self.enabled or not self._strip:
            return
        
        with self._lock:
            self._current_progress = max(0, min(100, percent))
            self._stop_animation()
            self._render_progress()
    
    def show_success(self, duration: float = 3.0):
        """Display success animation.
        
        Args:
            duration: Duration to show success animation in seconds.
        """
        if not self.enabled or not self._strip:
            return
        
        self._stop_animation()
        self._animation_running = True
        self._animation_thread = threading.Thread(
            target=self._success_animation, 
            args=(duration,), 
            daemon=True
        )
        self._animation_thread.start()
    
    def show_error(self, duration: float = 3.0):
        """Display error animation.
        
        Args:
            duration: Duration to show error animation in seconds.
        """
        if not self.enabled or not self._strip:
            return
        
        self._stop_animation()
        self._animation_running = True
        self._animation_thread = threading.Thread(
            target=self._error_animation, 
            args=(duration,), 
            daemon=True
        )
        self._animation_thread.start()
    
    def clear(self):
        """Turn off all LEDs."""
        if not self.enabled or not self._strip:
            return
        
        self._stop_animation()
        
        with self._lock:
            for i in range(self._strip.numPixels()):
                self._strip.setPixelColor(i, self._color(0, 0, 0))
            self._strip.show()
    
    def shutdown(self):
        """Clean shutdown of LED strip."""
        self._stop_animation()
        self.clear()
        print("LED strip controller shutdown")
    
    def _stop_animation(self):
        """Stop any running animation."""
        self._animation_running = False
        if self._animation_thread and self._animation_thread.is_alive():
            self._animation_thread.join(timeout=1)
    
    def _render_progress(self):
        """Render current progress state with smooth gradient fill."""
        if not self.enabled or not self._strip:
            return
        
        with self._lock:
            led_count = self._strip.numPixels()
            progress_color_rgb = self.settings.get('progress_color', [0, 255, 0])
            background_color = self._color(0, 0, 0)
            
            # Calculate progress position
            progress_position = (self._current_progress / 100.0) * led_count
            fully_lit_leds = int(progress_position)  # Number of fully lit LEDs
            partial_brightness = progress_position - fully_lit_leds  # Brightness of current LED (0.0-1.0)
            
            for i in range(led_count):
                if i < fully_lit_leds:
                    # Fully lit LED
                    self._strip.setPixelColor(i, self._color(*progress_color_rgb))
                elif i == fully_lit_leds and partial_brightness > 0:
                    # Partially lit LED (current position) - scale brightness
                    color = self._scale_color(progress_color_rgb, partial_brightness)
                    self._strip.setPixelColor(i, color)
                else:
                    # Unlit LED
                    self._strip.setPixelColor(i, background_color)
            
            self._strip.show()
    
    def _idle_animation(self):
        """Breathing animation for idle state."""
        idle_color_rgb = self.settings.get('idle_color', [0, 50, 255])
        
        while self._animation_running:
            # Breathe in
            for brightness in range(0, 255, 5):
                if not self._animation_running:
                    return
                
                color = self._scale_color(idle_color_rgb, brightness / 255.0)
                
                with self._lock:
                    for i in range(self._strip.numPixels()):
                        self._strip.setPixelColor(i, color)
                    self._strip.show()
                
                time.sleep(0.02)
            
            # Breathe out
            for brightness in range(255, 0, -5):
                if not self._animation_running:
                    return
                
                color = self._scale_color(idle_color_rgb, brightness / 255.0)
                
                with self._lock:
                    for i in range(self._strip.numPixels()):
                        self._strip.setPixelColor(i, color)
                    self._strip.show()
                
                time.sleep(0.02)
    
    def _success_animation(self, duration: float):
        """Pulse animation for successful completion."""
        success_color = self._get_color('success_color', (0, 255, 0))
        end_time = time.time() + duration
        
        # Fill with success color
        with self._lock:
            for i in range(self._strip.numPixels()):
                self._strip.setPixelColor(i, success_color)
            self._strip.show()
        
        # Pulse effect
        pulse_count = 0
        while self._animation_running and time.time() < end_time and pulse_count < 3:
            # Fade out
            for brightness in range(255, 0, -15):
                if not self._animation_running:
                    return
                
                color = self._scale_brightness(success_color, brightness / 255.0)
                
                with self._lock:
                    for i in range(self._strip.numPixels()):
                        self._strip.setPixelColor(i, color)
                    self._strip.show()
                
                time.sleep(0.02)
            
            # Fade in
            for brightness in range(0, 255, 15):
                if not self._animation_running:
                    return
                
                color = self._scale_brightness(success_color, brightness / 255.0)
                
                with self._lock:
                    for i in range(self._strip.numPixels()):
                        self._strip.setPixelColor(i, color)
                    self._strip.show()
                
                time.sleep(0.02)
            
            pulse_count += 1
        
        self._animation_running = False
        self.show_idle()
    
    def _error_animation(self, duration: float):
        """Flashing animation for errors."""
        error_color = self._get_color('error_color', (255, 0, 0))
        end_time = time.time() + duration
        
        flash_count = 0
        while self._animation_running and time.time() < end_time and flash_count < 6:
            # Flash on
            with self._lock:
                for i in range(self._strip.numPixels()):
                    self._strip.setPixelColor(i, error_color)
                self._strip.show()
            
            time.sleep(0.2)
            
            if not self._animation_running:
                return
            
            # Flash off
            with self._lock:
                for i in range(self._strip.numPixels()):
                    self._strip.setPixelColor(i, self._color(0, 0, 0))
                self._strip.show()
            
            time.sleep(0.2)
            flash_count += 1
        
        self._animation_running = False
        self.show_idle()
    
    def _get_color(self, key: str, default: Tuple[int, int, int]) -> int:
        """Get color from settings and convert to 24-bit value.
        
        Args:
            key: Settings key name.
            default: Default RGB tuple.
            
        Returns:
            24-bit color value.
        """
        rgb = self.settings.get(key, default)
        if isinstance(rgb, (list, tuple)) and len(rgb) >= 3:
            return self._color(rgb[0], rgb[1], rgb[2])
        return self._color(*default)
    
    def _color(self, r: int, g: int, b: int) -> int:
        """Create 24-bit color value from RGB components.
        
        Args:
            r: Red component (0-255).
            g: Green component (0-255).
            b: Blue component (0-255).
            
        Returns:
            24-bit color value.
        """
        return (r << 16) | (g << 8) | b
    
    def _scale_color(self, rgb: Tuple[int, int, int], scale: float) -> int:
        """Scale RGB color by a factor.
        
        Args:
            rgb: RGB tuple.
            scale: Scale factor (0.0-1.0).
            
        Returns:
            Scaled 24-bit color value.
        """
        r = int(rgb[0] * scale)
        g = int(rgb[1] * scale)
        b = int(rgb[2] * scale)
        return self._color(r, g, b)
    
    def _scale_brightness(self, color: int, scale: float) -> int:
        """Scale brightness of a 24-bit color.
        
        Args:
            color: 24-bit color value.
            scale: Scale factor (0.0-1.0).
            
        Returns:
            Scaled 24-bit color value.
        """
        r = int(((color >> 16) & 0xFF) * scale)
        g = int(((color >> 8) & 0xFF) * scale)
        b = int((color & 0xFF) * scale)
        return self._color(r, g, b)

