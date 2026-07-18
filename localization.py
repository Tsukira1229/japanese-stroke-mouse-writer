# -*- coding: utf-8 -*-
"""Desktop UI localization and Windows language detection."""

from __future__ import annotations

import ctypes
import locale
import sys
from enum import Enum


class Language(str, Enum):
    JAPANESE = "ja"
    TRADITIONAL_CHINESE = "zh-Hant"
    SIMPLIFIED_CHINESE = "zh-Hans"
    ENGLISH = "en"


LANGUAGE_OPTIONS = (
    (Language.JAPANESE, "日本語"),
    (Language.TRADITIONAL_CHINESE, "繁體中文"),
    (Language.SIMPLIFIED_CHINESE, "简体中文"),
    (Language.ENGLISH, "English"),
)


ZH_HANT = {
    "app_title": "日文筆順滑鼠書寫工具",
    "tab_content": "內容與預覽",
    "tab_general": "一般設定",
    "tab_environment": "環境設定",
    "tab_help": "使用說明",
    "emergency_hint": "緊急停止：按 ESC 或將滑鼠移到螢幕角落",
    "help_title": "程式功能與操作方式",
    "help_content": """1. 輸入內容與確認預覽
在「內容與預覽」輸入要書寫的文字。空格、Tab、換行及自動換行都會反映在實際結果中。淡色字格表示占用範圍，黑色線條才是實際筆順。
支援日文、英數、半形片假名、常用符號，以及一部分可用來拼湊顏文字的特殊符號。使用者可自行輸入或貼上顏文字，程式會逐字元書寫；若含有未支援的特殊符號，會在開始前提示。

2. 設定起始座標與末端座標
兩個座標共同形成允許書寫的矩形範圍，座標是整個螢幕的絕對位置。
• 向右書寫：起始座標選矩形左上角，末端座標選右下角。
• 向左書寫：起始座標選矩形右上角，末端座標選左下角。
按下偵測按鈕後，主視窗會最小化，游標所在螢幕會顯示跟隨滑鼠的十字線、即時座標與 3 秒倒數，協助對齊指定位置。偵測末端時，已取得的起點會保持標示，且同一螢幕會顯示預計書寫矩形。倒數結束後程式會自動填入 X、Y。偵測期間按 ESC 可取消並保留原座標。也可直接輸入座標，多螢幕環境可使用負數。

3. 調整排版
「一般設定」可調整字體大小、字距、行距、水平或垂直排列，以及向右或向左流向。半形字元彼此相鄰時使用一半字距；只要任一側為全形字元就使用完整字距。空格與 Tab 亦遵循此規則。文字到達主方向邊界時會自動換行或換欄；副方向空間不足時會在移動滑鼠前停止並顯示錯誤。垂直排列會自動旋轉英數字、括號與長音符號。
書寫風格可選擇KanjiVG原始筆跡或Yomogi直繪中心線。Yomogi以最終外觀為優先，路徑順序不代表傳統筆順；96個無法產生合格中心線的目錄字元會明確回退KanjiVG。

4. 調整書寫環境
「環境設定」可切換語言，並調整開始倒數、曲線精細度與取樣點停頓。曲線精細度越小越平滑但耗時越長；若筆畫斷線，可增加取樣點停頓。

5. 開始書寫
先按「更新預覽」確認內容完全位於矩形內，再按「開始書寫」。開始倒數期間請切換到目標畫布，並保持畫筆或鉛筆工具已選取。

6. 緊急停止
座標偵測、開始倒數或書寫期間都可按 ESC 停止。書寫時也可將滑鼠快速移到任一螢幕角落觸發安全停止。程式在停止或發生錯誤時會自動放開滑鼠左鍵。""",
    "writing_text": "書寫文字",
    "canvas_coordinates": "畫布座標",
    "start_coordinates": "起始座標",
    "end_coordinates": "末端座標",
    "detect": "偵測{target}",
    "update_preview": "更新預覽",
    "start_writing": "開始書寫",
    "actual_preview": "實際排版預覽",
    "preview_hint": "淡色字格僅供定位；實際輸出為黑色筆順路徑。",
    "preview_empty": "請確認文字、座標與排版設定",
    "text_layout": "文字與排版",
    "font_size_px": "字體大小（px）",
    "char_gap_px": "字距（px）",
    "line_gap_px": "行距（px）",
    "orientation": "排列方向",
    "flow": "流向",
    "stroke_style": "書寫風格",
    "horizontal": "水平",
    "vertical": "垂直",
    "right": "向右",
    "left": "向左",
    "presets": "自訂選項",
    "preset_add": "新增",
    "preset_overwrite": "覆寫",
    "preset_rename": "重新命名",
    "preset_delete": "刪除",
    "preset_hint": "自訂選項保存字體大小、字距、行距、排列方向、流向與書寫風格。",
    "writing_environment": "書寫環境",
    "language": "語言",
    "appearance": "外觀主題",
    "appearance_system": "跟隨系統",
    "appearance_light": "亮色主題",
    "appearance_dark": "暗色主題",
    "appearance_hint": "預設使用亮色主題，也可改為暗色主題或跟隨 Windows。",
    "countdown_seconds": "開始倒數（秒）",
    "curve_detail": "曲線精細度",
    "point_delay_ms": "取樣點停頓（毫秒）",
    "countdown_hint": "倒數：按下開始後保留的視窗切換時間。",
    "curve_hint": "曲線精細度：範圍 0.1–20；數字越小越細緻，但書寫時間越長。",
    "delay_hint": "取樣點停頓：範圍 1–1000 毫秒；若筆畫斷線可適度提高。",
    "ready": "準備就緒",
    "language_changed": "介面語言已切換",
    "appearance_changed": "外觀主題已切換",
    "preview_updating": "正在更新排版預覽…",
    "preview_updated": "預覽已更新",
    "preview_summary": "{cells} 格 · {strokes} 筆 · {points} 點",
    "settings_error": "設定錯誤",
    "preview_error": "無法建立預覽",
    "portable_write_error": "Portable 資料夾無法寫入",
    "preset_select_first": "請先選擇自訂選項。",
    "preset_title": "自訂選項",
    "preset_add_title": "新增自訂選項",
    "preset_name_prompt": "名稱（1–40 個字元）：",
    "preset_overwrite_title": "覆寫自訂選項",
    "preset_overwrite_prompt": "以目前設定覆寫「{name}」？",
    "preset_rename_title": "重新命名",
    "preset_new_name": "新名稱：",
    "preset_delete_title": "刪除自訂選項",
    "preset_delete_prompt": "確定刪除「{name}」？",
    "preset_loaded": "已載入自訂選項：{name}",
    "preset_added": "已新增自訂選項：{name}",
    "preset_overwritten": "已覆寫自訂選項：{name}",
    "preset_renamed": "已重新命名為：{name}",
    "preset_deleted": "已刪除自訂選項：{name}",
    "cannot_add": "無法新增",
    "cannot_overwrite": "無法覆寫",
    "cannot_rename": "無法重新命名",
    "cannot_delete": "無法刪除",
    "detecting": "{target}偵測進行中…",
    "coordinate_detected": "已偵測{target}座標：X={x}，Y={y}",
    "start_short": "起始",
    "end_short": "末端",
    "preparing_write": "準備開始書寫…",
    "cannot_start": "無法開始書寫",
    "writing_complete": "書寫完成",
    "complete": "完成",
    "complete_message": "文字已依預覽排版完成書寫。",
    "cancelled_esc": "操作已由 ESC 取消",
    "cancelled_failsafe": "滑鼠已移到螢幕角落，操作已停止",
    "operation_failed": "操作未完成",
    "operation_running": "操作進行中",
    "stop_requested": "已送出停止要求，請等待操作結束。",
    "number_required": "「{label}」必須是數字。",
    "finite_required": "「{label}」必須是有限數字。",
    "minimum": "「{label}」不可小於 {value}。",
    "maximum": "「{label}」不可大於 {value}。",
    "integer_required": "「{label}」必須是整數。",
    "invalid_number_reverted": "「{label}」輸入無效，已恢復上一個有效值。",
    "font_size": "字體大小",
    "char_gap": "字距",
    "line_gap": "行距",
    "countdown": "開始倒數",
    "point_delay": "取樣點停頓",
    "start_x": "起始 X",
    "start_y": "起始 Y",
    "end_x": "末端 X",
    "end_y": "末端 Y",
    "layout_font_range": "字體大小必須介於 10 與 1000 px。",
    "layout_gap_negative": "字距與行距不可為負數。",
    "layout_end_pair": "末端 X 與 Y 座標必須同時設定。",
    "layout_vertical_small": "起點與末端的垂直範圍小於半個字格。",
    "layout_right_small": "向右排版時，末端 X 必須位於起點右側且至少容納半個字格。",
    "layout_left_small": "向左排版時，起點與末端的水平範圍至少需要容納半個字格。",
    "layout_text_empty": "請輸入至少一個支援的書寫字元。",
    "layout_wrap_overflow": "第 {index} 個字元換行後超出畫布範圍。",
    "layout_primary_overflow": "第 {index} 個字元無法放入目前畫布寬度或高度。",
    "layout_wrap_still_overflow": "第 {index} 個字元換行後仍無法放入畫布。",
    "layout_character_overflow": "第 {index} 個字元超出畫布範圍。",
    "unsupported_character": "第 {index} 個字元「{char}」不是支援的書寫字元。",
    "missing_character": "找不到第 {index} 個字元「{char}」的筆順資料。",
    "stroke_style_resource": "Yomogi風格包中缺少預期字元「{char}」，資料可能已損毀。",
    "escape_operation": "已按下 ESC，操作已停止。",
    "escape_writing": "已按下 ESC，書寫已停止。",
    "failsafe_stop": "滑鼠已移到安全停止角落，書寫已中止。",
    "virtual_screen_error": "無法取得 Windows 虛擬螢幕尺寸。",
    "send_input_error": "Windows SendInput 滑鼠事件傳送失敗（錯誤碼 {code}）。",
    "screen_overflow": "筆跡座標 ({x:.0f}, {y:.0f}) 超出虛擬螢幕範圍 ({min_x}, {min_y})–({max_x}, {max_y})。",
    "settings_schema": "不支援的設定檔版本。",
    "preset_missing": "找不到指定的自訂選項。",
    "preset_name_length": "自訂選項名稱必須為 1 至 40 個字元。",
    "preset_duplicate": "已有相同名稱的自訂選項。",
    "portable_permission": "Portable 資料夾無法寫入：{path}\n請將整個程式資料夾移到文件、桌面或其他可寫入位置。",
}


EN = {
    "app_title": "Japanese Stroke Mouse Writer", "tab_content": "Content & Preview", "tab_general": "General", "tab_environment": "Environment", "tab_help": "Help",
    "emergency_hint": "Emergency stop: press ESC or move the pointer to a screen corner", "writing_text": "Text to write", "canvas_coordinates": "Canvas coordinates",
    "help_title": "Features and operation guide",
    "help_content": """1. Enter content and check the preview
Enter the text in Content & Preview. Spaces, tabs, explicit line breaks, and automatic wrapping are preserved in the result. Light cells show occupied space; black lines are the actual stroke paths.
Japanese, letters, numbers, halfwidth katakana, common symbols, and some special symbols useful for assembling kaomoji are supported. Users can type or paste kaomoji manually, and the program writes them character by character. Unsupported special symbols are reported before writing starts.

2. Set the start and end coordinates
The two coordinates form the writable rectangle and use absolute screen positions.
• Right flow: choose the rectangle's top-left corner as Start and bottom-right corner as End.
• Left flow: choose the rectangle's top-right corner as Start and bottom-left corner as End.
After clicking a detection button, the main window is minimized. The pointer's current monitor shows a crosshair, live coordinates, and a three-second countdown to help align the requested position. While detecting the end coordinate, the captured start remains marked and the expected writing rectangle appears when both points are on the same monitor. The X and Y values are filled when the countdown ends. Press ESC to cancel detection and keep the old values. Coordinates may also be entered manually, including negative values on multi-monitor desktops.

3. Adjust the layout
General settings control font size, character gap, line gap, horizontal or vertical orientation, and right or left flow. Adjacent halfwidth characters use half the configured gap; a pair containing any fullwidth character uses the full gap. Spaces and Tab follow the same rule. Text wraps at the main-axis boundary. If the secondary axis has no room, writing stops before the pointer moves and an error is shown. Vertical layout automatically rotates letters, numbers, brackets, and long marks.
Writing style selects KanjiVG Original or Yomogi Direct Centreline. Yomogi prioritizes the final visual result, so its path order is not traditional stroke order. The 96 catalog characters that cannot produce a valid Yomogi centreline explicitly fall back to KanjiVG.

4. Adjust the writing environment
Environment settings control language, start countdown, curve detail, and sample delay. Smaller curve-detail values are smoother but take longer. Increase sample delay if strokes break.

5. Start writing
Click Update preview first and confirm that all content is inside the rectangle. Then click Start writing, switch to the target canvas during the countdown, and keep its pen or pencil tool selected.

6. Emergency stop
Press ESC during coordinate detection, the start countdown, or writing. During writing, moving the pointer quickly to any screen corner also triggers the failsafe. The program releases the left mouse button automatically after a stop or error.""",
    "start_coordinates": "Start coordinates", "end_coordinates": "End coordinates", "detect": "Detect {target}", "update_preview": "Update preview", "start_writing": "Start writing",
    "actual_preview": "Layout preview", "preview_hint": "Light cells show placement; black paths are the actual strokes.", "preview_empty": "Check the text, coordinates, and layout settings",
    "text_layout": "Text and layout", "font_size_px": "Font size (px)", "char_gap_px": "Character gap (px)", "line_gap_px": "Line gap (px)", "orientation": "Orientation", "flow": "Flow", "stroke_style": "Writing style",
    "horizontal": "Horizontal", "vertical": "Vertical", "right": "Right", "left": "Left", "presets": "Presets", "preset_add": "Add", "preset_overwrite": "Overwrite",
    "preset_rename": "Rename", "preset_delete": "Delete", "preset_hint": "Presets save font size, character gap, line gap, orientation, flow, and writing style.",
    "writing_environment": "Writing environment", "language": "Language", "appearance": "Appearance", "appearance_system": "Follow system", "appearance_light": "Light theme", "appearance_dark": "Dark theme", "appearance_hint": "The light theme is used by default; you can choose the dark theme or follow Windows.", "countdown_seconds": "Start countdown (seconds)", "curve_detail": "Curve detail", "point_delay_ms": "Sample delay (ms)",
    "countdown_hint": "Countdown: time to switch to the target window after starting.", "curve_hint": "Curve detail: 0.1–20; smaller values are smoother but take longer.", "delay_hint": "Sample delay: 1–1000 ms; increase it if strokes break.",
    "ready": "Ready", "language_changed": "Interface language changed", "appearance_changed": "Appearance theme changed", "preview_updating": "Updating layout preview…", "preview_updated": "Preview updated", "preview_summary": "{cells} cells · {strokes} strokes · {points} points",
    "settings_error": "Settings error", "preview_error": "Cannot create preview", "portable_write_error": "Portable folder is not writable", "preset_select_first": "Select a preset first.", "preset_title": "Presets",
    "preset_add_title": "Add preset", "preset_name_prompt": "Name (1–40 characters):", "preset_overwrite_title": "Overwrite preset", "preset_overwrite_prompt": "Overwrite “{name}” with the current settings?",
    "preset_rename_title": "Rename", "preset_new_name": "New name:", "preset_delete_title": "Delete preset", "preset_delete_prompt": "Delete “{name}”?", "preset_loaded": "Preset loaded: {name}",
    "preset_added": "Preset added: {name}", "preset_overwritten": "Preset overwritten: {name}", "preset_renamed": "Renamed to: {name}", "preset_deleted": "Preset deleted: {name}",
    "cannot_add": "Cannot add", "cannot_overwrite": "Cannot overwrite", "cannot_rename": "Cannot rename", "cannot_delete": "Cannot delete", "detecting": "Detecting {target}…",
    "coordinate_detected": "Detected {target} coordinates: X={x}, Y={y}", "start_short": "start", "end_short": "end", "preparing_write": "Preparing to write…", "cannot_start": "Cannot start writing",
    "writing_complete": "Writing complete", "complete": "Complete", "complete_message": "The text was written using the previewed layout.", "cancelled_esc": "Operation cancelled by ESC", "cancelled_failsafe": "Pointer moved to a screen corner; operation stopped", "operation_failed": "Operation failed",
    "operation_running": "Operation in progress", "stop_requested": "A stop request was sent. Wait for the operation to finish.", "number_required": "“{label}” must be a number.", "finite_required": "“{label}” must be finite.",
    "minimum": "“{label}” cannot be less than {value}.", "maximum": "“{label}” cannot be greater than {value}.", "integer_required": "“{label}” must be an integer.", "invalid_number_reverted": "Invalid {label}; the previous valid value was restored.",
    "font_size": "Font size", "char_gap": "Character gap", "line_gap": "Line gap", "countdown": "Start countdown", "point_delay": "Sample delay", "start_x": "Start X", "start_y": "Start Y", "end_x": "End X", "end_y": "End Y",
    "layout_font_range": "Font size must be between 10 and 1000 px.", "layout_gap_negative": "Character and line gaps cannot be negative.", "layout_end_pair": "End X and Y must be set together.",
    "layout_vertical_small": "The vertical range is smaller than half a character cell.", "layout_right_small": "For right flow, End X must be to the right and fit at least half a cell.", "layout_left_small": "For left flow, the horizontal range must fit at least half a cell.",
    "layout_text_empty": "Enter at least one supported writing character.", "layout_wrap_overflow": "Character {index} exceeds the canvas after wrapping.", "layout_primary_overflow": "Character {index} cannot fit in the canvas width or height.",
    "layout_wrap_still_overflow": "Character {index} still cannot fit after wrapping.", "layout_character_overflow": "Character {index} exceeds the canvas.", "unsupported_character": "Character {index}, “{char}”, is not a supported writing character.",
    "missing_character": "No stroke data was found for character {index}, “{char}”.", "stroke_style_resource": "The expected character “{char}” is missing from the Yomogi style pack; the resource may be damaged.", "escape_operation": "ESC was pressed. The operation stopped.", "escape_writing": "ESC was pressed. Writing stopped.", "failsafe_stop": "The pointer reached a failsafe screen corner. Writing stopped.", "virtual_screen_error": "Cannot read the Windows virtual screen dimensions.", "send_input_error": "Windows SendInput mouse event failed (error {code}).",
    "screen_overflow": "Stroke coordinate ({x:.0f}, {y:.0f}) is outside the virtual screen ({min_x}, {min_y})–({max_x}, {max_y}).", "settings_schema": "Unsupported settings file version.",
    "preset_missing": "The selected preset was not found.", "preset_name_length": "Preset names must contain 1–40 characters.", "preset_duplicate": "A preset with this name already exists.",
    "portable_permission": "The Portable folder is not writable: {path}\nMove the entire program folder to Documents, Desktop, or another writable location.",
}


ZH_HANS = {**ZH_HANT,
    "app_title": "日文笔顺鼠标书写工具", "tab_content": "内容与预览", "tab_general": "常规设置", "tab_environment": "环境设置", "tab_help": "使用说明", "emergency_hint": "紧急停止：按 ESC 或将鼠标移到屏幕角落",
    "help_title": "程序功能与操作方式",
    "help_content": """1. 输入内容并确认预览
在“内容与预览”中输入要书写的文字。空格、Tab、换行和自动换行都会反映在实际结果中。浅色字格表示占用范围，黑色线条才是实际笔顺。
支持日文、英数字、半形片假名、常用符号，以及一部分可用来拼凑颜文字的特殊符号。使用者可自行输入或粘贴颜文字，程序会逐字符书写；若包含不支持的特殊符号，会在开始前提示。

2. 设置起始坐标与末端坐标
两个坐标共同形成允许书写的矩形范围，坐标是整个屏幕的绝对位置。
• 向右书写：起始坐标选择矩形左上角，末端坐标选择右下角。
• 向左书写：起始坐标选择矩形右上角，末端坐标选择左下角。
按下检测按钮后，主窗口会最小化，鼠标所在屏幕会显示跟随指针的十字线、实时坐标与 3 秒倒计时，帮助对齐指定位置。检测末端时，已经取得的起点会保持标示；两个点位于同一屏幕时还会显示预计书写矩形。倒计时结束后程序会自动填入 X、Y。检测期间按 ESC 可取消并保留原坐标。也可直接输入坐标，多屏幕环境可使用负数。

3. 调整排版
“常规设置”可调整字体大小、字距、行距、水平或垂直排列，以及向右或向左流向。半形字符彼此相邻时使用一半字距；只要任一侧为全形字符就使用完整字距。空格与 Tab 也遵循此规则。文字到达主方向边界时会自动换行或换列；副方向空间不足时会在移动鼠标前停止并显示错误。垂直排列会自动旋转英文字母、数字、括号和长音符号。
书写风格可选择KanjiVG原始笔迹或Yomogi直绘中心线。Yomogi以最终外观为优先，路径顺序不代表传统笔顺；96个无法生成合格中心线的目录字符会明确回退到KanjiVG。

4. 调整书写环境
“环境设置”可切换语言，并调整开始倒计时、曲线精细度与采样点停顿。曲线精细度越小越平滑但耗时越长；若笔画断线，可增加采样点停顿。

5. 开始书写
先按“更新预览”确认内容完全位于矩形内，再按“开始书写”。开始倒计时期间请切换到目标画布，并保持画笔或铅笔工具已选中。

6. 紧急停止
坐标检测、开始倒计时或书写期间都可按 ESC 停止。书写时也可将鼠标快速移到任一屏幕角落触发安全停止。程序在停止或发生错误时会自动释放鼠标左键。""",
    "writing_text": "书写文字",
    "canvas_coordinates": "画布坐标", "start_coordinates": "起始坐标", "end_coordinates": "末端坐标", "detect": "检测{target}", "update_preview": "更新预览", "start_writing": "开始书写",
    "actual_preview": "实际排版预览", "preview_hint": "浅色字格仅供定位；实际输出为黑色笔顺路径。", "preview_empty": "请确认文字、坐标与排版设置", "text_layout": "文字与排版",
    "font_size_px": "字体大小（px）", "char_gap_px": "字距（px）", "line_gap_px": "行距（px）", "orientation": "排列方向", "flow": "流向", "stroke_style": "书写风格", "horizontal": "水平", "vertical": "垂直", "right": "向右", "left": "向左",
    "presets": "自定义选项", "preset_add": "新增", "preset_overwrite": "覆盖", "preset_rename": "重命名", "preset_delete": "删除", "preset_hint": "自定义选项保存字体大小、字距、行距、排列方向、流向与书写风格。",
    "writing_environment": "书写环境", "language": "语言", "appearance": "外观主题", "appearance_system": "跟随系统", "appearance_light": "亮色主题", "appearance_dark": "暗色主题", "appearance_hint": "默认使用亮色主题，也可改为暗色主题或跟随 Windows。", "countdown_seconds": "开始倒计时（秒）", "curve_detail": "曲线精细度", "point_delay_ms": "采样点停顿（毫秒）",
    "countdown_hint": "倒计时：按下开始后保留的窗口切换时间。", "curve_hint": "曲线精细度：范围 0.1–20；数值越小越细致，但书写时间越长。", "delay_hint": "采样点停顿：范围 1–1000 毫秒；若笔画断线可适度提高。",
    "ready": "准备就绪", "language_changed": "界面语言已切换", "appearance_changed": "外观主题已切换", "preview_updating": "正在更新排版预览…", "preview_updated": "预览已更新", "preview_summary": "{cells} 格 · {strokes} 笔 · {points} 点", "settings_error": "设置错误", "preview_error": "无法建立预览",
    "portable_write_error": "Portable 文件夹无法写入", "preset_select_first": "请先选择自定义选项。", "start_short": "起始", "end_short": "末端", "preparing_write": "准备开始书写…", "cannot_start": "无法开始书写",
    "writing_complete": "书写完成", "complete": "完成", "complete_message": "文字已按预览排版完成书写。", "cancelled_esc": "操作已由 ESC 取消", "cancelled_failsafe": "鼠标已移到屏幕角落，操作已停止", "operation_failed": "操作未完成", "operation_running": "操作进行中",
    "stop_requested": "已发送停止请求，请等待操作结束。", "number_required": "“{label}”必须是数字。", "finite_required": "“{label}”必须是有限数字。", "minimum": "“{label}”不可小于 {value}。", "maximum": "“{label}”不可大于 {value}。",
    "integer_required": "“{label}”必须是整数。", "invalid_number_reverted": "“{label}”输入无效，已恢复上一个有效值。", "font_size": "字体大小", "char_gap": "字距", "line_gap": "行距", "countdown": "开始倒计时", "point_delay": "采样点停顿",
    "start_x": "起始 X", "start_y": "起始 Y", "end_x": "末端 X", "end_y": "末端 Y", "preset_title": "自定义选项", "preset_add_title": "新增自定义选项", "preset_name_prompt": "名称（1–40 个字符）：",
    "preset_overwrite_title": "覆盖自定义选项", "preset_overwrite_prompt": "使用当前设置覆盖“{name}”？", "preset_rename_title": "重命名", "preset_new_name": "新名称：", "preset_delete_title": "删除自定义选项", "preset_delete_prompt": "确定删除“{name}”？",
    "preset_loaded": "已加载自定义选项：{name}", "preset_added": "已新增自定义选项：{name}", "preset_overwritten": "已覆盖自定义选项：{name}", "preset_renamed": "已重命名为：{name}", "preset_deleted": "已删除自定义选项：{name}",
    "cannot_add": "无法新增", "cannot_overwrite": "无法覆盖", "cannot_rename": "无法重命名", "cannot_delete": "无法删除", "detecting": "正在检测{target}…", "coordinate_detected": "已检测{target}坐标：X={x}，Y={y}",
    "layout_font_range": "字体大小必须介于 10 与 1000 px。", "layout_gap_negative": "字距与行距不可为负数。", "layout_end_pair": "末端 X 与 Y 坐标必须同时设置。", "layout_vertical_small": "起点与末端的垂直范围小于半个字格。",
    "layout_right_small": "向右排版时，末端 X 必须位于起点右侧且至少容纳半个字格。", "layout_left_small": "向左排版时，起点与末端的水平范围至少需要容纳半个字格。", "layout_text_empty": "请输入至少一个支持的书写字符。",
    "layout_wrap_overflow": "第 {index} 个字符换行后超出画布范围。", "layout_primary_overflow": "第 {index} 个字符无法放入当前画布宽度或高度。", "layout_wrap_still_overflow": "第 {index} 个字符换行后仍无法放入画布。", "layout_character_overflow": "第 {index} 个字符超出画布范围。",
    "unsupported_character": "第 {index} 个字符“{char}”不是支持的书写字符。", "missing_character": "找不到第 {index} 个字符“{char}”的笔顺数据。", "stroke_style_resource": "Yomogi风格包中缺少预期字符“{char}”，资源可能已损坏。", "escape_operation": "已按下 ESC，操作已停止。", "escape_writing": "已按下 ESC，书写已停止。", "failsafe_stop": "鼠标已移到安全停止角落，书写已中止。", "virtual_screen_error": "无法获取 Windows 虚拟屏幕尺寸。", "send_input_error": "Windows SendInput 鼠标事件发送失败（错误码 {code}）。",
    "screen_overflow": "笔迹坐标 ({x:.0f}, {y:.0f}) 超出虚拟屏幕范围 ({min_x}, {min_y})–({max_x}, {max_y})。", "settings_schema": "不支持的设置文件版本。", "preset_missing": "找不到指定的自定义选项。", "preset_name_length": "自定义选项名称必须为 1 至 40 个字符。", "preset_duplicate": "已有相同名称的自定义选项。",
    "portable_permission": "Portable 文件夹无法写入：{path}\n请将整个程序文件夹移动到文档、桌面或其他可写入位置。",
}


JA = {**EN,
    "app_title": "日本語筆順マウスライター", "tab_content": "内容とプレビュー", "tab_general": "一般設定", "tab_environment": "環境設定", "tab_help": "使用説明", "emergency_hint": "緊急停止：ESC または画面の隅へマウスを移動",
    "help_title": "機能と操作方法",
    "help_content": """1. 内容を入力してプレビューを確認する
「内容とプレビュー」に書き込む文字を入力します。スペース、Tab、改行、自動折り返しは実際の結果にも反映されます。薄いマスは占有範囲、黒い線は実際の筆順です。
日本語、英数字、半角カタカナ、一般記号、顔文字に使える一部の特殊記号に対応します。顔文字は手入力または貼り付けでき、プログラムが1文字ずつ書き込みます。未対応の特殊記号が含まれる場合は、開始前に通知します。

2. 開始座標と終了座標を設定する
2つの座標で書き込み可能な長方形を指定します。座標は画面全体の絶対位置です。
• 右方向：開始座標に長方形の左上、終了座標に右下を指定します。
• 左方向：開始座標に長方形の右上、終了座標に左下を指定します。
検出ボタンを押すとメイン画面が最小化し、マウスがある画面に追従する十字線、現在座標、3秒のカウントダウンが表示されます。終了座標の検出中は取得済みの開始位置が固定表示され、同じ画面上では予定書き込み範囲も表示されます。十字線を指定位置に合わせると、カウント終了時に X、Y が入力されます。検出中に ESC を押すと元の座標を残して中止できます。座標は直接入力でき、マルチモニターの負の値にも対応します。

3. レイアウトを調整する
「一般設定」では文字サイズ、文字間隔、行間隔、横書きまたは縦書き、右方向または左方向を設定します。半角文字同士は半分の文字間隔を使用し、どちらかが全角文字なら完全な文字間隔を使用します。スペースと Tab にも同じ規則を適用します。主方向の境界に達すると自動で改行または改列します。副方向の空間が不足する場合は、マウスを動かす前に停止してエラーを表示します。縦書きでは英数字、括弧、長音記号を自動回転します。
書き込みスタイルはKanjiVGオリジナルまたはYomogi直接中心線を選択できます。Yomogiは最終的な外観を優先するため、パス順序は伝統的な筆順を示しません。有効な中心線を生成できない96文字はKanjiVGに明示的にフォールバックします。

4. 書き込み環境を調整する
「環境設定」では言語、開始カウントダウン、曲線精度、サンプル待機を設定します。曲線精度は小さいほど滑らかですが時間がかかります。線が途切れる場合はサンプル待機を増やしてください。

5. 書き込みを開始する
先に「プレビュー更新」を押し、内容が長方形内に収まっていることを確認してから「書き始める」を押します。カウントダウン中に対象キャンバスへ切り替え、ペンまたは鉛筆ツールを選択した状態にします。

6. 緊急停止
座標検出、開始カウントダウン、書き込み中は ESC で停止できます。書き込み中にマウスを画面のいずれかの隅へ素早く移動しても安全停止します。停止またはエラー時にはマウス左ボタンを自動で解放します。""",
    "writing_text": "書く文字",
    "canvas_coordinates": "キャンバス座標", "start_coordinates": "開始座標", "end_coordinates": "終了座標", "detect": "{target}を検出", "update_preview": "プレビュー更新", "start_writing": "書き始める",
    "actual_preview": "レイアウトプレビュー", "preview_hint": "薄い枠は配置位置、黒い線が実際の筆順です。", "preview_empty": "文字、座標、レイアウト設定を確認してください", "text_layout": "文字とレイアウト",
    "font_size_px": "文字サイズ（px）", "char_gap_px": "文字間隔（px）", "line_gap_px": "行間隔（px）", "orientation": "配置方向", "flow": "進行方向", "stroke_style": "書き込みスタイル", "horizontal": "横書き", "vertical": "縦書き", "right": "右へ", "left": "左へ",
    "presets": "プリセット", "preset_add": "追加", "preset_overwrite": "上書き", "preset_rename": "名前変更", "preset_delete": "削除", "preset_hint": "プリセットには文字サイズ、文字間隔、行間隔、配置方向、進行方向、書き込みスタイルが保存されます。",
    "writing_environment": "書き込み環境", "language": "言語", "appearance": "外観テーマ", "appearance_system": "システムに合わせる", "appearance_light": "ライトテーマ", "appearance_dark": "ダークテーマ", "appearance_hint": "初期設定ではライトテーマを使用します。ダークテーマまたは Windows に合わせる設定も選択できます。", "countdown_seconds": "開始カウントダウン（秒）", "curve_detail": "曲線精度", "point_delay_ms": "サンプル待機（ミリ秒）",
    "countdown_hint": "カウントダウン：開始後に対象画面へ切り替える時間です。", "curve_hint": "曲線精度：0.1～20。小さいほど滑らかですが時間がかかります。", "delay_hint": "サンプル待機：1～1000 ミリ秒。線が途切れる場合は増やしてください。",
    "ready": "準備完了", "language_changed": "表示言語を変更しました", "appearance_changed": "外観テーマを変更しました", "preview_updating": "プレビューを更新中…", "preview_updated": "プレビューを更新しました", "preview_summary": "{cells} マス・{strokes} 画・{points} 点",
    "settings_error": "設定エラー", "preview_error": "プレビューを作成できません", "portable_write_error": "Portable フォルダーに書き込めません", "preset_select_first": "先にプリセットを選択してください。", "preset_title": "プリセット",
    "preset_add_title": "プリセットを追加", "preset_name_prompt": "名前（1～40文字）：", "preset_overwrite_title": "プリセットを上書き", "preset_overwrite_prompt": "現在の設定で「{name}」を上書きしますか？", "preset_rename_title": "名前変更", "preset_new_name": "新しい名前：",
    "preset_delete_title": "プリセットを削除", "preset_delete_prompt": "「{name}」を削除しますか？", "preset_loaded": "プリセットを読み込みました：{name}", "preset_added": "プリセットを追加しました：{name}",
    "preset_overwritten": "プリセットを上書きしました：{name}", "preset_renamed": "名前を変更しました：{name}", "preset_deleted": "プリセットを削除しました：{name}", "cannot_add": "追加できません", "cannot_overwrite": "上書きできません",
    "cannot_rename": "名前を変更できません", "cannot_delete": "削除できません", "detecting": "{target}を検出中…", "coordinate_detected": "{target}座標：X={x}、Y={y}", "start_short": "開始", "end_short": "終了",
    "preparing_write": "書き込みを準備中…", "cannot_start": "書き込みを開始できません", "writing_complete": "書き込み完了", "complete": "完了", "complete_message": "プレビューのレイアウトで文字を書き込みました。", "cancelled_esc": "ESC で操作を中止しました", "cancelled_failsafe": "マウスが画面の隅に移動したため操作を停止しました",
    "operation_failed": "操作に失敗しました", "operation_running": "操作中", "stop_requested": "停止要求を送りました。操作が終了するまでお待ちください。", "number_required": "「{label}」には数値を入力してください。", "finite_required": "「{label}」には有限の数値を入力してください。",
    "minimum": "「{label}」は {value} 以上にしてください。", "maximum": "「{label}」は {value} 以下にしてください。", "integer_required": "「{label}」には整数を入力してください。", "invalid_number_reverted": "「{label}」が無効なため、直前の値に戻しました。",
    "font_size": "文字サイズ", "char_gap": "文字間隔", "line_gap": "行間隔", "countdown": "開始カウントダウン", "point_delay": "サンプル待機", "start_x": "開始 X", "start_y": "開始 Y", "end_x": "終了 X", "end_y": "終了 Y",
    "layout_font_range": "文字サイズは 10～1000 px にしてください。", "layout_gap_negative": "文字間隔と行間隔に負の値は使用できません。", "layout_end_pair": "終了 X と Y は同時に設定してください。", "layout_vertical_small": "縦方向の範囲が半文字分より小さいです。",
    "layout_right_small": "右方向では終了 X を開始点より右に置き、半文字分以上確保してください。", "layout_left_small": "左方向では横幅を半文字分以上確保してください。", "layout_text_empty": "対応している書き込み文字を1文字以上入力してください。",
    "layout_wrap_overflow": "{index} 文字目は改行後にキャンバスを超えます。", "layout_primary_overflow": "{index} 文字目をキャンバスの幅または高さに配置できません。", "layout_wrap_still_overflow": "{index} 文字目は改行後も配置できません。", "layout_character_overflow": "{index} 文字目がキャンバスを超えます。",
    "unsupported_character": "{index} 文字目の「{char}」は対応している書き込み文字ではありません。", "missing_character": "{index} 文字目の「{char}」に対応する筆順データがありません。", "stroke_style_resource": "Yomogiスタイルパックに必要な文字「{char}」がありません。データが破損している可能性があります。", "escape_operation": "ESC が押されたため操作を停止しました。", "escape_writing": "ESC が押されたため書き込みを停止しました。", "failsafe_stop": "マウスが安全停止用の画面の隅に移動したため書き込みを停止しました。", "virtual_screen_error": "Windows の仮想画面サイズを取得できません。", "send_input_error": "Windows SendInput のマウスイベント送信に失敗しました（エラー {code}）。",
    "settings_schema": "対応していない設定ファイルです。", "preset_missing": "指定したプリセットが見つかりません。", "preset_name_length": "プリセット名は1～40文字にしてください。", "preset_duplicate": "同じ名前のプリセットがあります。",
    "screen_overflow": "筆跡座標 ({x:.0f}, {y:.0f}) は仮想画面の範囲外です ({min_x}, {min_y})–({max_x}, {max_y})。",
    "portable_permission": "Portable フォルダーに書き込めません：{path}\nプログラムフォルダー全体を書き込み可能な場所へ移動してください。",
}


TRANSLATIONS = {
    Language.JAPANESE: JA,
    Language.TRADITIONAL_CHINESE: ZH_HANT,
    Language.SIMPLIFIED_CHINESE: ZH_HANS,
    Language.ENGLISH: EN,
}


def tr(key: str, language: Language, **values: object) -> str:
    template = TRANSLATIONS[language].get(key, ZH_HANT.get(key, key))
    return template.format(**values)


def language_from_code(value: object, fallback: Language | None = None) -> Language:
    try:
        return Language(str(value))
    except ValueError:
        return fallback or detect_system_language()


def language_from_locale(locale_name: str | None) -> Language:
    normalized = (locale_name or "").replace("_", "-").lower()
    if normalized.startswith("ja"):
        return Language.JAPANESE
    if normalized.startswith(("zh-tw", "zh-hk", "zh-mo", "zh-hant")):
        return Language.TRADITIONAL_CHINESE
    if normalized.startswith(("zh-cn", "zh-sg", "zh-hans")):
        return Language.SIMPLIFIED_CHINESE
    return Language.ENGLISH


def _system_locale_name() -> str | None:
    if sys.platform == "win32":
        buffer = ctypes.create_unicode_buffer(85)
        if ctypes.windll.kernel32.GetUserDefaultLocaleName(buffer, len(buffer)):
            return buffer.value
    current = locale.getlocale()[0]
    return current


def detect_system_language() -> Language:
    return language_from_locale(_system_locale_name())


class LocalizedValueError(ValueError):
    def __init__(self, message_key: str, **values: object) -> None:
        self.message_key = message_key
        self.message_values = values
        super().__init__(tr(message_key, Language.TRADITIONAL_CHINESE, **values))


class LocalizedPermissionError(PermissionError):
    def __init__(self, message_key: str, **values: object) -> None:
        self.message_key = message_key
        self.message_values = values
        super().__init__(tr(message_key, Language.TRADITIONAL_CHINESE, **values))


class LocalizedOSError(OSError):
    def __init__(self, message_key: str, **values: object) -> None:
        self.message_key = message_key
        self.message_values = values
        super().__init__(tr(message_key, Language.TRADITIONAL_CHINESE, **values))


def exception_text(error: BaseException, language: Language) -> str:
    key = getattr(error, "message_key", None)
    values = getattr(error, "message_values", {})
    return tr(key, language, **values) if key else str(error)


def validate_translation_catalogs() -> None:
    expected = set(ZH_HANT)
    for language, catalog in TRANSLATIONS.items():
        missing = expected - set(catalog)
        if missing:
            raise RuntimeError(f"{language.value} is missing translations: {sorted(missing)}")
