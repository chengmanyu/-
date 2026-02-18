# 小愛同學快速啟動器

一個專為 Windows 設計的輕量工具，讓你可以用 **按住熱鍵 F5 一秒** 或**語音喚醒**（說「小愛同學」或「小愛」）快速呼叫「小愛同學電腦版」，並自動點擊語音輸入按鈕。

**重要前置條件**  
→ 必須先安裝「小愛同學電腦版」（UWP 應用），否則無法啟動與點擊！

## 下載與安裝「小愛同學電腦版」

我們提供官方提取的安裝包（版本 1.0.124.0）： 安裝後可以更新到最新版本

- 檔案名稱：`8497DDF3.639A2791C9AB_1.0.124.0_neutral___kf545nqv09rxe.Msixbundle`
- 下載位置：請到 **[Releases](https://github.com/chengmanyu/XiaoAi-Launcher/releases)** 頁面下載最新版附檔

### 安裝方式（三種選一種）

**方式一：最簡單（推薦）**  
1. 下載 .msixbundle 檔案  
2. 直接**雙擊**該檔案  
3. 系統會自動呼叫「應用程式安裝程式」（App Installer）  
4. 點「安裝」 → 等待完成即可  

（若雙擊無反應，請先確認 Windows 已安裝「應用程式安裝程式」，可從 Microsoft Store 搜尋「App Installer」安裝）

**方式二：使用 PowerShell（適合進階使用者）**  
1. 以**系統管理員身分**開啟 PowerShell  
2. 切換到檔案所在資料夾，例如：
   ```powershell
   cd C:\Downloads
   ```
3. 執行指令：
   ```powershell
   Add-AppxPackage -Path ".\8497DDF3.639A2791C9AB_1.0.124.0_neutral___kf545nqv09rxe.Msixbundle"
   ```
4. 等待安裝完成

**方式三：如果以上都失敗**

- 先去 Microsoft Store 搜尋「小愛同學」直接安裝（最保險，但需要網路）
- 或檢查系統是否缺少依賴 → 可嘗試安裝最新版「App Installer」： https://aka.ms/getwinget

安裝完成後，開始使用啟動器！

目前提供兩個版本：

- **V1**：基礎版，功能穩定，語音喚醒較保守
- **V2**：進階優化版，語音喚醒更快、更靈敏，點擊後滑鼠短暫鎖定防誤觸，支援位置快取與校準

## 功能比較

| 功能項目               | V1 版本                  | V2 版本（推薦）               |
|-----------------------|--------------------------|-------------------------------|
| 按住 F5 1秒 啟動       | ✓                        | ✓                             |
| 語音喚醒（小愛/小愛同學/小愛小愛）| ✓                        | ✓（更靈敏、反應更快）          |
| 自動點擊語音按鈕       | ✓（固定比例座標）         | ✓（支援快取 + 手動校準）       |
| 滑鼠鎖定防誤觸         | ✗                        | ✓（點擊期間約 1 秒鎖鼠）       |
| 系統托盤圖示與選單     | ✓                        | ✓（可切換語音喚醒、重新校準）  |
| 位置校準功能           | ✗                        | ✓                             |
| 命令列參數（--no-voice 等）| ✓                     | ✓                             |

## 下載與使用方式

請到 **[Releases](https://github.com/chengmanyu/XiaoAi-Launcher/releases)** 頁面下載你想要的版本。


## 安裝與執行方式

備註: V1 (可以選擇直接透過已下載的 exe 檔案運行)

1. 下載 V2_xiaoi_launcher.py（或 V1）
2. 確定電腦已安裝 **Python 3.8+**
3. 安裝必要套件（第一次執行需安裝）：

   ```bash
   pip install keyboard pystray pillow speechrecognition pyautogui pygetwindow pynput
   ```
4. 雙擊執行 .py 檔案，或在命令提示字元執行：
   ```bash
   python V2_xiaoi_launcher.py
   ```
  常用啟動參數：
  ```bash
  python V2_xiaoi_launcher.py --no-voice       # 關閉語音喚醒
  python V2_xiaoi_launcher.py --no-auto-click  # 關閉自動點擊
  ```

## 常見問題

- 語音喚醒不靈敏？
  → 請確保麥克風正常，並遠離噪音源。V2 版本已優化靈敏度。
- 自動點擊位置不準？
  → 請優先使用 V2 版本，第一次執行會引導你校準（把滑鼠移到語音圓圈正中央，按 c 確認）。 （不同螢幕解析度也 OK）
  → 校準後位置會儲存，每次啟動後請先校準,移動了小愛視窗也要校準 (右鍵系統托盤)
- 想關閉程式？
  → 右鍵系統托盤的小藍色 AI 圖示 → 結束程式

## 原始碼授權
MIT License – 歡迎 fork / 修改 / 分享

## 感謝
- 感謝 Google Speech Recognition 提供免費語音辨識
- 感謝 pyautogui、keyboard 等優秀的開源專案

有任何問題或建議，歡迎在 Issues 留言！
