# CLAUDE.md — 建築分析圖製圖台

單一 HTML 檔的建築分析圖產生器。無框架、無後端、無建置依賴。
功能與資料格式看 [README.md](README.md)，這份只寫「怎麼改、怎麼驗、什麼會騙你」。

---

## 一、動手前先知道的三件事

**① 真正的原始碼是 `src/diagram-table.html`，不是 `index.html`。**

那個檔案是 **claude.ai Artifact 的 body** —— 沒有 doctype、沒有 `<html>/<head>/<body>`，
因為發佈時 Artifact runtime 會自己包。直接用瀏覽器開它會是 quirks mode。

```
改 src/diagram-table.html
py tools/build.py        → 包上骨架產生 index.html（GitHub Pages 服務的就是它）
node tests/smoke.js      → 煙霧測試（每種圖 × 每種版面 × 每個選項）
```

`index.html` 是產物但**有進版控**，因為 Pages 直接服務它。改完一定要重跑 build，
否則線上版跟原始碼會不一致而且沒有任何東西會報錯。

**② 同一份程式碼跑在兩個限制不同的環境。**

| | Artifact（claude.ai） | GitHub Pages |
|---|---|---|
| 外部圖片（地圖圖磚） | ❌ CSP 擋 | ✅ |
| `fetch`（地點搜尋） | ❌ CSP 擋 | ✅ |
| 外部 script | 只有 cdnjs / jsdelivr | ✅ |
| 下載檔案 | ❌ 沙箱擋，只能用剪貼簿 | ✅ |

**任何新功能都要想「在 Artifact 版會怎麼壞」**，並且壞掉時要給出可行的替代路徑
（目前地圖的替代路徑是「上傳自己的底圖」）。

**③ 本機一律用 `py`，不要用 `python`。**
這台機器上 `python` 指到一個什麼套件都沒裝的直譯器。
印中文前先 `$env:PYTHONUTF8 = 1`，否則 Windows 主控台會拋 `UnicodeEncodeError`。

---

## 二、驗證紀律（用真實損害換來的，不是原則宣示）

> **選一個真的偵測得到目標的檢查方法。**
> 不是「一律用看的」也不是「一律用量的」。

2026-09-16 同一天正反兩次都犯：

- **浮水印**：五個圖磚來源全部回 HTTP 200，但 CARTO 的每一張都斜蓋
  「API KEY REQUIRED」、OSM 回的圖片本身寫「403 Access blocked」、
  Esri 淺灰在深縮放回「Map data not yet available」。
  當時我用「四張圖磚 md5 不同 → 不是佔位圖」去論證，**那個推論從根上就錯**
  —— 浮水印疊在真地圖上層，底圖不同 hash 本來就不同。
  我用一個測不到目標的測試，推翻了眼睛已經看到的問題。
  **狀態碼、位元組數、雜湊值都測不到圖片內容。圖片只能看。**
- **圖例重疊**：縮圖上看起來還在疊，量 `getBBox()` 才知道每對間距 34–35px、沒有重疊。
  **像素級的間距只能量，不能看縮圖猜。**

配套三條：

1. **不要拿記憶當基準去驗程式。** 同一天我寫死了兩個「已知的」圖磚索引值去測投影，
   結果那兩個數字是我憑記憶編的，程式才是對的。
   投影改用**正反變換往返** + **物理尺度**（各緯度一度 = 111 km）驗證，不依賴任何常數記憶。
2. **推論一律標記。** 沒實際查過、只是照經驗推的，講的時候要講明。
3. **修完一個，驗過再修下一個。** 修的速度超過驗證速度時淨值是負的。

### 怎麼真的看到畫面

`.claude/launch.json` 有 `diagram` 這一筆（本機 8778 靜態 server）。

```
preview_start {name: "diagram"}   → http://localhost:8778/index.html
```

線上驗證則直接開 Pages。Artifact 版看不到（瀏覽器窗格沒登入），
所以**凡是只在 Artifact 版才會發生的行為，不要宣稱驗過**。

---

## 三、地圖：已驗過的來源（改動前先看這張表）

| 來源 | HTTP | 圖片裡實際畫的東西 | 現況 |
|---|---|---|---|
| Esri World Imagery 航照 | 200 | 真航照，z19 仍清晰 | ✅ 使用中 |
| Esri Light Gray Canvas | 200 | z≤16 真淺灰底圖；z17 起為「Map data not yet available」 | ✅ 使用中，`maxZ:16` |
| CARTO basemaps（四種樣式） | 200 | 真地圖 **＋ API KEY REQUIRED 浮水印** | ❌ 已移除，需免費金鑰 |
| OSM 標準圖磚 | 200 | 圖片本身寫「403 Access blocked」 | ❌ 已移除，違反使用政策 |
| OpenTopoMap | 200 | 真地圖，等高線風格 | ⚠️ 未採用，志工伺服器政策同 OSM |
| Wikimedia maps | 403 | — | ❌ 無 CORS |

三個都送 `Access-Control-Allow-Origin: *`，所以 canvas 不會被污染、`toDataURL()` 可用
—— 整個圖磚合成方案就建立在這一點上，換來源前先確認新來源也有。

**不用地圖函式庫。** 依中心點與縮放算出需要哪幾張圖磚，畫到 canvas，輸出 dataURL
餵進 `S.map.img`。下游（點／流／區／風／光、步行圈、比例尺、分析板、SVG 匯出）
完全不必改。公尺／像素由縮放級別與緯度直接算得，抓完改寫「底圖實際寬度」為實測值，
**比例尺與步行圈因此天生正確**。

缺口：站級尺度只有航照。淺色線稿底圖（分析圖最常用的那種）需要 CARTO 免費金鑰，
URL 格式尚未驗證，未接。

---

## 四、程式結構

一個 IIFE，沒有模組。由上而下：

```
PALETTES / STYLES / TYPES / SAMPLES / SIZES / BOARDS   設定表
S                                                      全域狀態 + localStorage
parse() / parseSite()                                  兩種資料格式
txt() / markFill() / smoothPath() / head() ...          繪圖工具
DRAW.<type>                                            每種圖一個算繪函式，只讀 F 這個矩形
drawBoard()                                            小倍數：改 F、設 TXT_K、包一層巢狀 <svg>
render()                                               圖框 + 圖框頁尾 + 分派
UI                                                     控制項綁定
```

**新增一種圖 = 在 `TYPES` 加一筆、`SAMPLES` 加一筆範例、寫一個 `DRAW.<id>`。**
`DRAW` 函式只能讀 `F`（繪圖區矩形）與傳入的 `C`（顏色）/`st`（風格），
不要直接讀 `W`/`H`，否則分析板模式會壞。

小倍數是用**巢狀 `<svg>` + viewBox** 做的，所以 `DRAW` 函式不必知道自己被縮小了；
字級靠 `TXT_K` 補回來（`txt()` 會乘，`raw:true` 可略過）。

色盤經色盲分離度與對比驗證（deutan/protan/tritan ΔE），亮底暗底各一套。
**改色盤要重跑驗證**，不要憑感覺調。

---

## 五、規矩

- **不准碰 `../stock`。** 那是量化交易研究系統，有自己的 Gate 驗收紀律與
  append-only 判決檔案。分析圖相關的任何檔案、設定、server 設定都放這個 repo。
  曾經為了本機預覽在 stock 的 `.claude/launch.json` 加過一筆，被要求移除。
- **commit 前先把完整訊息給老闆看，等明確同意。** 回一個 `.` 代表同意。
- **精簡，但不准有錯誤或缺失。** 短是刪廢話，不是刪資訊。
- **發現問題或不確定的因素，先停下來討論，不要亂做。**
- 這份文件**不要寫會過期的數字**（測試條數、commit 數、用量）。
  要數字就當場跑指令看 —— 更新過期數字只是把下一次過期往後推。
