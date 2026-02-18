"""
小愛同學 Hotkey Launcher with System Tray + Voice Wake + Calibration
- 語音喚醒更快速、更靈敏
- 每次喚醒（語音或 F5）只點擊語音按鈕一次
- 點擊後保持監聽狀態（實際持續時間取決於小愛同學 App）
"""

import keyboard
import subprocess
import sys
import threading
import time
import json
from pathlib import Path
import argparse
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import speech_recognition as sr
from difflib import SequenceMatcher
import pyautogui
import pygetwindow as gw
from pynput.mouse import Controller as MouseController

# ───────────────────────────────────────────────
#  全域設定
# ───────────────────────────────────────────────

CACHE_FILE = Path("button_locations.json")

f5_press_time = None
f5_hold_triggered = False
voice_listener_active = True
voice_wake_enabled = True
icon_instance = None
AUTO_CLICK_ENABLED = True

WAKE_WORDS = {
    'en': ['xiao ai', 'xiaoai'],
    'zh-CN': ['小爱同学', '小爱', '小爱', '小艾'],
    'yue': ['小愛同學', '小愛']
}

VOICE_BUTTON_POS = None     # (x, y)

# 鎖鼠相關
mouse_controller = MouseController()
lock_active = False
lock_thread = None

# ───────────────────────────────────────────────
#  位置快取管理（不變）
# ───────────────────────────────────────────────

def load_cached_position():
    global VOICE_BUTTON_POS
    if not CACHE_FILE.exists():
        return False
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if "voice_button" in data and "coords" in data["voice_button"]:
            VOICE_BUTTON_POS = tuple(data["voice_button"]["coords"])
            print(f"已載入快取位置：{VOICE_BUTTON_POS}")
            return True
    except Exception as e:
        print(f"讀取快取失敗：{e}")
    return False


def save_position(coords):
    try:
        data = {
            "voice_button": {
                "coords": list(coords),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "screen_size": list(pyautogui.size())
            }
        }
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"位置已儲存至 {CACHE_FILE}")
    except Exception as e:
        print(f"儲存位置失敗：{e}")


def calibrate_voice_button():
    global VOICE_BUTTON_POS

    print("\n" + "="*70)
    print("🎯  小愛同學 語音按鈕位置校準")
    print("請先開啟小愛同學 App，並確保視窗顯示正常")
    print("="*70)
    print("1. 將滑鼠游標移動到 語音輸入按鈕（左側彩色圓圈）的正中央")
    print("2. 按下 'c' 鍵 確認位置")
    print("3. 按下 'q' 鍵 取消/跳過")
    print("="*70 + "\n")

    from pynput import keyboard as kb_listener
    recorded = [None]

    def on_press(key):
        try:
            if key.char == 'c':
                recorded[0] = pyautogui.position()
                print(f"\n確認位置：{recorded[0]}")
                return False
            if key.char == 'q':
                print("\n已取消校準")
                return False
        except AttributeError:
            pass

    print("正在監聽鍵盤... (c = 確認, q = 取消)")
    with kb_listener.Listener(on_press=on_press) as listener:
        while listener.is_alive():
            time.sleep(0.1)

    if recorded[0]:
        VOICE_BUTTON_POS = recorded[0]
        save_position(VOICE_BUTTON_POS)
        return True
    return False


# ───────────────────────────────────────────────
#  強制激活小愛同學視窗
# ───────────────────────────────────────────────

def activate_xiaoai_window(max_tries=5, wait_per_try=0.6):
    for attempt in range(1, max_tries + 1):
        try:
            windows = gw.getWindowsWithTitle("小爱") or \
                      gw.getWindowsWithTitle("XiaoAi") or \
                      gw.getWindowsWithTitle("小愛同學") or \
                      gw.getWindowsWithTitle("xiaoi")

            if not windows:
                time.sleep(wait_per_try)
                continue

            win = windows[0]
            if win.isMinimized:
                win.restore()
            win.activate()
            time.sleep(0.3)

            if is_xiaoai_window_active():
                print(f"成功激活小愛同學視窗")
                return True

            time.sleep(wait_per_try)

        except:
            pass

    print("無法自動激活小愛視窗，請手動點擊")
    return False


# ───────────────────────────────────────────────
#  單次點擊 + 短暫鎖鼠
# ───────────────────────────────────────────────

def lock_mouse_at(x, y):
    global lock_active
    while lock_active:
        try:
            cx, cy = mouse_controller.position
            if abs(cx - x) > 8 or abs(cy - y) > 8:
                mouse_controller.position = (x, y)
            time.sleep(0.005)
        except:
            time.sleep(0.02)


def auto_click_voice_button(lock_seconds=1.0):
    global VOICE_BUTTON_POS, lock_active, lock_thread

    if not AUTO_CLICK_ENABLED:
        return

    try:
        print("\n[單次點擊] 開始...")

        time.sleep(0.6)  # 稍微縮短等待時間

        activate_xiaoai_window()

        if not is_xiaoai_window_active():
            print("⚠️ 目前最前視窗不是小愛同學，跳過點擊")
            return

        if VOICE_BUTTON_POS is None:
            w, h = pyautogui.size()
            x = int(w * 0.225)
            y = int(h * 0.388)
        else:
            x, y = VOICE_BUTTON_POS

        lock_active = True
        lock_thread = threading.Thread(target=lock_mouse_at, args=(x, y), daemon=True)
        lock_thread.start()

        pyautogui.moveTo(x, y, duration=0.0)
        pyautogui.click()
        print("已單次點擊語音按鈕")

        time.sleep(lock_seconds)
        lock_active = False
        if lock_thread and lock_thread.is_alive():
            lock_thread.join(timeout=0.3)

        print("滑鼠控制已恢復，進入持續監聽模式（取決於 App）")

    except Exception as e:
        print(f"自動點擊失敗：{e}")
        lock_active = False


def is_xiaoai_window_active():
    try:
        active = gw.getActiveWindow()
        if not active:
            return False
        title = (active.title or "").lower()
        return any(x in title for x in ["小爱", "xiaoai", "xiaoi", "小愛同學"])
    except:
        return False


def open_xiaoai():
    try:
        app_id = "8497DDF3.639A2791C9AB_kf545nqv09rxe!App"
        subprocess.Popen(f'explorer.exe shell:appsFolder\\{app_id}', shell=True)
        print("已嘗試啟動 小愛同學")

        time.sleep(1.0)

        if AUTO_CLICK_ENABLED:
            activate_xiaoai_window()
            threading.Thread(target=auto_click_voice_button, args=(1.0,), daemon=True).start()

    except Exception as e:
        print(f"啟動失敗：{e}")


# ───────────────────────────────────────────────
#  語音喚醒 - 優化為更快、更靈敏
# ───────────────────────────────────────────────

class VoiceWakeListener:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = True
        self.confidence_threshold = 0.65          # 降低門檻，更容易觸發
        self.stop_event = threading.Event()

    def similarity(self, a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def check_wake_word(self, text):
        if not text:
            return False
        text = text.lower().strip()
        for words in WAKE_WORDS.values():
            for w in words:
                if w.lower() in text or self.similarity(text, w.lower()) >= self.confidence_threshold:
                    return True
        return False

    def listen_for_wake_word(self):
        print("語音喚醒監聽已啟動（已優化速度與靈敏度）...")
        with self.microphone as source:
            # 縮短噪音校正時間，讓啟動更快
            self.recognizer.adjust_for_ambient_noise(source, duration=0.6)

        while self.is_listening and not self.stop_event.is_set():
            try:
                with self.microphone as source:
                    # 縮短 timeout 和 phrase_time_limit，讓反應更快
                    audio = self.recognizer.listen(source, timeout=4.0, phrase_time_limit=2.5)

                if self.stop_event.is_set():
                    return False

                for lang in ['zh-CN', 'en-US']:  # 先試中文，通常更快
                    try:
                        text = self.recognizer.recognize_google(audio, language=lang)
                        print(f"[{lang}] 聽到：{text}")
                        if self.check_wake_word(text):
                            print(f"偵測到喚醒詞！ ({lang}) → 即將點擊語音按鈕")
                            return True
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError:
                        time.sleep(0.5)
            except Exception:
                if self.is_listening:
                    time.sleep(0.4)  # 錯誤時短暫等待，避免 CPU 過載
        return False

    def stop(self):
        self.is_listening = False


voice_listener = VoiceWakeListener()


# ───────────────────────────────────────────────
#  鍵盤 & 托盤功能（保持原樣）
# ───────────────────────────────────────────────

def on_f5_press():
    global f5_press_time, f5_hold_triggered
    f5_press_time = time.time()
    f5_hold_triggered = False

    def monitor():
        global f5_hold_triggered
        start = f5_press_time
        while time.time() - start < 1.0:
            if not keyboard.is_pressed('f5'):
                return
            time.sleep(0.05)
        if keyboard.is_pressed('f5') and not f5_hold_triggered:
            f5_hold_triggered = True
            open_xiaoai()

    threading.Thread(target=monitor, daemon=True).start()


def on_f5_release():
    global f5_press_time
    f5_press_time = None


def force_recalibrate(icon=None, item=None):
    print("\n使用者要求重新校準...")
    if calibrate_voice_button():
        print("校準完成，已更新位置")
    else:
        print("校準取消，保留舊位置（如果有的話）")
    update_tray_menu()


def toggle_voice_wake(icon=None, item=None):
    global voice_wake_enabled
    voice_wake_enabled = not voice_wake_enabled
    status = "啟用" if voice_wake_enabled else "停用"
    print(f"語音喚醒：{status}")
    if voice_wake_enabled:
        voice_listener.stop_event.clear()
    else:
        voice_listener.stop_event.set()
    update_tray_menu()


def update_tray_menu():
    global icon_instance
    if icon_instance:
        vw_status = "語音喚醒：啟用" if voice_wake_enabled else "語音喚醒：停用"
        menu = Menu(
            MenuItem('小愛同學啟動器', lambda: None, enabled=False),
            MenuItem('按住 F5 1秒 開啟', lambda: None, enabled=False),
            MenuItem(vw_status, toggle_voice_wake),
            MenuItem('重新校準語音按鈕位置', force_recalibrate),
            MenuItem('結束程式', stop_program),
        )
        icon_instance.menu = menu


def stop_program(icon=None, item=None):
    global voice_listener_active
    print("\n正在關閉...")
    voice_listener_active = False
    voice_listener.stop()
    try:
        keyboard.unhook_all()
    except:
        pass
    try:
        icon.stop()
    except:
        pass
    print("已關閉")
    sys.exit(0)


def create_icon():
    img = Image.new('RGB', (32, 32), 'blue')
    draw = ImageDraw.Draw(img)
    draw.text((5, 5), "AI", fill='white')
    return img


# ───────────────────────────────────────────────
#  主程式
# ───────────────────────────────────────────────

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--no-voice', action='store_true')
    parser.add_argument('--no-auto-click', action='store_true')
    args = parser.parse_args()

    if args.no_voice:
        voice_wake_enabled = False
        voice_listener.stop_event.set()

    AUTO_CLICK_ENABLED = not args.no_auto_click

    if not load_cached_position():
        print("未找到位置快取，開始第一次校準...")
        calibrate_voice_button()
        if VOICE_BUTTON_POS is None:
            print("校準取消，將使用螢幕比例估計值（可能不準確）")

    keyboard.on_press_key('f5', lambda _: on_f5_press())
    keyboard.on_release_key('f5', lambda _: on_f5_release())

    vw_text = "語音喚醒：啟用" if voice_wake_enabled else "語音喚醒：停用"
    menu = Menu(
        MenuItem('小愛同學啟動器', lambda: None, enabled=False),
        MenuItem('按住 F5 1秒 開啟', lambda: None, enabled=False),
        MenuItem(vw_text, toggle_voice_wake),
        MenuItem('重新校準語音按鈕位置', force_recalibrate),
        MenuItem('結束程式', stop_program),
    )

    icon = Icon("XiaoiLauncher", create_icon(), menu=menu)
    icon_instance = icon

    print("="*70)
    print("小愛同學啟動器 已啟動")
    print("• 按住 F5 1秒 或 說喚醒詞 → 單次點擊語音按鈕")
    print("• 點擊後進入持續監聽模式（實際時間取決於 App）")
    print("• 語音喚醒已優化（更快、更靈敏）")
    print("• 點擊期間滑鼠短暫鎖定（約1秒）")
    if voice_wake_enabled:
        print("• 語音喚醒：已啟用")
    else:
        print("• 語音喚醒：已關閉（可從托盤切換）")
    if AUTO_CLICK_ENABLED:
        print("• 自動點擊：啟用（每次只點一次）")
    else:
        print("• 自動點擊：關閉")
    print("• 右鍵托盤圖示 → 可重新校準位置")
    print("="*70)

    def voice_thread_func():
        while voice_listener_active:
            if voice_wake_enabled:
                if voice_listener.listen_for_wake_word():
                    open_xiaoai()
            else:
                time.sleep(0.6)

    threading.Thread(target=voice_thread_func, daemon=True).start()
    threading.Thread(target=icon.run, daemon=True).start()

    try:
        keyboard.wait()
    except KeyboardInterrupt:
        voice_listener.stop()
        sys.exit(0)