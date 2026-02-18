"""
小愛同學 Hotkey Launcher with System Tray + Voice Wake Feature
Hold F5 key for 1 second to launch 小愛同學
Voice Wake: Say "Xiao Ai" (English), "小爱同学" (Chinese Simplified), or "小愛同學" (Cantonese)
Right-click tray icon to close
"""

import keyboard
import subprocess
import sys
import threading
import time
import argparse
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import speech_recognition as sr
from difflib import SequenceMatcher
import pyautogui  # For auto-clicking voice button

f5_press_time = None
f5_hold_triggered = False
voice_listener_active = True
voice_wake_enabled = True  # Toggle for voice wake feature
icon_instance = None  # Global icon reference for menu updates

# Voice Wake Words Configuration
WAKE_WORDS = {
    'en': ['xiao ai', 'xiaoai'],  # English
    'zh-CN': ['小爱同学', '小爱'],  # Chinese Simplified
    'yue': ['小愛同學', '小愛']  # Cantonese
}

class VoiceWakeListener:
    """Listen for voice wake words in multiple languages"""
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = True
        self.confidence_threshold = 0.7  # Minimum confidence for wake detection
        self.stop_event = threading.Event()  # Event to stop listening immediately
        
    def similarity(self, a, b):
        """Calculate string similarity ratio (0-1)"""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def check_wake_word(self, recognized_text):
        """Check if recognized text matches any wake word"""
        if not recognized_text:
            return False
        
        recognized_text = recognized_text.lower().strip()
        
        for language, words in WAKE_WORDS.items():
            for wake_word in words:
                wake_word_lower = wake_word.lower()
                
                # Exact match
                if wake_word_lower in recognized_text:
                    return True
                
                # Fuzzy match (for handling slight speech recognition errors)
                similarity = self.similarity(recognized_text, wake_word_lower)
                if similarity >= self.confidence_threshold:
                    return True
        
        return False
    
    def listen_for_wake_word(self):
        """Continuous listening for wake words"""
        print("🎤 Voice Wake Listener started...")
        
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("🎤 Listening for wake words: 'Xiao Ai', '小爱同学', '小愛同學'...")
        
        while self.is_listening and not self.stop_event.is_set():
            try:
                with self.microphone as source:
                    # Listen for audio with timeout of 5 seconds
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
                
                # Check if stop was requested while listening
                if self.stop_event.is_set():
                    return False
                    
                try:
                    # Try English first
                    text_en = self.recognizer.recognize_google(audio, language='en-US')
                    print(f"🎤 English: {text_en}")
                    
                    if self.check_wake_word(text_en):
                        print("✅ English wake word detected!")
                        return True
                        
                except sr.UnknownValueError:
                    pass
                
                try:
                    # Try Chinese (Simplified and Cantonese)
                    text_zh = self.recognizer.recognize_google(audio, language='zh-CN')
                    print(f"🎤 Chinese: {text_zh}")
                    
                    if self.check_wake_word(text_zh):
                        print("✅ Chinese wake word detected!")
                        return True
                        
                except sr.UnknownValueError:
                    pass
                
            except sr.RequestError as e:
                print(f"⚠️ API Error: {e}")
                time.sleep(2)
            except sr.UnknownValueError:
                pass
            except Exception as e:
                if self.is_listening:  # Only print if still listening
                    continue
        
        return False
    
    def stop(self):
        """Stop the voice listener"""
        self.is_listening = False
        print("🎤 Voice Wake Listener stopped")

# Initialize voice listener
voice_listener = VoiceWakeListener()


def open_xiaoai():
    try:
        # Use the correct AppID found on the system
        app_id = "8497DDF3.639A2791C9AB_kf545nqv09rxe!App"
        subprocess.Popen(f'explorer.exe shell:appsFolder\\{app_id}', shell=True)
        print("🚀 Launched 小愛同學")
        
        # Auto-click voice button after app opens (if enabled)
        if AUTO_CLICK_ENABLED:
            auto_click_thread = threading.Thread(target=auto_click_voice_button, daemon=True)
            auto_click_thread.start()
    except Exception as e:
        print("Error:", e)

def auto_click_voice_button():
    """Automatically click the voice input button after app opens"""
    try:
        time.sleep(2.5)  # Wait for app to fully load
        
        # Get screen size for responsive positioning
        screen_width, screen_height = pyautogui.size()
        
        # Voice icon position (colorful circle icon on the left side)
        # Adjust these percentages based on your screen resolution
        voice_x = int(screen_width * 0.225)  # ~43% of screen width
        voice_y = int(screen_height * 0.388)  # ~38% of screen height
        
        print(f"🎤 Auto-clicking voice button at ({voice_x}, {voice_y})")
        pyautogui.click(x=voice_x, y=voice_y)
        print("✅ Voice input button clicked")
    except ImportError:
        print("⚠️ PyAutoGUI not installed. Install with: pip install pyautogui")
    except Exception as e:
        print(f"⚠️ Auto-click failed: {e}")

def on_f5_press():
    """Called when F5 is pressed down"""
    global f5_press_time, f5_hold_triggered
    f5_press_time = time.time()
    f5_hold_triggered = False
    print("⏳ Hold F5 for 1 second to open 小愛同學...")
    
    # Start monitoring in background thread
    def monitor_f5_hold():
        global f5_hold_triggered
        start_time = f5_press_time
        hold_duration = 1.0
        
        # Monitor for exactly 1 second
        while time.time() - start_time < hold_duration:
            if not keyboard.is_pressed('F5'):
                # Key was released before 1 second - do nothing
                return
            time.sleep(0.05)
        
        # F5 was held for 1 second - launch ONCE
        if keyboard.is_pressed('F5') and not f5_hold_triggered:
            f5_hold_triggered = True
            open_xiaoai()
            print("✅ F5 held for 1 second - Launching 小愛同學")
    
    monitor_thread = threading.Thread(target=monitor_f5_hold, daemon=True)
    monitor_thread.start()

def on_f5_release():
    """Called when F5 is released"""
    global f5_press_time, f5_hold_triggered
    f5_press_time = None

def toggle_voice_wake(icon=None, item=None):
    """Toggle voice wake feature on/off"""
    global voice_wake_enabled
    voice_wake_enabled = not voice_wake_enabled
    status = "✅ ENABLED" if voice_wake_enabled else "❌ DISABLED"
    print(f"🎤 Voice Wake {status}")
    
    # Reset the stop event when enabling, set it when disabling
    if voice_wake_enabled:
        voice_listener.stop_event.clear()
    else:
        voice_listener.stop_event.set()
    
    update_tray_menu()

def update_tray_menu():
    """Update system tray menu with current voice wake status"""
    global icon_instance
    if icon_instance:
        voice_status = "✅ Voice Wake: ON" if voice_wake_enabled else "❌ Voice Wake: OFF"
        menu = Menu(
            MenuItem('🚀 小愛同學 Launcher', lambda: None, enabled=False),
            MenuItem('📌 Hold F5 for 1 second', lambda: None, enabled=False),
            MenuItem(voice_status, toggle_voice_wake),
            MenuItem('Stop launcher', stop_program),
        )
        icon_instance.menu = menu

def stop_program(icon=None, item=None):
    global voice_listener, voice_listener_active
    print("\n⛔ Stopping the launcher...")
    
    # Stop voice listener thread
    voice_listener_active = False
    voice_listener.stop()
    
    # Unregister keyboard listener
    try:
        keyboard.unhook_all()
    except:
        pass
    
    # Stop the tray icon
    try:
        icon.stop()
    except:
        pass
    
    print("✅ Launcher closed completely")
    import os
    os._exit(0)  # Force exit to ensure complete shutdown

def create_icon():
    """Create a simple tray icon"""
    # Create a simple image (32x32 blue square)
    img = Image.new('RGB', (32, 32), color='blue')
    draw = ImageDraw.Draw(img)
    draw.text((5, 5), "AI", fill='white')
    return img

# Parse command-line arguments
import argparse
parser = argparse.ArgumentParser(description='小愛同學 Launcher with Voice Wake')
parser.add_argument('--no-voice', action='store_true', help='Disable voice wake feature on startup')
parser.add_argument('--no-auto-click', action='store_true', help='Disable auto-click voice button on app launch')
args = parser.parse_args()

# Global flag for auto-click
AUTO_CLICK_ENABLED = not args.no_auto_click

if args.no_voice:
    voice_wake_enabled = False
    voice_listener.stop_event.set()
    print("⚠️ Voice Wake Feature DISABLED (use --no-voice flag to disable)")

# Register F5 key events
keyboard.on_press_key('f5', lambda _: on_f5_press())
keyboard.on_release_key('f5', lambda _: on_f5_release())

# Create tray menu
voice_status = "✅ Voice Wake: ON" if voice_wake_enabled else "❌ Voice Wake: OFF"
menu = Menu(
    MenuItem('🚀 小愛同學 Launcher', lambda: None, enabled=False),
    MenuItem('📌 Hold F5 for 1 second', lambda: None, enabled=False),
    MenuItem(voice_status, toggle_voice_wake),
    MenuItem('Stop launcher', stop_program),
)

# Create system tray icon
icon = Icon("XiaoiLauncher", create_icon(), menu=menu)
icon_instance = icon

print("=" * 50)
print("✅ 小愛同學 Launcher is running!")
print("=" * 50)
print("📌 HOLD F5 key for 1 second to launch 小愛同學")
if voice_wake_enabled:
    print("🎤 Voice Wake: ENABLED")
    print("   Say: \"Xiao Ai\" / \"小爱同学\" / \"小愛同學\"")
else:
    print("🎤 Voice Wake: DISABLED")
    print("   (Right-click tray menu to enable)")
print("📌 Right-click tray icon (bottom right) for menu")
if AUTO_CLICK_ENABLED:
    print("🖱️  Auto-Click: ENABLED (voice button auto-clicks)")
else:
    print("🖱️  Auto-Click: DISABLED")
print("=" * 50)
print()

# Start voice wake listener in separate thread
def voice_wake_thread():
    """Background thread for voice wake listening"""
    while voice_listener_active:
        try:
            # Only listen if voice wake is enabled
            if voice_wake_enabled:
                if voice_listener.listen_for_wake_word():
                    open_xiaoai()
            else:
                # Sleep briefly when disabled to reduce CPU usage
                time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Voice listener error: {e}")
            time.sleep(2)

voice_thread = threading.Thread(target=voice_wake_thread, daemon=True)
voice_thread.start()

# Run icon in separate thread
tray_thread = threading.Thread(target=icon.run, daemon=True)
tray_thread.start()

print("\n💡 TIP: Right-click the tray icon to toggle Voice Wake ON/OFF")
print("    Or start with:")
print("    • python xiaoi_launcher.py --no-voice")
print("    • python xiaoi_launcher.py --no-auto-click")
print("    • python xiaoi_launcher.py --no-voice --no-auto-click")

# Keep the script alive
try:
    keyboard.wait()
except KeyboardInterrupt:
    voice_listener.stop()
    sys.exit(0)
