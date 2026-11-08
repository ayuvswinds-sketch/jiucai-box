"""
韭菜盒子 (app.py) － 官方資料版台股儀表板
------------------------------------------------------------
資料來源（全部是台灣官方網站，不用 Yahoo）：
  • 財報 EPS、三率、股利：公開資訊觀測站 MOPS（mopsov.twse.com.tw）
  • 每日股價、籌碼、ETF 成交量：臺灣證券交易所（上市）、證券櫃檯買賣中心（上櫃）
  • ETF 配息：證交所／櫃買中心「除權除息」公告

執行方式：在終端機輸入  py -m streamlit run app.py
注意：老師說會漲，但老師不會賠你。本工具僅供學習參考，不構成任何投資建議。
"""

import base64
import hashlib
import io
import json
import os
import pickle
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta

import lxml.html
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import streamlit as st
from PIL import Image

# 「老師說會漲」吉祥物（圖片直接藏在程式裡，不需要另外放圖檔）
LOGO_B64 = "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"

st.set_page_config(page_title="韭菜盒子", page_icon=Image.open(io.BytesIO(base64.b64decode(LOGO_B64))), layout="wide")

# ============================================================
# 1. 介面樣式
# ============================================================
st.markdown(
    """
<style>
.block-container {padding-top: 3.6rem; max-width: 1300px;}
[data-testid="stMetricValue"] {font-size: 1.8rem;}            /* 原本約 2.25rem，縮小 20% */
[data-testid="stMetricLabel"] p {font-size: .8rem;}
[data-testid="stMetricDelta"] {font-size: .8rem;}
[data-testid="stVerticalBlock"] {gap: .65rem;}                /* 區塊之間不要隔太開 */
[data-testid="stCaptionContainer"] {line-height: 1.75; margin-top: 2px;}
.biz {font-size:.92rem; opacity:.85; line-height:1.85; margin-bottom:4px;}
.pill {display:inline-block; padding:5px 16px; border-radius:999px; font-weight:700; font-size:1.05rem;}
.pill-green  {background:rgba(46,204,113,.16); color:#1e9e57; border:1px solid rgba(46,204,113,.55);}
.pill-yellow {background:rgba(241,196,15,.18); color:#b07d00; border:1px solid rgba(241,196,15,.6);}
.pill-red    {background:rgba(231,76,60,.14);  color:#d0392b; border:1px solid rgba(231,76,60,.55);}
.zone-wrap   {position:relative; margin:40px 6px 4px 6px;}
.zone-bar    {height:18px; border-radius:9px;}
.zone-marker {position:absolute; top:-36px; transform:translateX(-50%); font-weight:800;
              font-size:.9rem; white-space:nowrap; text-align:center; line-height:1.1;}
.zone-ticks  {position:relative; height:40px; margin:0 6px; font-size:.78rem; opacity:.8;}
.zone-tick   {position:absolute; transform:translateX(-50%); text-align:center; white-space:nowrap; top:4px;}
.price-card  {border-radius:12px; padding:14px 10px; text-align:center; margin-bottom:14px;}
.price-card .t {font-size:.92rem; font-weight:600;}
.price-card .v {font-size:1.45rem; font-weight:800; margin-top:4px;}
.price-card .d {font-size:.78rem; opacity:.75; margin-top:4px;}
.pc-green  {background:rgba(46,204,113,.12);  border:1px solid rgba(46,204,113,.4);}
.pc-yellow {background:rgba(241,196,15,.12);  border:1px solid rgba(241,196,15,.45);}
.pc-red    {background:rgba(231,76,60,.10);   border:1px solid rgba(231,76,60,.4);}
.pc-blue   {background:rgba(37,99,235,.09);   border:1px solid rgba(37,99,235,.35);}
.summary   {font-size:1.06rem; line-height:1.9;}
.muted     {opacity:.7; font-size:.85rem;}
.brand     {display:flex; align-items:center; gap:18px; margin:4px 0 6px 0;}
.brand img {height:104px; width:104px; object-fit:cover; border-radius:20px;
            box-shadow:0 2px 10px rgba(0,0,0,.08);}
.brand-t   {font-size:2.5rem; font-weight:900; line-height:1.15; color:#3f7d20; letter-spacing:.06em;}
.brand-s   {font-size:.98rem; opacity:.75; margin-top:4px; line-height:1.5;}
table.pick {width:100%; border-collapse:collapse; font-size:.9rem;}
table.pick th {text-align:left; font-weight:500; opacity:.6; padding:6px 8px; border-bottom:1px solid rgba(0,0,0,.12);}
table.pick td {padding:0; border-bottom:1px solid rgba(0,0,0,.06);}
table.pick td a {display:block; padding:7px 8px; color:inherit; text-decoration:none;}
table.pick tr:hover td {background:rgba(63,125,32,.08);}
.news {font-size:.9rem; line-height:1.45; padding:6px 0; border-bottom:1px solid rgba(0,0,0,.06);}
.news .d {opacity:.6; margin-right:6px;}
.news .t {display:inline-block; font-size:.75rem; padding:1px 7px; border-radius:9px; margin-right:6px;
          background:rgba(63,125,32,.12); color:#3f7d20;}
.news .t-up   {background:rgba(37,99,235,.12); color:#1d4ed8;}
.news .t-news {background:rgba(245,158,11,.15); color:#b45309;}
.news .src {opacity:.55; font-size:.8rem; margin-left:4px;}
.news .why {opacity:.7; font-size:.82rem; margin-top:2px;}
.chart-t   {font-weight:700; font-size:1rem; margin-top:10px;}
.tk-box summary {list-style:none; cursor:pointer;}
.tk-box summary::-webkit-details-marker {display:none;}
.ticker {overflow:hidden; white-space:nowrap; border-left:4px solid #3f7d20; border-radius:8px;
         background:rgba(63,125,32,.06); padding:14px 0; font-size:1rem; line-height:1.6;}
.tk-list {padding:4px 0 0 0;}
/* 跑馬燈填滿查詢欄下面的空位：左右兩欄一樣高，跑馬燈自動長到底 */
div[data-testid="stHorizontalBlock"]:has(.st-key-ticker_box) {align-items: stretch !important;}
div[data-testid="stHorizontalBlock"]:has(.st-key-ticker_box) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] {height: 100%;}
div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] > div:has(> .st-key-ticker_box),
div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] > .st-key-ticker_box {flex: 1 1 auto; display: flex; flex-direction: column;}
.st-key-ticker_box, .st-key-ticker_box > div, .st-key-ticker_box [data-testid="stElementContainer"],
.st-key-ticker_box .stMarkdown, .st-key-ticker_box [data-testid="stMarkdown"],
.st-key-ticker_box [data-testid="stMarkdownContainer"], .st-key-ticker_box details, .st-key-ticker_box summary
  {flex: 1 1 auto; display: flex; flex-direction: column; height: 100%;}
.vticker {flex: 1 1 auto; display:flex; flex-direction:column; min-height:160px; height:100%;
          border-left:4px solid #3f7d20; border-radius:8px; background:rgba(63,125,32,.06); padding:10px 14px; margin-bottom:6px;}
.vt-title {font-weight:700; font-size:1rem; margin-bottom:6px;}
.vt-win {flex:1 1 auto; overflow:hidden; position:relative; min-height:120px;}
.vt-in {position:absolute; left:0; right:0; top:0; animation:vtick linear infinite;}
.vticker:hover .vt-in {animation-play-state:paused;}
@keyframes vtick {from {transform:translateY(0);} to {transform:translateY(-50%);}}
.vt-item {padding:6px 0; border-bottom:1px dashed rgba(63,125,32,.25);}
.vt-h {font-weight:700; font-size:.95rem;}
.vt-b {font-size:.9rem; line-height:1.65; opacity:.85;}
.tk-note {font-size:.82rem; opacity:.6; margin-top:6px;}
.ticker-in {display:inline-block; padding-left:100%; animation:tick linear infinite;}
.ticker:hover .ticker-in {animation-play-state:paused;}
@keyframes tick {from {transform:translateX(0);} to {transform:translateX(-100%);}}
.tk-item {border-left:4px solid #3f7d20; padding:6px 12px; margin:8px 0; background:rgba(63,125,32,.05); border-radius:6px;}
.tk-h {font-weight:700; font-size:1rem;}
.tk-b {font-size:.95rem; line-height:1.75;}
.mev {border-left:4px solid #64748b; padding:5px 10px; margin-bottom:8px; background:rgba(0,0,0,.025); border-radius:6px;}
.mev .mh {font-size:.92rem; font-weight:600; line-height:1.5;}
.mev .md {display:inline-block; min-width:92px; opacity:.75; font-weight:500;}
.mev .ml {font-size:.78rem; margin-left:6px; font-weight:600;}
.mev .mi, .mev .ms {font-size:.82rem; opacity:.75; line-height:1.55;}
.mtip {font-size:.85rem; line-height:1.65; opacity:.85; margin-top:4px;}
.theme {display:inline-block; font-size:.82rem; padding:2px 10px; margin:0 6px 6px 0; border-radius:999px;
        background:rgba(37,99,235,.10); color:#1d4ed8; border:1px solid rgba(37,99,235,.25);}
/* 左邊（三率＋名詞小辭典）和右邊（財報與股利）拉成一樣高：名詞小辭典自動往下延伸 */
div[data-testid="stHorizontalBlock"]:has(.st-key-gloss_box) {align-items: stretch !important;}
div[data-testid="stHorizontalBlock"]:has(.st-key-gloss_box) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] {height: 100%;}
div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] > div:has(.st-key-gloss_box),
div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] > .st-key-gloss_box,
div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] > div:has(.st-key-fin_box),
div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] > .st-key-fin_box {flex: 1 1 auto;}
.st-key-gloss_box, .st-key-fin_box {height: 100%;}
.gloss {padding:10px 12px; margin:6px 0; border-radius:8px; background:rgba(63,125,32,.06); border-left:4px solid #3f7d20;}
.gloss .gt {font-weight:700; font-size:1.02rem;}
.gloss .gd {font-size:.95rem; line-height:1.75; margin-top:2px;}
.chart-tip {font-size:.95rem; line-height:1.75; padding:8px 12px; margin:-6px 0 14px 0;
            background:rgba(63,125,32,.07); border-left:4px solid #3f7d20; border-radius:6px;}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 2. 小工具
# ============================================================
class DataError(Exception):
    """抓資料失敗時用的錯誤（訊息會直接顯示給使用者看）"""


def ok(x):
    try:
        return x is not None and np.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def money(x, d=2):
    return f"NT$ {float(x):,.{d}f}" if ok(x) else "—"


def pct(x, d=2):
    return f"{float(x) * 100:.{d}f}%" if ok(x) else "—"


def num(s):
    """'1,234.5' → 1234.5；'--'、空白 → None"""
    try:
        return float(str(s).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def roc_date(s):
    """民國日期 '115/11/05' 或 '114年02月20日' → date(2026, 11, 5)"""
    p = re.sub(r"[年月]", "/", str(s).strip()).replace("日", "").split("/")
    return date(int(p[0]) + 1911, int(p[1]), int(p[2]))


TODAY = date.today()
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_cache")


def cached(key, fetch, permanent, ttl=1800):
    """
    把下載過的資料存在 app.py 旁邊的 data_cache 資料夾。
    已經結束、不會再變的資料（例如去年的財報）永久保存；最新的資料過一段時間再重抓。
    """
    path = os.path.join(CACHE_DIR, hashlib.md5(key.encode()).hexdigest() + ".pkl")
    if os.path.exists(path) and (permanent or time.time() - os.path.getmtime(path) < ttl):
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass
    value = fetch()
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(value, f)
    return value


# ============================================================
# 3. 連線（放慢速度，避免被官方網站判定為頻繁查詢）
# ============================================================
GAP = {"mops": 3.0, "twse": 2.2, "tpex": 1.5}  # 每個網站兩次查詢之間至少間隔幾秒


@st.cache_resource
def _net():
    s = requests.Session()
    s.headers["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    )
    return {"session": s, "last": {}, "locks": {k: threading.Lock() for k in GAP}}


def http(site, method, url, **kw):
    net = _net()
    with net["locks"][site]:  # 同一個網站一次只查一個，不同網站可以同時查
        return _http(net, site, method, url, **kw)


def _http(net, site, method, url, **kw):
    err = None
    for attempt in range(3):
        wait = GAP[site] - (time.time() - net["last"].get(site, 0))
        if wait > 0:
            time.sleep(wait)
        try:
            r = net["session"].request(method, url, timeout=40, **kw)
            net["last"][site] = time.time()
            r.raise_for_status()
            r.encoding = "utf-8"
            if site == "mops" and ("頻繁" in r.text[:4000] or "安全性考量" in r.text[:4000]):
                raise requests.RequestException("公開資訊觀測站表示查詢太頻繁")
            return r
        except requests.RequestException as e:
            err = e
            time.sleep(8 * (attempt + 1))
    names = {"mops": "公開資訊觀測站", "twse": "證交所", "tpex": "櫃買中心"}
    raise DataError(f"暫時連不上{names[site]}（{err}）。可能是網站忙碌或查詢太頻繁，請等 1~2 分鐘再試。")


def get_json(site, url):
    r = http(site, "GET", url)
    try:
        return r.json()
    except ValueError:
        raise DataError("交易所回傳的不是資料（可能暫時擋下了查詢），請等 1~2 分鐘再試。")


def _cells(tr):
    return [c.text_content().strip() for c in tr if c.tag in ("td", "th")]


# ============================================================
# 4. 公開資訊觀測站（MOPS）：EPS 與股利
# ============================================================
MOPS = "https://mopsov.twse.com.tw/mops/web/"
Q_END = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}


def report_deadline(y, s):
    """法規規定的財報公布期限：Q1 5/15、Q2 8/14、Q3 11/14、年報隔年 3/31"""
    return {1: date(y, 5, 15), 2: date(y, 8, 14), 3: date(y, 11, 14), 4: date(y + 1, 3, 31)}[s]


def mops_eps_season(typek, y, s):
    """
    綜合損益表彙總表（t163sb04）：一次抓下整個市場所有公司「該季累計」的基本每股盈餘。
    回傳 {公司代號: (公司名稱, 累計EPS)}
    """
    def fetch():
        html = http("mops", "POST", MOPS + "ajax_t163sb04", data={
            "encodeURIComponent": 1, "step": 1, "firstin": 1, "off": 1, "isQuery": "Y",
            "TYPEK": typek, "year": str(y - 1911), "season": f"{s:02d}",
        }).text
        out = {}
        for tr in lxml.html.fromstring(html).iter("tr"):
            c = _cells(tr)
            if len(c) > 3 and re.fullmatch(r"\d{4,6}[A-Z]?", c[0]) and ok(num(c[-1])):
                out[c[0]] = (c[1], num(c[-1]))
        if not out and done:
            raise DataError(f"公開資訊觀測站 {y - 1911} 年第 {s} 季資料讀取失敗，請稍後再試。")
        return out

    done = TODAY > report_deadline(y, s) + timedelta(days=10)
    return cached(f"eps|{typek}|{y}|{s}", fetch, permanent=done, ttl=6 * 3600)


def mops_dividends(code):
    """
    股利分派情形（t05st09_2）：董事會／股東會決議的現金股利。
    回傳 list[dict(期間名稱, 起, 迄, 決議日, 每股現金)]
    """
    def fetch():
        html = http("mops", "POST", MOPS + "ajax_t05st09_2", data={
            "encodeURIComponent": 1, "step": 1, "firstin": 1, "off": 1, "queryName": "co_id",
            "inpuType": "co_id", "TYPEK": "all", "isnew": "false", "co_id": code,
            "date1": str(TODAY.year - 1911 - 5), "date2": str(TODAY.year - 1911), "qryType": "1",
        }).text
        rows, seen = [], set()
        for tr in lxml.html.fromstring(html).iter("tr"):
            c = _cells(tr)
            if len(c) < 13 or "~" not in c[2]:
                continue
            try:
                start, end = (roc_date(x) for x in c[2].split("~"))
                board = roc_date(c[4])
            except (ValueError, IndexError):
                continue
            key = (start, end, c[3])
            if key in seen:  # 同一期可能有「董事會」和「股東會」兩筆，只算一次
                continue
            seen.add(key)
            cash = sum(num(c[i]) or 0 for i in (10, 11, 12))  # 盈餘＋法定公積＋資本公積發放的現金
            rows.append({"period": c[1], "start": start, "end": end, "board": board, "cash": cash})
        return rows

    return cached(f"div|{code}", fetch, permanent=False, ttl=12 * 3600)


# ---------- 名詞小辭典（產業簡稱、常見投資名詞）----------
# 格式：(名詞, 中文, 其他叫法, 白話說明, 代表公司)
GLOSSARY = [
    ("PCB", "印刷電路板", ["電路板"], "電子產品裡那塊綠色的板子，所有零件都焊在上面。", ["臻鼎-KY", "欣興", "華通", "健鼎"]),
    ("CCL", "銅箔基板", ["基板"], "做 PCB 的原料，像是電路板的「布料」。AI 伺服器要用高階的 CCL。", ["台光電", "台燿", "聯茂"]),
    ("ABF 載板", "高階 IC 載板", ["ABF", "載板", "IC 載板"], "承載 CPU、AI 晶片的小板子，比一般 PCB 精密很多。", ["欣興", "景碩", "南電"]),
    ("MLCC", "積層陶瓷電容", ["電容"], "很小的電子零件，負責穩定電流，一支手機裡有上千顆。", ["國巨", "華新科"]),
    ("被動元件", "", ["電阻", "電感"], "電容、電阻、電感這類不會自己「運算」的小零件，MLCC 也是其中一種。", ["國巨", "華新科", "奇力新"]),
    ("連接器", "", ["線材"], "讓電線、板子互相接起來的插頭和插座。", ["嘉澤", "貿聯-KY", "信邦"]),
    ("IC", "積體電路", ["晶片", "半導體"], "就是「晶片」，電子產品的大腦。", []),
    ("IC 設計", "", ["晶片設計", "fabless"], "只負責畫晶片的設計圖，不自己生產，生產交給晶圓代工廠。", ["聯發科", "瑞昱", "聯詠", "譜瑞-KY"]),
    ("ASIC", "客製化晶片", ["特殊應用晶片"], "幫特定客戶（例如雲端大廠）量身訂做的晶片，AI 熱潮下需求很大。", ["世芯-KY", "創意", "智原"]),
    ("矽智財", "IP", ["IP"], "晶片裡可以重複使用的「設計零件」，賣授權給 IC 設計公司收權利金。", ["力旺", "晶心科"]),
    ("晶圓代工", "", ["代工", "foundry"], "照客戶的設計圖幫忙生產晶片。", ["台積電", "聯電", "世界"]),
    ("封測", "封裝測試", ["封裝", "測試"], "把做好的晶片包起來、測試能不能用。", ["日月光投控", "京元電子", "力成"]),
    ("CoWoS", "先進封裝", ["先進封裝"], "把好幾顆晶片疊在一起的高級封裝技術，AI 晶片一定要用。", ["台積電", "日月光投控"]),
    ("DRAM", "記憶體", ["動態記憶體"], "電腦運算時暫存資料的地方，價格漲跌很明顯，景氣循環股。", ["南亞科", "華邦電"]),
    ("HBM", "高頻寬記憶體", [], "AI 晶片專用的高速記憶體，主要由韓國 SK 海力士、三星和美國美光生產。", []),
    ("NAND Flash", "快閃記憶體", ["快閃記憶體", "NAND"], "斷電後資料還在的記憶體，用在手機、隨身碟、SSD 硬碟。", ["群聯", "旺宏"]),
    ("記憶體模組", "", ["模組"], "把記憶體晶片組裝成記憶卡、記憶體條來賣。", ["威剛", "十銓", "創見"]),
    ("GPU", "圖形處理器", ["顯示卡"], "AI 運算最重要的晶片，輝達（NVIDIA）是龍頭，AMD 是第二。", []),
    ("AI 伺服器", "", ["伺服器", "server"], "跑 AI 用的超大電腦，台灣廠商幫雲端大廠組裝。", ["廣達", "緯創", "緯穎", "鴻海", "英業達"]),
    ("散熱", "", ["水冷", "液冷"], "幫晶片降溫。AI 晶片很燙，散熱從風扇升級到水冷，題材很熱門。", ["奇鋐", "雙鴻", "健策"]),
    ("機殼", "", ["伺服器機殼"], "伺服器、電腦的外殼和機架。", ["勤誠", "營邦"]),
    ("電源供應器", "", ["電源"], "把插座的電轉成電腦能用的電，AI 伺服器很耗電，需求變大。", ["台達電", "光寶科"]),
    ("CPO", "共同封裝光學", ["光學封裝"], "用「光」代替電線在晶片之間傳資料，更快更省電，是新題材。", ["聯亞", "上詮", "波若威"]),
    ("矽光子", "", ["SiPh"], "跟 CPO 類似，在晶片上用光傳資料。", ["聯亞", "上詮", "聯鈞"]),
    ("光通訊", "", ["光模組"], "用光纖傳網路訊號的零件，資料中心大量使用。", ["華星光", "聯亞", "光聖"]),
    ("網通", "網路通訊", ["交換器", "路由器"], "交換器、路由器、Wi-Fi 等讓網路連線的設備。", ["智邦", "啟碁", "中磊"]),
    ("面板", "", ["LCD", "顯示器"], "電視、電腦螢幕的螢幕，景氣循環股。", ["友達", "群創"]),
    ("重電", "重型電機", ["電網", "變壓器"], "變壓器、配電盤等電力設備，跟電網建設、資料中心用電有關。", ["華城", "士電", "中興電", "亞力"]),
    ("低軌衛星", "", ["衛星"], "在比較低的軌道繞地球的通訊衛星，例如 Starlink 星鏈。", ["昇達科", "華通", "啟碁"]),
    ("機器人", "", ["自動化"], "工業機器人、人形機器人和相關零件（例如滑軌、氣動元件）。", ["上銀", "亞德客-KY", "和大"]),
    ("軍工", "國防工業", ["國防", "無人機"], "飛機、無人機、軍用設備。", ["漢翔", "雷虎"]),
    ("電動車", "", ["EV", "車用"], "電動車的零件，例如馬達、充電、線束。", ["和大", "貿聯-KY", "台達電"]),
    ("蘋概股", "蘋果概念股", ["蘋果"], "主要客戶是蘋果（Apple）的公司，iPhone 賣得好不好影響很大。", ["鴻海", "大立光", "台積電"]),
    ("輝達概念股", "", ["NVIDIA", "輝達"], "跟輝達 AI 供應鏈有關的公司。", ["台積電", "鴻海", "廣達", "緯穎"]),
    ("貨櫃航運", "", ["航運", "航運三雄"], "用貨櫃船運貨的公司，運價漲跌影響很大，景氣循環股。", ["長榮", "陽明", "萬海"]),
    ("金控", "金融控股公司", ["金融股"], "旗下有銀行、保險、證券的大型金融集團，股價通常比較穩，常有配息。", ["富邦金", "國泰金", "中信金", "合庫金"]),
    ("ETF", "指數股票型基金", ["基金"], "一籃子股票包在一起賣，買一張等於分散買很多家公司。", ["元大台灣50", "國泰永續高股息"]),
    ("高股息", "高股息 ETF", ["存股", "高息"], "配息比較多的股票或 ETF，適合想領現金的人。", ["國泰永續高股息", "元大高股息"]),
    ("權值股", "", ["大型股"], "市值很大、會影響大盤漲跌的股票。", ["台積電", "鴻海", "聯發科"]),
    # ---- 投資名詞（沒有代表公司）----
    ("EPS", "每股盈餘", ["盈餘"], "公司賺的錢平均分給每一股是多少元。越高代表越會賺錢。", []),
    ("本益比", "P/E", ["PE", "P/E"], "股價是 EPS 的幾倍。數字越高代表大家願意付越多錢買它的未來，也可能代表比較貴。", []),
    ("殖利率", "", ["現金殖利率"], "一年配的股息 ÷ 股價。例如 5% 代表放一年大約能領回股價的 5% 當現金。", []),
    ("毛利率", "", ["毛利"], "賣東西扣掉成本後還剩幾成，代表產品有沒有競爭力。", []),
    ("營益率", "營業利益率", ["營業利益"], "再扣掉管理、研發、行銷等費用後還剩幾成，代表本業賺不賺錢。", []),
    ("淨利率", "稅後淨利率", ["淨利"], "全部扣完、繳完稅後真正賺到幾成。", []),
    ("月增", "MoM", ["MoM"], "這個月跟上個月比，增加或減少多少。", []),
    ("年增", "YoY", ["YoY"], "這個月跟去年同一個月比，增加或減少多少。比月增更能看出趨勢。", []),
    ("三大法人", "", ["法人"], "外資、投信、自營商這三種大型投資機構，被視為「大戶」。", []),
    ("外資", "外國機構投資人", [], "國外的大型基金、銀行。台股裡影響力最大的大戶。", []),
    ("投信", "證券投資信託", [], "台灣的基金公司，例如發行 ETF 的元大投信。", []),
    ("自營商", "", [], "證券公司用自己的錢買賣股票，通常是短線操作。", []),
    ("融資", "", ["借錢買股票"], "跟證券公司借錢買股票。融資越多代表散戶越積極，但股價下跌時賣壓也會越大。", []),
    ("融券", "", ["放空"], "跟證券公司借股票來賣，等股價下跌再買回來賺差價。", []),
    ("除權息", "", ["除息", "除權"], "公司發股息（除息）或發股票（除權）的那一天，股價會先扣掉發出去的部分。", []),
    ("填息", "", ["填權", "填權息"], "除息後股價又漲回除息前的價格，代表領到的股息是真的賺到。", []),
    ("可轉債", "可轉換公司債", ["CB"], "公司借錢的一種方式，以後可以換成股票。換成股票後股數變多，每股獲利會被稀釋。", []),
    ("庫藏股", "", ["買回"], "公司自己花錢買回自家股票，通常代表公司覺得股價被低估。", []),
    ("法說會", "法人說明會", ["法說"], "公司對外說明營運狀況和未來展望，常會影響股價。", []),
    ("KD", "隨機指標", ["KD 指標"], "0~100 的短線強弱計。K 往上穿過 D 叫黃金交叉（轉強），80 以上過熱、20 以下超賣。", []),
    ("DMI", "趨向指標", ["ADX"], "+DI 是多方力道，−DI 是空方力道；ADX 超過 25 代表趨勢明確。", []),
    ("均線", "移動平均線", ["月線", "季線", "MA"], "過去幾天的平均價格。月線是 20 天、季線是 60 天，股價在均線上面通常代表偏強。", []),
    ("定期定額", "", ["定額"], "每個月固定日期買固定金額，不用猜高低點，適合長期存股。", []),
]


def _gnorm(x):
    return re.sub(r"\s|-KY", "", str(x)).replace("臺", "台").upper()


def glossary_search(q):
    """查名詞：比對名詞、中文、其他叫法；打公司名稱的話，列出它屬於哪些產業"""
    q = _gnorm(q)
    if not q:
        return []
    exact, part, by_co = [], [], []
    for g in GLOSSARY:
        names = [_gnorm(n) for n in [g[0], g[1], *g[2]] if n]
        if q in names:
            exact.append(g)
        elif any(q in n for n in names):
            part.append(g)
        elif any(q == _gnorm(c) or _gnorm(c).startswith(q) for c in g[4]):
            by_co.append(g)
    return exact + part + by_co


def company_themes(name):
    """這家公司出現在哪些產業名詞的代表公司裡"""
    n = _gnorm(name)
    return [g[0] for g in GLOSSARY if g[4] and any(_gnorm(c) == n for c in g[4])
            and g[0] not in ("ETF", "高股息", "權值股")]


def mops_profile(code):
    """公司基本資料（t05st03）：產業類別、主要經營業務"""
    def fetch():
        html = http("mops", "POST", MOPS + "ajax_t05st03", data={
            "encodeURIComponent": 1, "step": 1, "firstin": 1, "off": 1, "queryName": "co_id",
            "inpuType": "co_id", "TYPEK": "all", "co_id": code,
        }).text
        doc = lxml.html.fromstring(html)
        info = {}
        for th in doc.iter("th"):
            label = re.sub(r"\s", "", th.text_content())
            td = th.getnext()
            while td is not None and td.tag != "td":
                td = td.getnext()
            if td is None:  # 有些欄位的內容在下一列
                tr = th.getparent().getnext()
                td = tr.find("td") if tr is not None else None
            if label and td is not None and label not in info:
                info[label] = re.sub(r"\s+", " ", td.text_content()).strip()
        out = {"industry": info.get("產業類別", ""), "business": info.get("主要經營業務", "")}
        if not out["industry"] and not out["business"]:
            raise DataError("公司基本資料暫時讀不到")
        return out

    return cached(f"profile|{code}", fetch, permanent=False, ttl=30 * 86400)


NEWS_TAGS = [  # (分類, 關鍵字, 白話說明)
    ("發債/CB", r"可轉換公司債|轉換公司債|公司債|CB", "借錢或發可轉債。可轉債以後可能換成股票，股數變多、每股獲利會被稀釋"),
    ("增資", r"現金增資|私募|增資發行|GDR|海外存託憑證", "跟股東或投資人拿錢，股數會變多"),
    ("減資", r"減資", "股數變少，可能是退錢給股東或打消虧損"),
    ("處分資產", r"處分", "賣掉資產，可能有一次性的獲利或虧損"),
    ("土地廠房", r"土地|不動產|廠房|建廠|擴廠|使用權資產|資本支出|資本預算|機器設備|設備", "買地、蓋廠、買設備，代表在擴產，短期花錢、長期看成長"),
    ("庫藏股", r"庫藏股|買回本公司股份", "公司自己買回股票，通常代表覺得股價被低估"),
    ("併購投資", r"合併|收購|併購|取得.*股權|轉投資|對.*增資|投資.*公司", "買別的公司或投資子公司，可能帶來新業務"),
    ("股利", r"股利|配息|盈餘分配|除權|除息", "跟配多少股息有關"),
    ("營收財報", r"營收|財務報告|財報|自結|損益", "跟賺多少錢有關"),
    ("法說會", r"法人說明會|法說會", "公司對外說明營運狀況，常會講未來展望"),
    ("背書貸款", r"背書保證|資金貸與", "幫別的公司擔保或借錢給別人，金額太大要留意風險"),
    ("合約訂單", r"重大合約|訂單|簽訂|簽約", "拿到大訂單或簽重要合約"),
]


def tag_news(title):
    for tag, pat, _ in NEWS_TAGS:
        if re.search(pat, title):
            return tag
    return ""


def mops_news(code, days=31):
    """重大訊息（t05st01）：近 1 個月公司自己公告的消息"""
    def fetch(y):
        html = http("mops", "POST", MOPS + "ajax_t05st01", data={
            "encodeURIComponent": 1, "step": 1, "firstin": 1, "off": 1, "keyword4": "", "code1": "",
            "TYPEK2": "", "checkbtn": "", "queryName": "co_id", "inpuType": "co_id", "TYPEK": "all",
            "co_id": code, "year": str(y - 1911), "month": "", "b_date": "", "e_date": "",
        }).text
        rows = []
        for tr in lxml.html.fromstring(html).iter("tr"):
            c = _cells(tr)
            idx = next((i for i, x in enumerate(c) if re.fullmatch(r"\d{2,3}/\d{1,2}/\d{1,2}", x)), None)
            if idx is None:
                continue
            rest = [x for x in c[idx + 1:] if not re.fullmatch(r"[\d:]+|詳細資料", x)]
            if not rest:
                continue
            try:
                rows.append((roc_date(c[idx]), max(rest, key=len)))
            except ValueError:
                continue
        return rows

    start = TODAY - timedelta(days=days)
    out = []
    for y in sorted({start.year, TODAY.year}):
        out += cached(f"news|{code}|{y}", lambda y=y: fetch(y), permanent=False, ttl=6 * 3600)
    out = sorted({r for r in out if r[0] >= start}, key=lambda r: r[0], reverse=True)
    return [(d, t, tag_news(t)) for d, t in out]


def mops_revenue_month(market, y, m):
    """
    每月營收彙總表：整個市場所有公司一個月一份。
    回傳 {公司代號: (當月營收, 上月營收, 去年同月營收)}，單位千元。還沒公布的月份回傳 None。
    """
    def fetch():
        out = {}
        for kind in ("0", "1"):  # 0：國內公司，1：外國公司（KY 股）
            url = f"https://mopsov.twse.com.tw/nas/t21/{market}/t21sc03_{y - 1911}_{m}_{kind}.html"
            net = _net()
            wait = GAP["mops"] - (time.time() - net["last"].get("mops", 0))
            if wait > 0:
                time.sleep(wait)
            try:
                r = net["session"].get(url, timeout=40)
                net["last"]["mops"] = time.time()
            except requests.RequestException as e:
                raise DataError(f"月營收暫時抓不到（{e}）")
            if r.status_code == 404:
                continue
            html = r.content.decode("cp950", errors="ignore")
            for tr in lxml.html.fromstring(html).iter("tr"):
                c = _cells(tr)
                if len(c) >= 5 and re.fullmatch(r"\d{4,6}[A-Z]?", c[0]):
                    cur, prev, last_y = num(c[2]), num(c[3]), num(c[4])
                    if ok(cur):
                        out[c[0]] = (cur, prev, last_y)
        return out or None

    # 月營收最晚隔月 10 日公布；公布期限過了很久的月份就永久保存
    done = TODAY > date(y + (m == 12), m % 12 + 1, 10) + timedelta(days=20)
    v = cached(f"rev|{market}|{y}|{m}", fetch, permanent=done, ttl=6 * 3600)
    return v


def ttm_dividend_mops(rows, asof):
    """近一年股利：從最新一期往回加，加到涵蓋 12 個月為止（季配、半年配、年配都適用）"""
    use = sorted((r for r in rows if r["board"] <= asof and asof - r["end"] < timedelta(days=550)),
                 key=lambda r: r["end"], reverse=True)
    total, months = 0.0, 0
    for r in use:
        if months >= 12:
            break
        total += r["cash"]
        months += max(1, round((r["end"] - r["start"]).days / 30.4))
    return total


# ============================================================
# 5. 證交所／櫃買中心：股價與 ETF 除息
# ============================================================
def _month_done(y, m):
    nxt = date(y + (m == 12), m % 12 + 1, 1)
    return TODAY >= nxt + timedelta(days=3)


def _col(f, *names):
    """找欄位位置；交易所偶爾會改欄位名稱，所以可以給好幾個候選名稱"""
    clean = [str(x).replace(" ", "") for x in f]
    for n in names:
        for i, x in enumerate(clean):
            if x == n or x.startswith(n):
                return i
    raise DataError(f"交易所資料格式變了，找不到「{names[0]}」欄位（目前欄位：{'、'.join(clean)}）。請把這段訊息截圖給 Claude。")


def _ohlcv_rows(data, f, keys, vol_div):
    """把交易所回傳的每日資料整理成 (日期, 開, 高, 低, 收, 成交張數)。keys 的每一項可以是多個候選名稱"""
    i_d, i_o, i_h, i_l, i_c, i_v = (_col(f, *(k if isinstance(k, tuple) else (k,))) for k in keys)
    rows = []
    for r in data:
        c = num(r[i_c])
        if not ok(c):
            continue  # 當天沒有成交
        o, h, l = (num(r[i]) for i in (i_o, i_h, i_l))
        rows.append((roc_date(r[i_d]), o or c, h or c, l or c, c, (num(r[i_v]) or 0) / vol_div))
    return rows


def twse_month(code, y, m):
    def fetch():
        j = get_json("twse", "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY"
                             f"?date={y}{m:02d}01&stockNo={code}&response=json")
        if j.get("stat") != "OK":
            return {"name": None, "rows": []}
        name = (j.get("title") or "").split()[2] if len((j.get("title") or "").split()) > 2 else None
        rows = _ohlcv_rows(j["data"], j["fields"],
                           ("日期", ("開盤價", "開盤"), ("最高價", "最高"), ("最低價", "最低"), ("收盤價", "收盤"), "成交股數"), 1000)
        return {"name": name, "rows": rows}
    return cached(f"twse2|{code}|{y}|{m}", fetch, permanent=_month_done(y, m))


def tpex_month(code, y, m):
    def fetch():
        j = get_json("tpex", "https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock"
                             f"?code={code}&date={y}/{m:02d}/01&response=json")
        t = (j.get("tables") or [{}])[0]
        if not t.get("data"):
            return {"name": j.get("name"), "rows": []}
        # 2025 年以前的欄位叫「成交仟股」，之後改叫「成交張數」，兩者單位相同（1 張 = 1,000 股）
        rows = _ohlcv_rows(t["data"], t["fields"], ("日期", "開盤", "最高", "最低", "收盤", ("成交張數", "成交仟股")), 1)
        return {"name": j.get("name"), "rows": rows}
    return cached(f"tpex2|{code}|{y}|{m}", fetch, permanent=_month_done(y, m))


# ---------- 籌碼：外資／投信買賣超、融資餘額（每天一份全市場資料，所有股票共用） ----------
def twse_chips_day(d):
    def fetch():
        inst, margin = {}, {}
        j = get_json("twse", "https://www.twse.com.tw/rwd/zh/fund/T86"
                             f"?date={d:%Y%m%d}&selectType=ALLBUT0999&response=json")
        if j.get("stat") == "OK":
            f = j["fields"]
            i_f = f.index("外陸資買賣超股數(不含外資自營商)")
            i_fd = f.index("外資自營商買賣超股數")
            i_t = f.index("投信買賣超股數")
            for r in j["data"]:
                inst[r[0].strip()] = (((num(r[i_f]) or 0) + (num(r[i_fd]) or 0)) / 1000, (num(r[i_t]) or 0) / 1000)
        m = get_json("twse", "https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN"
                             f"?date={d:%Y%m%d}&selectType=ALL&response=json")
        for t in m.get("tables") or []:
            f = t.get("fields") or []
            if f and f[0] == "代號" and "今日餘額" in f:
                i_bal = f.index("今日餘額")  # 第一個「今日餘額」是融資
                for r in t.get("data") or []:
                    margin[str(r[0]).strip()] = num(r[i_bal])
        return {"inst": inst, "margin": margin}
    return cached(f"twse_chips|{d}", fetch, permanent=d < TODAY, ttl=3600)


def tpex_chips_day(d):
    def fetch():
        inst, margin = {}, {}
        j = get_json("tpex", "https://www.tpex.org.tw/www/zh-tw/insti/dailyTrade"
                             f"?type=Daily&sect=EW&date={d:%Y/%m/%d}&response=json")
        t = (j.get("tables") or [{}])[0]
        if len(t.get("fields") or []) >= 14:
            # 欄位順序：外資(不含自營) 2~4、外資自營 5~7、外資合計 8~10、投信 11~13 …
            for r in t.get("data") or []:
                inst[str(r[0]).strip()] = ((num(r[10]) or 0) / 1000, (num(r[13]) or 0) / 1000)
        m = get_json("tpex", "https://www.tpex.org.tw/www/zh-tw/margin/balance"
                             f"?date={d:%Y/%m/%d}&response=json")
        t = (m.get("tables") or [{}])[0]
        f = t.get("fields") or []
        if "資餘額" in f:
            i_bal = f.index("資餘額")
            for r in t.get("data") or []:
                margin[str(r[0]).strip()] = num(r[i_bal])
        return {"inst": inst, "margin": margin}
    return cached(f"tpex_chips|{d}", fetch, permanent=d < TODAY, ttl=3600)


def load_chips(code, market, days):
    """依照實際交易日下載籌碼資料（假日不用查）"""
    fn = twse_chips_day if market == "sii" else tpex_chips_day
    bar = st.progress(0.0, text="準備下載籌碼資料…")
    rows = []
    for i, d in enumerate(days):
        bar.progress(i / len(days), text=f"正在下載籌碼：{d:%Y/%m/%d}（第一次比較久，下載過的日子會存起來）")
        day = fn(d)
        f, t = day["inst"].get(code, (None, None))
        rows.append({"date": pd.Timestamp(d), "foreign": f, "trust": t, "margin": day["margin"].get(code)})
    bar.empty()
    return pd.DataFrame(rows).set_index("date")


def twse_exdiv_year(y):
    """證交所除權息計算結果表（整個市場一年份）→ list[(除息日, 代號, 現金)]"""
    def fetch():
        end = min(date(y, 12, 31), TODAY)
        j = get_json("twse", "https://www.twse.com.tw/rwd/zh/exRight/TWT49U"
                             f"?startDate={y}0101&endDate={end:%Y%m%d}&response=json")
        if j.get("stat") != "OK":
            return []
        f = j["fields"]
        i_d, i_c, i_v, i_t = f.index("資料日期"), f.index("股票代號"), f.index("權值+息值"), f.index("權/息")
        return [(roc_date(r[i_d]), r[i_c].strip(), num(r[i_v]) or 0) for r in j["data"] if r[i_t].strip() == "息"]
    return cached(f"twse_exdiv|{y}", fetch, permanent=y < TODAY.year, ttl=12 * 3600)


def tpex_exdiv_year(y):
    def fetch():
        end = min(date(y, 12, 31), TODAY)
        j = get_json("tpex", "https://www.tpex.org.tw/www/zh-tw/bulletin/exDailyQ"
                             f"?startDate={y}/01/01&endDate={end:%Y/%m/%d}&response=json")
        t = (j.get("tables") or [{}])[0]
        if not t.get("data"):
            return []
        f = t["fields"]
        i_d, i_c, i_v = f.index("除權息日期"), f.index("代號"), f.index("息值")
        return [(roc_date(r[i_d]), r[i_c].strip(), num(r[i_v]) or 0) for r in t["data"] if (num(r[i_v]) or 0) > 0]
    return cached(f"tpex_exdiv|{y}", fetch, permanent=y < TODAY.year, ttl=12 * 3600)


def month_list(n):
    """從這個月往回數 n 個月（舊→新）"""
    y, m, out = TODAY.year, TODAY.month, []
    for _ in range(n):
        out.append((y, m))
        y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    return out[::-1]


def ended_quarters(n_years):
    """近 n 年已經結束的季度（舊→新）"""
    out = []
    for y in range(TODAY.year - n_years, TODAY.year + 1):
        for s in (1, 2, 3, 4):
            if date(y, *Q_END[s]) < TODAY:
                out.append((y, s))
    return out


# ---------- 三率：毛利率、營益率、淨利率（公開資訊觀測站 營益分析彙總表 t163sb06） ----------
def mops_margin_season(typek, y, s):
    """
    回傳 {公司代號: (營收百萬, 毛利率%, 營益率%, 淨利率%)}，都是「今年到該季為止的累計」數字。
    金融業（銀行、保險）沒有毛利率，不會出現在這張表。
    """
    def fetch():
        html = http("mops", "POST", MOPS + "ajax_t163sb06", data={
            "encodeURIComponent": 1, "step": 1, "firstin": 1, "off": 1, "isQuery": "Y",
            "TYPEK": typek, "year": str(y - 1911), "season": f"{s:02d}",
        }).text
        out = {}
        for tr in lxml.html.fromstring(html).iter("tr"):
            c = _cells(tr)
            if len(c) >= 7 and re.fullmatch(r"\d{4,6}[A-Z]?", c[0]) and ok(num(c[2])):
                out[c[0]] = (num(c[2]), num(c[3]), num(c[4]), num(c[6]))
        return out

    done = TODAY > report_deadline(y, s) + timedelta(days=10)
    return cached(f"margin3|{typek}|{y}|{s}", fetch, permanent=done, ttl=6 * 3600)


def single_quarter_margins(cum):
    """
    把累計的三率換成「單季」三率：
    單季毛利 = 本季累計毛利 − 上季累計毛利，再除以單季營收（毛利 = 營收 × 毛利率）
    """
    out = {}
    for (y, s), (rev, gm, om, nm) in sorted(cum.items()):
        if s == 1:
            out[(y, s)] = (gm, om, nm)
        elif (y, s - 1) in cum:
            prev = cum[(y, s - 1)]
            q_rev = rev - prev[0]
            if q_rev > 0:
                calc = lambda a, b: (rev * a - prev[0] * b) / q_rev if ok(a) and ok(b) else None
                out[(y, s)] = (calc(gm, prev[1]), calc(om, prev[2]), calc(nm, prev[3]))
    return out


# ---------- 近 30 天 ETF 成交量排行（證交所＋櫃買中心，每天一份全市場資料） ----------
def etf_volume_day(d):
    def fetch():
        vols = {}
        j = get_json("twse", "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX"
                             f"?date={d:%Y%m%d}&type=0099P&response=json")
        for t in j.get("tables") or []:
            f = t.get("fields") or []
            if "證券代號" in f and "成交股數" in f:
                i_c, i_n, i_v = f.index("證券代號"), f.index("證券名稱"), f.index("成交股數")
                for r in t.get("data") or []:
                    vols[r[i_c].strip()] = (r[i_n].strip(), (num(r[i_v]) or 0) / 1000, "TW")
        j = get_json("tpex", "https://www.tpex.org.tw/www/zh-tw/afterTrading/otc"
                             f"?date={d:%Y/%m/%d}&type=EW&response=json")
        t = (j.get("tables") or [{}])[0]
        f = [str(x).strip() for x in t.get("fields") or []]
        if "代號" in f and "成交股數" in f:
            i_c, i_n, i_v = f.index("代號"), f.index("名稱"), f.index("成交股數")
            for r in t.get("data") or []:
                if str(r[i_c]).startswith("00"):
                    vols[r[i_c].strip()] = (r[i_n].strip(), (num(r[i_v]) or 0) / 1000, "TWO")
        return vols
    return cached(f"etfvol|{d}", fetch, permanent=d < TODAY, ttl=3600)


@st.cache_data(ttl=3600, show_spinner=False)
def etf_top10(today):
    """把近 30 天每個交易日的 ETF 成交張數加總，取前 10 名"""
    total, names = {}, {}
    d = today - timedelta(days=29)
    while d <= today:
        if d.weekday() < 5:
            for code, (name, vol, mkt) in etf_volume_day(d).items():
                total[code] = total.get(code, 0) + vol
                names[code] = (name, mkt)
        d += timedelta(days=1)
    top = sorted(total.items(), key=lambda kv: kv[1], reverse=True)[:10]
    return pd.DataFrame([{"代號": f"{c}.{names[c][1]}", "名稱": names[c][0], "30 天成交（張）": v} for c, v in top])


# ---------- 查詢紀錄（存在 data_cache/history.json，只留在你自己的電腦） ----------
HISTORY_FILE = os.path.join(CACHE_DIR, "history.json")
# 放在 Streamlit 雲端（網頁版）時，程式會在 /mount/src 底下。
# 網頁版：每個人只記自己這次打開後查過的（不存檔，大家不會互相看到）；自己電腦：照舊存 14 天。
ON_CLOUD = os.path.abspath(__file__).startswith("/mount/src")


def _read_history():
    if ON_CLOUD:
        return st.session_state.get("hist_rows", [])
    try:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def log_query(symbol, name):
    rows = [r for r in _read_history() if time.time() - r["t"] < 60 * 86400]  # 只保留 60 天內
    rows.append({"symbol": symbol, "name": name, "t": time.time()})
    if ON_CLOUD:
        st.session_state.hist_rows = rows
        return
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)


def top_queries(days=14, n=10):
    recent = [r for r in _read_history() if time.time() - r["t"] < days * 86400]
    if not recent:
        return pd.DataFrame(columns=["代號", "名稱", "查詢次數"])
    df = pd.DataFrame(recent)
    g = df.groupby("symbol").agg(名稱=("name", "last"), 查詢次數=("t", "size"), 最近=("t", "max"))
    g = g.sort_values(["查詢次數", "最近"], ascending=False).head(n).reset_index()
    return g.rename(columns={"symbol": "代號"})[["代號", "名稱", "查詢次數"]]


# ============================================================
# 6. 依代碼下載所有資料（附進度條）
# ============================================================
@st.cache_data(ttl=24 * 3600, show_spinner=False)
def stock_list(today):
    """全部上市、上櫃股票和 ETF 的「代號 → 名稱」，用來讓你直接打股票名稱查詢（一天更新一次）"""
    for back in range(10):  # 從今天往前找最近一個有交易的日子
        d = today - timedelta(days=back)
        if d.weekday() >= 5:
            continue
        out = {}
        j = get_json("twse", "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX"
                             f"?date={d:%Y%m%d}&type=ALLBUT0999&response=json")
        for t in j.get("tables") or []:
            f = t.get("fields") or []
            if "證券代號" in f and "證券名稱" in f:
                i_c, i_n = f.index("證券代號"), f.index("證券名稱")
                for r in t.get("data") or []:
                    out[str(r[i_c]).strip()] = (str(r[i_n]).strip(), "sii")
        j = get_json("tpex", "https://www.tpex.org.tw/www/zh-tw/afterTrading/otc"
                             f"?date={d:%Y/%m/%d}&type=EW&response=json")
        t = (j.get("tables") or [{}])[0]
        f = [str(x).strip() for x in t.get("fields") or []]
        if "代號" in f and "名稱" in f:
            i_c, i_n = f.index("代號"), f.index("名稱")
            for r in t.get("data") or []:
                out.setdefault(str(r[i_c]).strip(), (str(r[i_n]).strip(), "otc"))
        if out:
            return out
    return {}


def find_by_name(text):
    """用名稱找股票：先找完全一樣的，再找開頭一樣的，再找名稱裡有包含的"""
    norm = lambda x: re.sub(r"\s", "", x).replace("臺", "台").upper()
    q = norm(text)
    items = [(c, n, m) for c, (n, m) in stock_list(TODAY).items()]
    for rule in (lambda n: norm(n) == q, lambda n: norm(n).startswith(q), lambda n: q in norm(n)):
        hit = [it for it in items if rule(it[1])]
        if hit:
            return hit
    return []


def detect_market(raw):
    s = (raw or "").strip().upper().replace(" ", "")
    if not s:
        return None, None
    if s.endswith(".TWO"):
        return s[:-4], "otc"
    if s.endswith(".TW"):
        return s[:-3], "sii"
    known = st.session_state.get("mkt_hint", {}).get(s)
    if known:  # 從按鈕或排行榜點進來的，已經知道是上市還是上櫃
        return s, known
    for y, m in month_list(2)[::-1]:  # 只打數字：先找上市，找不到再找上櫃
        if twse_month(s, y, m)["rows"]:
            return s, "sii"
        if tpex_month(s, y, m)["rows"]:
            return s, "otc"
    return s, None


def load_all(code, market, is_etf):
    price_fn = twse_month if market == "sii" else tpex_month
    tasks = [(f"股價 {y}/{m:02d}", f"p{y}{m}", lambda y=y, m=m: price_fn(code, y, m)) for y, m in month_list(25)]
    if is_etf:
        ex_fn = twse_exdiv_year if market == "sii" else tpex_exdiv_year
        tasks += [(f"{y} 年除息資料", f"x{y}", lambda y=y: ex_fn(y)) for y in range(TODAY.year - 4, TODAY.year + 1)]
    else:
        tasks += [(f"{y - 1911} 年第 {s} 季財報", f"e{y}{s}", lambda y=y, s=s: mops_eps_season(market, y, s))
                  for y, s in ended_quarters(4)]
        tasks.append(("股利分派資料", "div", lambda: mops_dividends(code)))
        tasks += [(f"{y - 1911} 年第 {s} 季三率", f"g{y}{s}", lambda y=y, s=s: mops_margin_season(market, y, s))
                  for y, s in ended_quarters(2)]

    # 股價（證交所／櫃買中心）和財報（公開資訊觀測站）是不同網站，分開同時下載，比較快
    groups = {"price": [t for t in tasks if t[1][0] in "px"], "mops": [t for t in tasks if t[1][0] not in "px"]}
    _net()  # 先在主程式建立連線設定
    res, done, now_label = {}, [0], [""]
    try:
        from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
        ctx = get_script_run_ctx()
    except Exception:
        add_script_run_ctx, ctx = None, None

    def run_group(group):
        if add_script_run_ctx and ctx:
            add_script_run_ctx(threading.current_thread(), ctx)
        for label, key, fn in group:
            now_label[0] = label
            res[key] = fn()
            done[0] += 1

    bar = st.progress(0.0, text="準備下載資料…")
    with ThreadPoolExecutor(max_workers=2) as pool:
        futs = [pool.submit(run_group, g) for g in groups.values() if g]
        while not all(f.done() for f in futs):
            bar.progress(min(done[0] / len(tasks), 1.0),
                         text=f"正在下載：{now_label[0]}（{done[0]}/{len(tasks)}，第一次查詢比較久，之後會很快）")
            time.sleep(0.3)
        for f in futs:
            f.result()  # 有錯誤的話在這裡顯示
    bar.empty()

    # 每日股價
    rows, name = [], None
    for y, m in month_list(25):
        p = res[f"p{y}{m}"]
        rows += p["rows"]
        name = p["name"] or name
    if not rows:
        return None
    ohlc = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "vol"])
    ohlc = ohlc.drop_duplicates("date").set_index("date").sort_index()
    ohlc.index = pd.to_datetime(ohlc.index)

    out = {"ohlc": ohlc, "close": ohlc["close"], "name": name, "is_etf": is_etf}
    if is_etf:
        ex = [r for y in range(TODAY.year - 4, TODAY.year + 1) for r in res[f"x{y}"] if r[1] == code]
        out["exdiv"] = pd.Series([r[2] for r in ex], index=pd.to_datetime([r[0] for r in ex]), dtype=float).sort_index()
    else:
        cum = {}
        for y, s in ended_quarters(4):
            hit = res[f"e{y}{s}"].get(code)
            if hit:
                cum[(y, s)] = hit[1]
                out["name"] = out["name"] or hit[0]
        out["cum_eps"] = cum
        out["div_rows"] = res["div"]
        out["cum_margin"] = {(y, s): res[f"g{y}{s}"][code] for y, s in ended_quarters(2) if code in res[f"g{y}{s}"]}
    return out


# ============================================================
# 7. 計算：EPS、技術指標、價格位階
# ============================================================
def ttm_eps_at(cum, y, s):
    """近四季 EPS = 今年累計 + 去年全年 − 去年同期累計（台灣財報是累計數）"""
    if (y, s) not in cum:
        return None
    if s == 4:
        return cum[(y, 4)]
    if (y - 1, 4) in cum and (y - 1, s) in cum:
        return cum[(y, s)] + cum[(y - 1, 4)] - cum[(y - 1, s)]
    return None


def single_quarter_eps(cum):
    out = {}
    for (y, s), v in cum.items():
        if s == 1:
            out[(y, s)] = v
        elif (y, s - 1) in cum:
            out[(y, s)] = v - cum[(y, s - 1)]
    return out


def latest_ttm(cum):
    for y, s in sorted(cum, reverse=True):
        v = ttm_eps_at(cum, y, s)
        if v is not None:
            return v, (y, s)
    return None, None


def calc_rsi(close, n=14):
    diff = close.diff()
    up = diff.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    down = (-diff.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    return 100 - 100 / (1 + up / down)


def calc_kd(df, n=9):
    """KD 指標（台股常用 9 日）：K、D 都在 0~100 之間"""
    low_n, high_n = df["low"].rolling(n).min(), df["high"].rolling(n).max()
    rsv = ((df["close"] - low_n) / (high_n - low_n).replace(0, np.nan) * 100).fillna(50)
    k, d, ks, ds = 50.0, 50.0, [], []
    for v in rsv:
        k = k * 2 / 3 + v / 3
        d = d * 2 / 3 + k / 3
        ks.append(k)
        ds.append(d)
    return pd.Series(ks, index=df.index), pd.Series(ds, index=df.index)


def calc_dmi(df, n=14):
    """DMI 趨向指標：+DI（多方力道）、-DI（空方力道）、ADX（趨勢強度）"""
    h, l, c = df["high"], df["low"], df["close"]
    up, down = h.diff(), -l.diff()
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    smooth = lambda s: s.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    atr = smooth(tr).replace(0, np.nan)
    pdi, mdi = 100 * smooth(plus_dm) / atr, 100 * smooth(minus_dm) / atr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return pdi, mdi, smooth(dx)


def trend_of(ma60):
    m = ma60.dropna()
    if len(m) < 21:
        return "unknown"
    change = m.iloc[-1] / m.iloc[-21] - 1
    return "up" if change > 0.01 else "down" if change < -0.01 else "flat"


def band(values, lo_q=0.1, mid_q=0.5, hi_q=0.9):
    return tuple(float(v) for v in pd.Series(values).quantile([lo_q, mid_q, hi_q]))


def valuation_by_pe(monthly_px, cum, eps_now, close):
    """本益比法：過去 2 年每個月的「月均價 ÷ 當時已公布的近四季 EPS」→ 取低 10%、中間、高 10%"""
    if not ok(eps_now) or eps_now <= 0:
        return None
    pes = []
    for d, px in monthly_px.items():
        known = [(y, s) for (y, s) in cum if report_deadline(y, s) <= d.date()]
        for y, s in sorted(known, reverse=True):
            e = ttm_eps_at(cum, y, s)
            if e is not None:
                if e > 0 and 0 < px / e < 100:
                    pes.append(px / e)
                break
    note = "過去 2 年每個月實際的本益比"
    if len(pes) < 12:
        pes = list(close.iloc[-250:] / eps_now)
        note = "近一年股價換算的本益比（歷史財報不足）"
    lo, mid, hi = band(pes)
    return {"method": "pe", "note": note, "low_mult": lo, "mid_mult": mid, "high_mult": hi,
            "cheap": eps_now * lo, "fair": eps_now * mid, "expensive": eps_now * hi}


def valuation_by_yield(monthly_px, ttm_div_fn, div_now):
    """殖利率法：殖利率越高＝價格越便宜。用過去 2 年每月的歷史殖利率區間"""
    if not ok(div_now) or div_now <= 0:
        return None
    ylds = []
    for d, px in monthly_px.items():
        dv = ttm_div_fn(d.date())
        if dv > 0 and px > 0:
            ylds.append(dv / px)
    if len(ylds) >= 12:
        lo_y, mid_y, hi_y = band(ylds)
        note = "過去 2 年每個月實際的殖利率"
    else:
        lo_y, mid_y, hi_y = 0.03125, 0.05, 0.0625
        note = "存股族常用的殖利率法則（6.25% / 5% / 3.125%）"
    return {"method": "yield", "note": note, "high_yield": hi_y, "mid_yield": mid_y, "low_yield": lo_y,
            "cheap": div_now / hi_y, "fair": div_now / mid_y, "expensive": div_now / lo_y}


def forecast_eps(cum, eps_now):
    """預估 EPS：近四季 EPS × 今年累計 EPS 的年增率（限制在 -15%～+20%，避免過度樂觀）"""
    if not ok(eps_now) or eps_now <= 0 or not cum:
        return None, None
    y, s = max(cum)
    g = 0.0
    if (y - 1, s) in cum and cum[(y - 1, s)] > 0 and cum[(y, s)] > 0:
        g = cum[(y, s)] / cum[(y - 1, s)] - 1
    g = float(np.clip(g, -0.15, 0.20))
    return eps_now * (1 + g), f"近四季 EPS × 今年前 {s} 季 EPS 年增率 {g:+.0%}（已限制在 -15%～+20%）"


def price_zone(price, v):
    if price < v["cheap"]:
        return "cheap"
    if price < v["fair"]:
        return "fair_low"
    if price <= v["expensive"]:
        return "fair_high"
    return "expensive"


# ============================================================
# 8. 小白白話摘要（依規則自動產生）
# ============================================================
def build_summary(price, v, zone, yld, trend, rsi_now, ma20_now, is_etf):
    s = []
    s.append({
        "cheap": f"目前股價 {money(price)} 低於便宜價（{money(v['cheap'])}），以過去的標準來看算是在「打折」。",
        "fair_low": f"目前股價 {money(price)} 介於便宜價和合理價之間，價格還算實在。",
        "fair_high": f"目前股價 {money(price)} 介於合理價和昂貴價之間，不算便宜，但也還沒過熱。",
        "expensive": f"目前股價 {money(price)} 已經高於昂貴價（{money(v['expensive'])}），以過去的標準來看偏貴。",
    }[zone])

    if not ok(yld) or yld <= 0:
        s.append("近一年沒有配息紀錄，賺錢主要得靠股價上漲。")
    elif yld >= 0.05:
        s.append(f"近一年殖利率約 {pct(yld)}，配息表現不錯，等於放一年大約能領回這個比例的現金。")
    elif yld >= 0.03:
        s.append(f"近一年殖利率約 {pct(yld)}，配息表現中規中矩。")
    else:
        s.append(f"近一年殖利率約 {pct(yld)}，配息偏少，比較適合看重成長而不是領股息的人。")

    trend_text = {"up": "季線（60日均價）正在往上走，中期趨勢偏多",
                  "down": "季線（60日均價）稍微向下，中期趨勢偏弱",
                  "flat": "季線（60日均價）走平，中期趨勢沒有明顯方向",
                  "unknown": "上市時間較短，中期趨勢還看不出來"}[trend]
    side = "股價站在月線之上，短線有撐" if ok(ma20_now) and price >= ma20_now else "股價跌到月線之下，短線稍弱"
    s.append(f"{trend_text}；{side}。")

    if ok(rsi_now) and rsi_now >= 70:
        s.append(f"RSI 為 {rsi_now:.0f}，短線漲得有點急，市場情緒偏熱。")
    elif ok(rsi_now) and rsi_now <= 30:
        s.append(f"RSI 為 {rsi_now:.0f}，短線跌得比較深，市場情緒偏冷。")

    hot = ok(rsi_now) and rsi_now >= 70
    if zone == "expensive" or hot:
        label = ("注意追高風險", "red", "價格偏貴或短線過熱，先別急著一次大筆買進。")
    elif zone in ("cheap", "fair_low") and trend != "down":
        label = ("適合定期定額", "green", "價格不貴、趨勢也沒有在往下，適合每月固定小額慢慢買。")
    elif is_etf and zone != "expensive":
        label = ("適合定期定額", "green", "ETF 分散了風險，價格不算貴時，用定期定額長期累積是很穩的方式。")
    elif zone in ("cheap", "fair_low") and trend == "down":
        label = ("觀望中", "yellow", "價格雖然不貴，但還在往下走，可以等季線止跌再分批進場。")
    else:
        label = ("觀望中", "yellow", "價格在合理偏上的位置，沒有特別便宜，可以先觀察。")
    return s[:4], label


# ============================================================
# 9. 畫面：標題、搜尋、右上角排行榜
# ============================================================
if "q" not in st.session_state:
    st.session_state.q = "2330"
    st.session_state.setdefault("mkt_hint", {})["2330"] = "sii"
st.session_state.setdefault("tbl_ver", 0)


def _plain(code):
    """2330.TW → 2330，順便記住它是上市還是上櫃，畫面上就不用顯示 .TW"""
    s = str(code).strip().upper()
    hint = st.session_state.setdefault("mkt_hint", {})
    if s.endswith(".TWO"):
        hint[s[:-4]] = "otc"
        return s[:-4]
    if s.endswith(".TW"):
        hint[s[:-3]] = "sii"
        return s[:-3]
    return s


def set_q(code):
    st.session_state.q = _plain(code)


def pick_row(table_key, df_key):
    """點排行榜的某一列 → 直接查那一檔"""
    rows = st.session_state[f"{table_key}_{st.session_state.tbl_ver}"].selection.rows
    if rows:
        st.session_state.q = _plain(st.session_state[df_key].iloc[rows[0]]["代號"])
        st.session_state.tbl_ver += 1  # 換一個新表格，清掉選取狀態


# 從排行榜點連結進來（網址後面帶 ?q=代號）
if "q" in st.query_params:
    st.session_state.q = _plain(st.query_params["q"])
    del st.query_params["q"]


def link_table(df):
    """簡單的表格：整列都可以點，點一下就查那一檔，不需要勾選框"""
    head = "".join(f"<th>{c}</th>" for c in df.columns)
    body = ""
    for _, r in df.iterrows():
        tds = "".join(f'<td><a href="?q={r["代號"]}" target="_self">{_plain(v) if c == "代號" else v}</a></td>'
                      for c, v in r.items())
        body += f"<tr>{tds}</tr>"
    st.markdown(f'<table class="pick"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>',
                unsafe_allow_html=True)


def show_pick_table(df, table_key):
    df = df.assign(代號=df["代號"].map(_plain))  # 畫面上只顯示數字代號
    st.session_state[f"df_{table_key}"] = df
    st.dataframe(df, hide_index=True, height=35 * (len(df) + 1) + 3,
                 key=f"{table_key}_{st.session_state.tbl_ver}", selection_mode="single-row",
                 on_select=lambda: pick_row(table_key, f"df_{table_key}"))


top_l, top_r = st.columns([1.75, 1], gap="large")

with top_l:
    st.markdown(f"""
<div class="brand">
  <img src="data:image/jpeg;base64,{LOGO_B64}" alt="韭菜盒子">
  <div>
    <div class="brand-t">韭菜盒子</div>
    <div class="brand-s">先看懂數字，再決定要不要被割。</div>
  </div>
</div>""", unsafe_allow_html=True)
    st.caption("財報、三率、股利來自「公開資訊觀測站」；股價、籌碼來自證交所／櫃買中心（收盤後更新）。")
    with st.container(border=True):
        st.text_input(
            "今天想研究哪一根韭…不是，哪一檔股票？（打完按 Enter）", key="q",
            placeholder="例如：2330、台積電、00878、合庫金",
            help="打股票代號或名稱都可以，上市或上櫃系統會自動判斷。名稱只打一部分也行，有好幾檔時會讓你選。",
        )
        hist_slot = st.container()  # 14 天內查過的股票，查完資料後再填進來
    ticker_slot = st.container(key="ticker_box")  # 跑馬燈：填滿查詢欄下面的空位，資料最後再填

with top_r, st.container(border=True):
    st.markdown("##### 近 30 天 ETF 成交量前 10")
    if True:
        try:
            with st.spinner("統計近 30 天 ETF 成交量（第一次約 1 分鐘）…"):
                top_etf = etf_top10(TODAY)
            if len(top_etf):
                link_table(top_etf.assign(**{"30 天成交（張）": top_etf["30 天成交（張）"].map("{:,.0f}".format)}))
                st.caption("點任一列就能直接查詢。近 30 天（含今天）的成交張數加總。")
            else:
                st.caption("近 30 天沒有交易資料。")
        except DataError as e:
            st.caption(f"ETF 排行暫時抓不到：{e}")


def render_history():
    """查詢欄下面的小方塊：14 天內查過的股票，點一下就查"""
    h = top_queries(n=10)
    if len(h):
        items = list(zip(h["代號"], h["名稱"]))
    else:  # 還沒有紀錄時，先放幾個常見的
        items = [("2330.TW", "台積電"), ("8069.TWO", "元太"), ("00878.TW", "國泰永續高股息")]
    with hist_slot:
        st.caption("這次查過" if ON_CLOUD else "14 天內查過")
        per_row = 5
        for i in range(0, len(items), per_row):
            cols = st.columns(per_row)
            for col, (sym, nm) in zip(cols, items[i:i + per_row]):
                col.button(nm, key=f"hist_{sym}", on_click=set_q, args=(sym,))


# ============================================================
# 未來 30 天總經時間軸（AI 上網查證）
# ============================================================
# 依序試這幾個 AI 版本：第一個額度用完或不能用，就自動換下一個。以後 Google 換新版本，只要改這裡
# 免費方案的「上網查證」只開放給 Gemini 2 系列，所以上網查時先試 Gemini 2；不上網時用額度比較多的輕量版
SEARCH_MODELS = ["gemini-2.5-flash-lite", "gemini-2.0-flash", "gemini-2.5-flash", "gemini-3.8-flash"]
PLAIN_MODELS = ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.8-flash"]
GEMINI_MODELS = SEARCH_MODELS


@st.cache_resource
def _macro_cooldown():
    """記住上次失敗的時間（所有分頁共用），避免一直重試、把免費額度越用越少"""
    return {"until": 0.0, "msg": "", "detail": ""}


def ask_gemini(api_key, prompt, allow_no_search=False, search=True):
    """
    問 Gemini（會上網查證）。第一個版本額度用完或不能用，就自動換下一個。
    allow_no_search=True：上網查證的額度都用完時，改用 AI 本身知道的資料再試一次。
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    search_cfg = types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])
    tries = [(m, search_cfg) for m in SEARCH_MODELS] if search else []
    if allow_no_search or not search:
        tries += [(m, None) for m in PLAIN_MODELS]
    errors = []
    for model, cfg in tries:
        try:
            resp = client.models.generate_content(model=model, contents=prompt, config=cfg)
            return resp.text or ""
        except Exception as e:
            errors.append(f"{model}（{'上網查' if cfg else '不上網'}）：{str(e)[:900]}")
            if any(k in str(e) for k in ("429", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND")):
                continue
            raise RuntimeError("\n".join(errors)) from e
    raise RuntimeError("\n".join(errors))


def _ai_failed(e):
    """AI 失敗時記下來，30 分鐘內所有 AI 功能都先不重試，避免浪費免費額度"""
    cd = _macro_cooldown()
    cd["detail"] = str(e)
    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
        cd["msg"] = "AI 的免費額度暫時用完了。每分鐘、每天都有次數上限，每天下午 4 點（台灣時間）重新計算。"
    else:
        cd["msg"] = f"AI 查詢失敗。（錯誤訊息：{e}）"
    cd["until"] = time.time() + 30 * 60
    return cd["msg"]


@st.cache_data(ttl=30 * 86400, show_spinner=False)  # 同一家公司 30 天只問一次
def company_customers(code, name, api_key, ver=3):  # 改了問法就把 ver 加 1，才會重新查
    prompt = f"""
根據你知道的公開資訊：台灣上市櫃公司「{name}」（股票代號 {code}）的主要客戶有哪些？
規則：
1. 只列「上市櫃公司」或「國際知名大廠」，小公司、沒上市的公司不要列。最多 6 個，用大家熟悉的名稱（例如 NVIDIA、蘋果、AMD、鴻海）。
2. 只列公開報導或公司揭露過的客戶。
3. 不確定就回傳空清單，不要猜。
4. 只輸出 JSON，前後不要有其他文字：{{"customers": ["客戶1", "客戶2"]}}
"""
    text = ask_gemini(api_key, prompt, search=False)
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("AI 這次沒有回傳正確的格式")
    return [str(c).strip() for c in json.loads(m.group(0)).get("customers", []) if str(c).strip()][:6]


@st.cache_data(ttl=6 * 3600, show_spinner=False)  # 同一檔股票 6 小時只問一次
def company_news_ai(code, name, today_iso, api_key, ver=1):
    """請 AI 上網找：接下來要發生的事（法說會、股東會等），和近 1 個月的重要市場消息"""
    prompt = f"""
今天是 {today_iso}（台灣時間）。請用 Google 搜尋查證，整理台灣上市櫃公司「{name}」（股票代號 {code}）的：
A. 接下來 60 天內「已經確定日期」的事件，例如法說會、股東會、除權息、財報公布、新產品發表，最多 4 則。
B. 近 30 天內可能影響股價的重要消息，例如跟大廠合作、拿到訂單、擴廠、產品進度、法規或產業變化、分析師調整看法，最多 6 則。

規則：
1. 只列可以查證的消息，不要猜、不要編。查不到就給空清單。
2. 用白話文，不要表情符號。標題 30 字以內。
3. why 用一句話說明這件事可能讓股價往哪個方向動、為什麼。
4. source 寫消息來源的媒體或網站名稱，例如 經濟日報、鉅亨網、公司官網。
5. 只輸出 JSON，前後不要有其他文字：
{{
  "upcoming": [{{"date": "YYYY-MM-DD", "title": "", "why": "", "source": ""}}],
  "recent":   [{{"date": "YYYY-MM-DD", "title": "", "why": "", "source": ""}}]
}}
"""
    text = ask_gemini(api_key, prompt)
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("AI 這次沒有回傳正確的格式")
    data = json.loads(m.group(0))
    today = pd.Timestamp(today_iso)

    def clean(lst, keep):
        out = []
        for e in lst or []:
            try:
                d = pd.Timestamp(e.get("date", ""))
            except Exception:
                continue
            if keep(d) and str(e.get("title", "")).strip():
                out.append({"d": d, "title": str(e["title"]).strip(), "why": str(e.get("why", "")).strip(),
                            "source": str(e.get("source", "")).strip()})
        return out

    up = sorted(clean(data.get("upcoming"), lambda d: today <= d <= today + pd.Timedelta(days=62)), key=lambda e: e["d"])
    rc = sorted(clean(data.get("recent"), lambda d: today - pd.Timedelta(days=31) <= d <= today), key=lambda e: e["d"], reverse=True)
    return {"upcoming": up[:4], "recent": rc[:6]}


@st.cache_data(ttl=30 * 86400, show_spinner=False)
def glossary_ai(term, api_key, ver=1):
    prompt = f"""
請用白話文、不要專業術語、不要表情符號，解釋台股投資人常聽到的名詞「{term}」。
只輸出 JSON，前後不要有其他文字：
{{"term": "名詞", "zh": "中文全名（沒有就空字串）", "desc": "1~2 句白話說明", "cos": ["台股代表公司名稱，最多 4 家，沒有就空清單"]}}
"""
    text = ask_gemini(api_key, prompt, search=False)
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("AI 這次沒有回傳正確的格式")
    d = json.loads(m.group(0))
    return (d.get("term") or term, d.get("zh", ""), [], d.get("desc", ""), [c for c in d.get("cos", []) if c][:4])


def _gemini_key():
    """先找 .streamlit/secrets.toml，再找電腦的環境變數，都沒有就回傳空字串"""
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return os.environ.get("GEMINI_API_KEY", "")


@st.cache_data(ttl=60 * 60 * 6, show_spinner=False)  # 6 小時內只問一次，換股票也不會重問
def macro_calendar(today_iso, api_key):
    prompt = f"""
今天是 {today_iso}（台灣時間）。請用 Google 搜尋查證，整理出從今天起 30 天內，
全球與台美股市最需關注的 4~7 個「總體經濟事件」或「政治大事件」
（例如：Fed FOMC 利率決議、美國 CPI/PCE 通膨、美國非農就業、台灣央行理監事會、選舉、OPEC 會議、輝達等科技巨頭財報）。

規則：
1. 只列出已經公布日期的事件，日期一定要查證，不要自己猜。
2. 日期、時間都換算成台灣時間。
3. 用白話文，不要專業術語，不要表情符號。
4. 只輸出下面格式的 JSON，前後不要有其他文字：
{{
  "events": [
    {{
      "date": "YYYY-MM-DD",
      "time": "台灣時間幾點，例如 21:30，不確定就寫空字串",
      "short": "6 個字以內的短名稱，例如 美國CPI",
      "name": "完整事件名稱",
      "level": "高 或 中 或 低（對台股可能的影響大小）",
      "impact": "可能影響哪些族群、為什麼，一句話",
      "strategy": "建議怎麼因應，一句話"
    }}
  ],
  "tips": [
    "成長期衝刺的人，該怎麼根據這些事件調整，一句話",
    "高股息防守的人，該怎麼根據這些事件調整，一句話"
  ]
}}
"""
    text = ask_gemini(api_key, prompt)
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("AI 這次沒有回傳正確的格式")
    data = json.loads(m.group(0))

    start = pd.Timestamp(today_iso)
    events = []
    for e in data.get("events", []):
        try:
            d = pd.Timestamp(e["date"])
        except Exception:
            continue
        if start <= d <= start + pd.Timedelta(days=31):
            e["d"] = d
            events.append(e)
    events.sort(key=lambda e: e["d"])
    if not events:
        raise ValueError("AI 這次沒有找到未來 30 天內的事件")
    return {"events": events, "tips": data.get("tips", [])[:2]}


def macro_timeline(events, today, days=31):
    level_col = {"高": "#e5383b", "中": "#f59e0b", "低": "#64748b"}
    fig = go.Figure()
    end = today + pd.Timedelta(days=days)
    # 中間那條橫線
    fig.add_shape(type="line", x0=today, x1=end, y0=0, y1=0, line=dict(color="#111111", width=2))
    # 今天
    fig.add_trace(go.Scatter(x=[today], y=[0], mode="markers+text", text=["今天"], textposition="bottom center",
                             marker=dict(size=10, color="#2563eb"), hoverinfo="skip", showlegend=False))
    heights = [1.2, -1.2, 2.2, -2.2]  # 上下交錯，日期靠太近時字才不會疊在一起
    for i, e in enumerate(events):
        y = heights[i % 4]
        col = level_col.get(str(e.get("level", "")).strip(), "#64748b")
        fig.add_shape(type="line", x0=e["d"], x1=e["d"], y0=0, y1=y * 0.82, line=dict(color=col, width=1.5))
        when = e["d"].strftime("%m/%d") + (f" {e['time']}" if e.get("time") else "")
        fig.add_trace(go.Scatter(
            x=[e["d"]], y=[0], mode="markers", showlegend=False,
            marker=dict(size=14, color=col, line=dict(color="white", width=2)),
            hovertemplate=f"<b>{e.get('name', '')}</b><br>{when}<br>影響：{e.get('impact', '')}<extra></extra>"))
        fig.add_annotation(x=e["d"], y=y, text=f"<b>{e.get('short', '')}</b><br>{when}", showarrow=False,
                           font=dict(size=12, color=col), align="center")
    fig.update_layout(
        height=330, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(font_size=17, bgcolor="white", bordercolor="#111111", font_color="#111111"), 
        yaxis=dict(visible=False, range=[-2.9, 2.9], fixedrange=True),
        xaxis=dict(range=[today - pd.Timedelta(days=1), end], tickformat="%m/%d", dtick=7 * 24 * 3600 * 1000,
                   showgrid=False, fixedrange=True),
    )
    return fig


# ---------- 總經大事：官方已公布的日期（不用 AI，也不用金鑰）----------
# 美國的時間是美東時間；程式會自動換算成台灣時間。
# 來源：Fed 官網 FOMC 行事曆、美國勞工統計局（BLS）發布時程、台灣中央銀行。
# 每年 Fed、BLS 公布新一年的日期後，要再補進來。
_MACRO_TYPES = {  # 種類: (短名稱, 完整名稱, 影響, 可能波動的族群, 因應方式)
    "fomc": ("Fed 利率", "美國聯準會（Fed）利率決議", "高",
             "利率敏感的成長股、科技股、金融股；也會影響美元和新台幣匯率",
             "決議前不追高；看主席記者會的說法是偏升息還是偏降息再調整"),
    "cpi": ("美國 CPI", "美國消費者物價指數（通膨）公布", "高",
            "通膨高於預期，科技股、成長股容易跌；低於預期則容易漲",
            "公布前後波動大，短線不要重押；長期定期定額照常"),
    "jobs": ("非農就業", "美國非農就業報告", "中",
             "就業太強可能讓 Fed 不降息，科技股承壓；太弱則擔心景氣",
             "注意失業率和新增人數是否大幅偏離預期"),
    "minutes": ("Fed 會議紀錄", "Fed 上次開會的會議紀錄公布", "低",
                "影響通常不大，除非內容透露新的升降息想法",
                "看看官員對未來利率的看法有沒有改變"),
    "cbc": ("台灣央行", "台灣中央銀行理監事會（利率決議）", "中",
            "銀行、壽險、營建股；也影響房貸利率和新台幣",
            "留意是否調整利率或房貸管制"),
}
MACRO_EVENTS = [  # (美東日期時間 或 台灣日期時間, 種類, 是否為台灣時間, 備註)
    ("2026-11-10 08:30", "cpi", False, ""),
    ("2026-11-18 14:00", "minutes", False, ""),
    ("2026-12-04 08:30", "jobs", False, ""),
    ("2026-12-09 14:00", "fomc", False, ""),
    ("2026-12-10 08:30", "cpi", False, ""),
    ("2026-12-17 16:30", "cbc", True, "預計，以央行公告為準"),
    ("2026-12-30 14:00", "minutes", False, ""),
    ("2027-01-08 08:30", "jobs", False, ""),
    ("2027-01-13 08:30", "cpi", False, ""),
    ("2027-01-27 14:00", "fomc", False, ""),
    ("2027-02-05 08:30", "jobs", False, ""),
    ("2027-02-11 08:30", "cpi", False, ""),
    ("2027-03-05 08:30", "jobs", False, ""),
    ("2027-03-10 08:30", "cpi", False, ""),
    ("2027-03-17 14:00", "fomc", False, ""),
    ("2027-04-02 08:30", "jobs", False, ""),
    ("2027-04-13 08:30", "cpi", False, ""),
    ("2027-04-28 14:00", "fomc", False, ""),
    ("2027-06-09 14:00", "fomc", False, ""),
    ("2027-07-02 08:30", "jobs", False, ""),
    ("2027-07-14 08:30", "cpi", False, ""),
    ("2027-07-28 14:00", "fomc", False, ""),
    ("2027-09-15 14:00", "fomc", False, ""),
    ("2027-10-08 08:30", "jobs", False, ""),
    ("2027-10-27 14:00", "fomc", False, ""),
    ("2027-11-05 08:30", "jobs", False, ""),
    ("2027-11-10 08:30", "cpi", False, ""),
    ("2027-12-03 08:30", "jobs", False, ""),
    ("2027-12-08 14:00", "fomc", False, ""),
    ("2027-12-10 08:30", "cpi", False, ""),
]


def _us_dst(d):
    """美國夏令時間：3 月第二個星期日 ~ 11 月第一個星期日"""
    mar = date(d.year, 3, 8) + timedelta(days=(6 - date(d.year, 3, 8).weekday()) % 7)
    nov = date(d.year, 11, 1) + timedelta(days=(6 - date(d.year, 11, 1).weekday()) % 7)
    return mar <= d.date() < nov


def macro_events(today, days=45):
    """未來 days 天內的總經大事（日期都換成台灣時間）"""
    out = []
    for when, kind, is_tw, note in MACRO_EVENTS:
        t = pd.Timestamp(when)
        if not is_tw:  # 美東 → 台灣：冬天 +13 小時、夏天 +12 小時
            t = t + pd.Timedelta(hours=12 if _us_dst(t) else 13)
        if today <= t.normalize() <= today + pd.Timedelta(days=days):
            short, name, level, impact, strategy = _MACRO_TYPES[kind]
            out.append({"d": t.normalize(), "time": t.strftime("%H:%M"), "short": short,
                        "name": name + (f"（{note}）" if note else ""), "level": level,
                        "impact": impact, "strategy": strategy})
    return out


MACRO_TIPS = [
    "成長期衝刺的人：Fed 利率決議和 CPI 公布前後，科技股波動最大，不要在公布前一天重押，等結果出來再加碼。",
    "高股息防守的人：這些事件對高股息股影響比較小，照原本計畫定期定額就好；股價因消息大跌時，反而是撿便宜的機會。",
]


def render_macro():
    with macro_slot, st.container(border=True):
        st.markdown("#### 總經大事")
        today = pd.Timestamp(date.today())
        events = macro_events(today)
        if not events:
            st.caption("未來 45 天內沒有已公布日期的總經大事。如果一直空白，可能是要補新一年的日期了。")
            return
        left, right = st.columns([1.15, 1], gap="medium")  # 左邊時間軸，右邊日期清單和說明
        with left:
            st.plotly_chart(macro_timeline(events, today, days=46), key="macro_tl")
            st.caption("紅：影響大　橙：中等　灰：小。時間都是台灣時間，滑鼠移到圓點上可以看說明。")
        with right:
            lvl_col = {"高": "#e5383b", "中": "#f59e0b", "低": "#64748b"}
            html = ""
            for e in events:
                c = lvl_col.get(e["level"], "#64748b")
                html += (f'<div class="mev" style="border-left-color:{c}">'
                         f'<div class="mh"><span class="md">{e["d"]:%m/%d} {e["time"]}</span>{e["name"]}'
                         f'<span class="ml" style="color:{c}">影響{e["level"]}</span></div>'
                         f'<div class="mi">{e["impact"]}</div><div class="ms">建議：{e["strategy"]}</div></div>')
            st.markdown(html, unsafe_allow_html=True)
            for t in MACRO_TIPS:
                st.markdown(f"<div class='mtip'>{t}</div>", unsafe_allow_html=True)
        st.caption("日期來源：Fed 官網、美國勞工統計局、台灣中央銀行；僅供參考，不是投資建議。")



def stop_here():
    render_history()
    st.stop()


st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)  # 上方查詢區和公司名稱之間留白



try:
    q_text = (st.session_state.q or "").strip()
    if q_text and not re.fullmatch(r"\d{4,6}[A-Za-z]?(\.TWO?)?", q_text, re.I):  # 打的是名稱，不是代號
        with st.spinner("用名稱尋找股票中…"):
            hits = find_by_name(q_text)
        if not hits:
            st.warning(f"找不到名稱裡有「{q_text}」的股票，換個關鍵字或直接打代號試試。")
            stop_here()
        if len(hits) > 1:
            st.markdown(f"有好幾檔名稱裡有「{q_text}」，你要找的是哪一檔？")
            cols = st.columns(4)
            for i, (c, n, m) in enumerate(hits[:12]):
                cols[i % 4].button(f"{n}（{c}）", key=f"pick_{c}", on_click=set_q,
                                   args=(f"{c}.{'TW' if m == 'sii' else 'TWO'}",))
            if len(hits) > 12:
                st.caption(f"共 {len(hits)} 檔，只列前 12 檔。打完整一點的名稱會更準。")
            stop_here()
        c, n, m = hits[0]
        st.session_state.setdefault("mkt_hint", {})[c] = m
        q_text = c
    with st.spinner("確認股票代碼中…"):
        code, market = detect_market(q_text)
    if not code:
        stop_here()
    if market is None:
        st.warning("找不到這個代碼，請確認號碼是否正確。")
        stop_here()
    data = load_all(code, market, is_etf=code.startswith("00"))
except DataError as e:
    st.error(f"{e}")
    stop_here()

if not data:
    st.warning("查不到這個代碼的股價，請確認號碼是否正確。")
    stop_here()

# ============================================================
# 10. 計算所有數據
# ============================================================
close, is_etf = data["close"], data["is_etf"]
symbol = f"{code}.{'TW' if market == 'sii' else 'TWO'}"
name = data["name"] or code
if st.session_state.get("last_logged") != symbol:  # 同一檔重新整理不重複記錄
    log_query(symbol, name)
    st.session_state.last_logged = symbol
render_history()
price = float(close.iloc[-1])
prev = float(close.iloc[-2]) if len(close) > 1 else price
chg = price - prev
last_day = close.index[-1].date()

ma20, ma60, rsi = close.rolling(20).mean(), close.rolling(60).mean(), calc_rsi(close)
ma20_now, ma60_now, rsi_now = ma20.iloc[-1], ma60.iloc[-1], rsi.iloc[-1]
trend = trend_of(ma60)

monthly_px = close.resample("ME").mean().iloc[-25:-1]  # 過去 24 個完整月份的月均價
monthly_px.index = monthly_px.index.normalize()

if is_etf:
    exdiv = data["exdiv"]
    ttm_div_fn = lambda d: float(exdiv[(exdiv.index > pd.Timestamp(d - timedelta(days=365))) & (exdiv.index <= pd.Timestamp(d))].sum())
    eps_now, eps_q, cum = None, None, {}
else:
    cum, div_rows = data["cum_eps"], data["div_rows"]
    ttm_div_fn = lambda d: ttm_dividend_mops(div_rows, d)
    eps_now, eps_q = latest_ttm(cum)

div_ttm = ttm_div_fn(last_day)
yld = div_ttm / price if price > 0 else None
pe_now = price / eps_now if ok(eps_now) and eps_now > 0 else None

val = None if is_etf else valuation_by_pe(monthly_px, cum, eps_now, close)
if val is None:
    val = valuation_by_yield(monthly_px, ttm_div_fn, div_ttm)

# ============================================================
# 11. 畫面：基本資訊
# ============================================================
profile = {"industry": "", "business": ""}
if not is_etf:
    try:
        with st.spinner("讀取公司基本資料…"):
            profile = mops_profile(code)
    except DataError:
        pass
st.subheader(f"{name}（{code}）" + (f"｜{profile['industry']}" if profile["industry"] else ""))
themes = company_themes(name)
if themes:
    st.markdown("".join(f"<span class='theme'>{t}</span>" for t in themes), unsafe_allow_html=True)
if profile["business"]:
    biz = profile["business"]
    st.markdown(f"<div class='biz'>主要業務：{biz[:90] + '…' if len(biz) > 90 else biz}</div>",
                unsafe_allow_html=True, help=biz if len(biz) > 90 else None)
cust_slot = st.empty()  # 主要客戶（AI 查），最後再填，才不會拖慢整頁
st.caption(f"{'ETF（指數股票型基金）' if is_etf else '個股'}｜{'上市' if market == 'sii' else '上櫃'}｜"
           f"股價日期：{last_day:%Y-%m-%d}"
           + (f"｜最新財報：{eps_q[0] - 1911} 年第 {eps_q[1]} 季" if eps_q else ""))

with st.container(border=True):
    m1, m2, m3, m4 = st.columns(4, gap="small")
    m1.metric("目前股價", money(price), delta=f"{chg:+.2f}（{chg / prev * 100:+.2f}%）",
              delta_color="inverse",  # 台股習慣：紅漲綠跌
              help="最近一個交易日的收盤價。底下的數字是跟前一天比漲（紅）或跌（綠）多少。")
    m2.metric("本益比 P/E", f"{pe_now:.1f} 倍" if ok(pe_now) else "—",
              help="白話：用現在的價格買，要靠公司賺錢「幾年」才能回本。數字越低通常越便宜，但要跟同產業比較才準。ETF 沒有這個數字。")
    m3.metric("近四季 EPS", money(eps_now),
              help="每股盈餘：公司過去一年「每一股」幫你賺了多少錢。數字越大越會賺錢。（來源：公開資訊觀測站財報）")
    m4.metric("殖利率", pct(yld),
              help=f"白話：放一年大約能領回股價的幾 % 當現金股息。近一年配息合計 {money(div_ttm)}。台股一般 4~6% 算不錯。")

# ============================================================
# 12. 畫面：價格位階
# ============================================================
# 股價評估、韭菜分析放左邊（寬度約 75%），公司動態放右邊同一高度
eval_col, news_col = st.columns([3, 1], gap="medium")
with news_col:
    news_slot = st.container()  # 公司動態，資料最後再填

with eval_col, st.container(border=True):
    st.markdown("#### 股價評估")
    zone = None
    if val is None:
        st.info("這支股票目前沒有足夠的 EPS 或配息資料（例如公司虧損、剛上市），無法估算價格位階。")
    else:
        zone = price_zone(price, val)
        cheap, fair, exp_ = val["cheap"], val["fair"], val["expensive"]
        lo_edge, hi_edge = min(cheap * 0.85, price * 0.95), max(exp_ * 1.15, price * 1.05)
        to_pos = lambda x: (x - lo_edge) / (hi_edge - lo_edge) * 100
        pc, pf, pe_ = to_pos(cheap), to_pos(fair), to_pos(exp_)
        pp = float(np.clip(to_pos(price), 4, 96))
        zone_name = {"cheap": "便宜區", "fair_low": "合理偏低", "fair_high": "合理偏高", "expensive": "昂貴區"}[zone]
        st.markdown(f"""
<div class="zone-wrap">
  <div class="zone-marker" style="left:{pp}%">現在 {money(price)}<br>▼</div>
  <div class="zone-bar" style="background:linear-gradient(90deg,
       #2ecc71 0%, #2ecc71 {pc}%, #f1c40f {pc}%, #f1c40f {pe_}%, #e74c3c {pe_}%, #e74c3c 100%);"></div>
</div>
<div class="zone-ticks">
  <div class="zone-tick" style="left:{pc}%">｜<br>便宜價</div>
  <div class="zone-tick" style="left:{pf}%">｜<br>合理價</div>
  <div class="zone-tick" style="left:{pe_}%">｜<br>昂貴價</div>
</div>
<p>目前位置：<b>{zone_name}</b></p>
""", unsafe_allow_html=True)

        if val["method"] == "pe":
            how = f"近四季 EPS {money(eps_now)} × 歷史本益比 {val['low_mult']:.1f} / {val['mid_mult']:.1f} / {val['high_mult']:.1f} 倍"
            est_eps, est_src = forecast_eps(cum, eps_now)
            target = est_eps * val["mid_mult"] if ok(est_eps) else None
            t_low = est_eps * val["low_mult"] if ok(est_eps) else None
            t_high = est_eps * val["high_mult"] if ok(est_eps) else None
            t_note, t_help = f"預估 EPS {money(est_eps)} × 合理本益比 {val['mid_mult']:.1f} 倍", est_src
        else:
            how = f"近一年配息 {money(div_ttm)} ÷ 歷史殖利率 {pct(val['high_yield'])} / {pct(val['mid_yield'])} / {pct(val['low_yield'])}"
            target, t_low, t_high = fair, cheap, exp_
            t_note = "ETF／無 EPS 標的不適用本益比，以合理價作參考"
            t_help = "殖利率越高代表價格越便宜，所以「便宜價」對應的是歷史上的高殖利率。"

        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f'<div class="price-card pc-green"><div class="t">便宜價</div><div class="v">{money(cheap)}</div>'
                    f'<div class="d">低於這個價格，算是打折</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="price-card pc-yellow"><div class="t">合理價</div><div class="v">{money(fair)}</div>'
                    f'<div class="d">過去大部分時間的中間價位</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="price-card pc-red"><div class="t">昂貴價</div><div class="v">{money(exp_)}</div>'
                    f'<div class="d">高於這個價格，小心買貴</div></div>', unsafe_allow_html=True)
        k4.markdown(f'<div class="price-card pc-blue" title="{t_help}"><div class="t">預測目標價</div><div class="v">{money(target)}</div>'
                    f'<div class="d">區間 {money(t_low, 0)} ~ {money(t_high, 0)}</div></div>', unsafe_allow_html=True)
        st.caption(f"算法：{how}（依據：{val['note']}）｜目標價：{t_note}".replace("$", "\\$"))

# ============================================================
# 13. 畫面：老師白話講
# ============================================================
with eval_col, st.container(border=True):
    st.markdown("#### 韭菜分析")
    if zone is None:
        st.write("資料不足，暫時無法產生摘要。可以先看下方走勢圖了解股價方向。")
    else:
        sentences, (label, color, reason) = build_summary(price, val, zone, yld, trend, rsi_now, ma20_now, is_etf)
        st.markdown(f'<span class="pill pill-{color}">{label}</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary">{"".join(sentences)}</div>', unsafe_allow_html=True)
        st.markdown(f'<p class="muted">{reason}</p>', unsafe_allow_html=True)
    st.caption("*僅供學習參考，不是投資建議。")

# ============================================================
# 14. 畫面：技術線型與籌碼（K線、成交量、外資、投信、融資、KD、DMI）
# ============================================================
RED, GREEN = "#e5383b", "#2a9d5c"  # 台股習慣：紅漲綠跌
LINE_BLACK = "#111111"  # 圖上的橫線、虛線統一用黑色，比較清楚
GRID = dict(showgrid=True, gridcolor="rgba(0,0,0,0.45)", gridwidth=0.6, zeroline=True, zerolinecolor=LINE_BLACK, zerolinewidth=1)


def bar_colors(values):
    return [RED if (v or 0) >= 0 else GREEN for v in values]


# 線圖放整排；每張圖下面直接寫白話解讀
with st.container(border=True):
    st.markdown("#### 線圖與籌碼")
    span = st.radio("看多久的資料？", ["3 個月", "6 個月"], horizontal=True,
                    help="籌碼資料要一天一天從交易所下載。選 6 個月第一次比較久，下載過的日子會存起來，之後就很快。")
    n_days = {"3 個月": 63, "6 個月": 126}[span]

    ohlc = data["ohlc"]
    k_all, d_all = calc_kd(ohlc)
    pdi_all, mdi_all, adx_all = calc_dmi(ohlc)
    ma5 = close.rolling(5).mean()
    w = ohlc.iloc[-n_days:]
    try:
        chips = load_chips(code, market, [d.date() for d in w.index])
    except DataError as e:
        st.warning(f"籌碼資料暫時抓不到，先只顯示股價線型。（{e}）")
        chips = pd.DataFrame(index=w.index, columns=["foreign", "trust", "margin"], dtype=float)
    chips = chips.reindex(w.index)

    x = [d.strftime("%Y/%m/%d") for d in w.index]  # 用文字當 X 軸，假日就不會留空白
    sel = lambda s: s.reindex(w.index)

    # ---- 白話解讀（每張圖下面用）----
    tip = {}
    last5 = chips.iloc[-5:]
    for col_name, nm in (("foreign", "外資"), ("trust", "投信")):
        s5 = last5[col_name].dropna()
        if len(s5):
            tot = s5.sum()
            buy_days, sell_days = int((s5 > 0).sum()), int((s5 < 0).sum())
            if abs(tot) < 1:
                tip[col_name] = f"近 5 個交易日幾乎沒有進出，對股價影響不大。"
            else:
                tip[col_name] = (f"近 5 個交易日{'買超' if tot > 0 else '賣超'} {abs(tot):,.0f} 張"
                                 f"（{buy_days} 天買、{sell_days} 天賣）。"
                                 + ("大戶在進場。" if tot > 0 else "大戶在調節持股。"))
    m5 = chips["margin"].dropna()
    if len(m5) >= 6:
        diff = m5.iloc[-1] - m5.iloc[-6]
        tip["margin"] = ("近 5 日幾乎沒有變化，散戶槓桿持平。" if abs(diff) < 1 else
                         f"近 5 日{'增加' if diff > 0 else '減少'} {abs(diff):,.0f} 張。"
                         + ("散戶借錢買進變多，股價下跌時賣壓可能變大。" if diff > 0 else "散戶槓桿在下降，籌碼變得比較乾淨。"))
    k_now, d_now = k_all.iloc[-1], d_all.iloc[-1]
    k_prev, d_prev = k_all.iloc[-2], d_all.iloc[-2]
    cross = ("剛出現**黃金交叉**（K 往上穿過 D），短線轉強訊號。" if k_prev <= d_prev and k_now > d_now else
             "剛出現**死亡交叉**（K 往下穿過 D），短線轉弱訊號。" if k_prev >= d_prev and k_now < d_now else
             "K 在 D 上面，短線偏強。" if k_now > d_now else "K 在 D 下面，短線偏弱。")
    zone_kd = "，數值在 80 以上屬於過熱區" if k_now >= 80 else "，數值在 20 以下屬於超賣區" if k_now <= 20 else ""
    tip["kd"] = f"K = {k_now:.0f}、D = {d_now:.0f}{zone_kd}。{cross}"
    p_now, m_now, a_now = pdi_all.iloc[-1], mdi_all.iloc[-1], adx_all.iloc[-1]
    if ok(p_now) and ok(m_now):
        tip["dmi"] = (f"{'多方力道（+DI）大於空方' if p_now > m_now else '空方力道（−DI）大於多方'}，"
                      + (f"ADX {a_now:.0f} 在 25 以上，代表目前趨勢明確。" if ok(a_now) and a_now >= 25
                         else f"ADX {a_now:.0f} 低於 25，代表目前沒有明顯趨勢、比較像盤整。" if ok(a_now) else ""))
    c_now, m20, m60 = close.iloc[-1], ma20.iloc[-1], ma60.iloc[-1]
    if ok(m20) and ok(m60):
        tip["k"] = ("股價在月線、季線上面，走勢偏強。" if c_now > m20 and c_now > m60 else
                    "股價跌到月線、季線下面，走勢偏弱。" if c_now < m20 and c_now < m60 else
                    "股價在月線和季線之間，方向還不明確。")
    v5, v20 = w["vol"].iloc[-5:].mean(), w["vol"].iloc[-20:].mean()
    if ok(v5) and ok(v20) and v20:
        r = v5 / v20
        tip["vol"] = ("近 5 日成交量比近一個月平均多很多，買賣變熱絡。" if r >= 1.3 else
                      "近 5 日成交量比近一個月平均少，交易比較冷清。" if r <= 0.7 else "近 5 日成交量跟近一個月平均差不多。")

    def chart(title, fig, height, key, legend=False):
        """畫一張小圖，下面接白話解讀"""
        st.markdown(f"<div class='chart-t'>{title}</div>", unsafe_allow_html=True)
        fig.update_layout(height=height, margin=dict(l=8, r=8, t=30 if legend else 6, b=8), hovermode="x unified",
                          bargap=0.15, hoverdistance=40, showlegend=legend,
                          hoverlabel=dict(font_size=17, bgcolor="white", bordercolor="#111111", font_color="#111111"),
                          legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0, font=dict(size=11)))
        fig.update_xaxes(type="category", rangeslider_visible=False, nticks=8, showgrid=False)
        fig.update_yaxes(**GRID)
        st.plotly_chart(fig, key=f"chart_{key}")
        if tip.get(key):
            txt = re.sub(r"[*][*](.+?)[*][*]", r"<b>\1</b>", tip[key])  # **粗體** 改成 HTML 粗體
            st.markdown(f"<div class='chart-tip'>{txt}</div>", unsafe_allow_html=True)

    # ① K 線 + 均線
    f = go.Figure()
    f.add_trace(go.Candlestick(x=x, open=w["open"], high=w["high"], low=w["low"], close=w["close"], name="K 線",
                               increasing=dict(line=dict(color=RED, width=2.2), fillcolor=RED),
                               decreasing=dict(line=dict(color=GREEN, width=2.2), fillcolor=GREEN),
                               whiskerwidth=0.4, showlegend=False))  # 外框加粗，K 棒比較好指
    for s, nm, col in ((ma5, "5日線", "#64748b"), (ma20, "20日線（月線）", "#f59e0b"), (ma60, "60日線（季線）", "#a855f7")):
        f.add_trace(go.Scatter(x=x, y=sel(s), name=nm, line=dict(color=col, width=1.4), hovertemplate="%{y:,.2f}"))
    if val is not None:
        y_lo, y_hi = float(w["low"].min()), float(w["high"].max())
        for lv, txt, col in ((val["cheap"], "便宜價", "#2ecc71"), (val["fair"], "合理價", "#d4a017"), (val["expensive"], "昂貴價", RED)):
            if y_lo * 0.9 <= lv <= y_hi * 1.1:
                f.add_hline(y=lv, line=dict(color=LINE_BLACK, width=1.2, dash="dash"),
                            annotation_text=txt, annotation_position="top right", annotation_font_color=col)
    chart("K 線（股價）", f, 380, "k", legend=True)

    # 張數 → 金額（1 張 = 1,000 股，用當天收盤價估算）
    def amt(lots):
        out = []
        for n, c in zip(lots, w["close"]):
            if not ok(n) or not ok(c):
                out.append("—")
                continue
            v = float(n) * 1000 * float(c)
            sign = "-" if v < 0 else ""
            v = abs(v)
            out.append(f"{sign}{v / 1e8:,.2f} 億元" if v >= 1e8 else f"{sign}{v / 1e4:,.0f} 萬元")
        return out

    # ② 外資 ③ 投信
    for col_name, nm in (("foreign", "外資"), ("trust", "投信")):
        v = chips[col_name]
        f = go.Figure(go.Bar(x=x, y=v, marker_color=bar_colors(v), name=nm, customdata=amt(v),
                             hovertemplate=nm + " %{y:+,.0f} 張<br>約 %{customdata}<extra></extra>"))
        chart(f"{nm}買賣超（張）", f, 170, col_name)

    # ④ 融資餘額
    f = go.Figure(go.Scatter(x=x, y=chips["margin"], name="融資餘額", fill="tozeroy",
                             line=dict(color="#e76f51", width=1.6), fillcolor="rgba(231,111,81,.12)",
                             customdata=amt(chips["margin"]),
                             hovertemplate="融資 %{y:,.0f} 張<br>約 %{customdata}<extra></extra>"))
    m_ok = chips["margin"].dropna()
    if len(m_ok):
        f.update_yaxes(range=[m_ok.min() * 0.97, m_ok.max() * 1.03])
    chart("融資餘額（張）", f, 170, "margin")

    # ⑤ 成交量
    vol_col = [RED if c >= o else GREEN for o, c in zip(w["open"], w["close"])]
    f = go.Figure(go.Bar(x=x, y=w["vol"], marker_color=vol_col, name="成交量", customdata=amt(w["vol"]),
                         hovertemplate="成交 %{y:,.0f} 張<br>約 %{customdata}<extra></extra>"))
    vol5 = w["vol"].rolling(5).mean()
    f.add_trace(go.Scatter(x=x, y=vol5, name="5日均量", line=dict(color="#2563eb", width=1.2), customdata=amt(vol5),
                           hovertemplate="5日均量 %{y:,.0f} 張（約 %{customdata}）<extra></extra>"))
    chart("成交量（張）", f, 170, "vol")

    # ⑥ KD
    f = go.Figure()
    f.add_trace(go.Scatter(x=x, y=sel(k_all), name="K 值", line=dict(color="#2563eb", width=1.4), hovertemplate="K %{y:.1f}"))
    f.add_trace(go.Scatter(x=x, y=sel(d_all), name="D 值", line=dict(color="#f59e0b", width=1.4), hovertemplate="D %{y:.1f}"))
    for lv in (20, 80):
        f.add_hline(y=lv, line=dict(color=LINE_BLACK, width=1, dash="dot"))
    f.update_yaxes(range=[0, 100])
    chart("KD 指標", f, 210, "kd", legend=True)

    # ⑦ DMI
    f = go.Figure()
    f.add_trace(go.Scatter(x=x, y=sel(pdi_all), name="+DI 多方", line=dict(color=RED, width=1.4), hovertemplate="+DI %{y:.1f}"))
    f.add_trace(go.Scatter(x=x, y=sel(mdi_all), name="−DI 空方", line=dict(color=GREEN, width=1.4), hovertemplate="−DI %{y:.1f}"))
    f.add_trace(go.Scatter(x=x, y=sel(adx_all), name="ADX 趨勢強度", line=dict(color=LINE_BLACK, width=1.4, dash="dot"),
                           hovertemplate="ADX %{y:.1f}"))
    dmi_max = pd.concat([sel(pdi_all), sel(mdi_all), sel(adx_all)]).max()
    f.update_yaxes(range=[0, float(dmi_max) * 1.1 if ok(dmi_max) else 60])
    chart("DMI 趨向指標", f, 210, "dmi", legend=True)

    with st.expander("每張圖怎麼看？"):
        st.markdown("""
- **K 線**：每一根代表一天。**紅色＝收盤比開盤高（漲）**，**綠色＝收盤比開盤低（跌）**；上下細線是當天最高、最低價。
- **成交量**：當天買賣了多少張。價格上漲又大量，代表很多人搶著買；價格下跌又大量，代表很多人急著賣。
- **外資／投信買賣超**：紅色柱子＝那天買得比賣得多（買超），綠色＝賣超。外資是國外大型機構，投信是國內基金公司，
  兩者被視為「大戶」，連續買超通常是好現象。
- **融資餘額**：散戶「借錢買股票」的總張數。股價下跌但融資一直增加，代表散戶在攤平、之後賣壓可能較大。
- **KD 指標**：0~100 的短線強弱計。K 往上穿過 D 叫黃金交叉（轉強），往下穿過叫死亡交叉（轉弱）；80 以上過熱、20 以下超賣。
- **DMI**：+DI（紅）是多方力道，−DI（綠）是空方力道，誰在上面誰佔優勢；ADX（黑色點線）超過 25 代表趨勢明確，低於 20 代表盤整。
- 資料來源：證交所／櫃買中心每日公布的三大法人買賣超與融資融券餘額（收盤後約 16:00~21:30 陸續公布）。
""")


# ============================================================
# 15. 畫面：三率 + 財報股利
# ============================================================
fin_l, fin_r = st.columns(2, gap="medium")

with fin_l, st.container(border=True):
    st.markdown("#### 三率")
    sqm = single_quarter_margins(data.get("cum_margin", {})) if not is_etf else {}
    keys = sorted(k for k, v in sqm.items() if all(ok(x) for x in v))[-8:]
    if is_etf:
        st.caption("ETF 是一籃子股票，沒有自己的毛利率、營益率、淨利率。")
    elif not keys:
        st.caption("公開資訊觀測站查無這家公司的三率（金融業如銀行、保險沒有毛利率，所以不會有這項資料）。")
    else:
        cur = sqm[keys[-1]]
        prv = sqm[keys[-2]] if len(keys) > 1 else (None, None, None)
        q_label = f"{keys[-1][0] - 1911} 年 Q{keys[-1][1]}"
        helps = (
            "賣東西的價差。每賣 100 元，扣掉進貨／製造成本後還剩多少。越高代表產品越有競爭力、越不怕削價競爭。",
            "本業賺多少。毛利再扣掉人事、研發、行銷等營運費用後還剩多少。這是公司「本業」真正的獲利能力。",
            "最後放進口袋多少。再加減業外收支、扣完稅之後，每 100 元營收真正賺到的錢。",
        )
        m1, m2, m3 = st.columns(3)
        for col, nm, v, p, hp in zip((m1, m2, m3), ("毛利率", "營益率", "淨利率"), cur, prv, helps):
            col.metric(nm, f"{v:.1f}%", delta=f"{v - p:+.1f} 個百分點" if ok(p) else None,
                       delta_color="inverse", help=hp)
        st.caption(f"最新一季：{q_label}（和上一季相比；紅色＝變好，綠色＝變差）")

        x = [f"{y - 1911}Q{s}" for y, s in keys]
        fig_m = go.Figure()
        for i, (nm, col) in enumerate((("毛利率", "#3f7d20"), ("營益率", "#2563eb"), ("淨利率", "#f59e0b"))):
            fig_m.add_trace(go.Scatter(x=x, y=[sqm[k][i] for k in keys], name=nm, mode="lines+markers",
                                       line=dict(color=col, width=2), hovertemplate=nm + " %{y:.1f}%<extra></extra>"))
        fig_m.update_layout(height=260, margin=dict(l=8, r=8, t=10, b=8), hovermode="x unified",
                            hoverlabel=dict(font_size=17, bgcolor="white", bordercolor="#111111", font_color="#111111"), 
                            legend=dict(orientation="h", y=1.15, x=0), yaxis=dict(ticksuffix="%", **GRID),
                            xaxis=dict(type="category", showgrid=False))
        st.plotly_chart(fig_m)
        trend_txt = []
        for i, nm in enumerate(("毛利率", "營益率", "淨利率")):
            if len(keys) >= 4:
                chg = sqm[keys[-1]][i] - sqm[keys[-4]][i]
                trend_txt.append(f"{nm}{'上升' if chg > 0.5 else '下滑' if chg < -0.5 else '持平'}")
        if trend_txt:
            ups = sum("上升" in t for t in trend_txt)
            downs = sum("下滑" in t for t in trend_txt)
            verdict = ("三率一起往上，俗稱「三率三升」，代表公司越來越會賺錢。" if ups == 3 else
                       "三率一起往下，俗稱「三率三降」，賺錢能力在變弱，要留意。" if downs == 3 else
                       "三率都差不多，獲利能力很穩定。" if ups == 0 and downs == 0 else
                       "三率有升有降，獲利能力沒有明顯方向。")
            st.markdown(f"**跟三季前比**：{'、'.join(trend_txt)}。{verdict}")
        st.caption("來源：公開資訊觀測站 營益分析彙總表（已換算成單季數字）")

with fin_r, st.container(border=True, key="fin_box"):
    st.markdown("#### 財報與股利")
    avg_px_year = close.groupby(close.index.year).mean()
    # 股利年度資料
    if not is_etf:
        by_year = {}
        for r in div_rows:
            fy = int(r["period"][:3]) + 1911 if r["period"][:3].isdigit() else r["end"].year
            by_year[fy] = by_year.get(fy, 0) + r["cash"]
        year_label = "年度"
    else:
        by_year = exdiv.groupby(exdiv.index.year).sum().to_dict() if len(exdiv) else {}
        year_label = "除息年度"

    # 上面一排：單季 EPS（左）、股利（右），兩個小表格並排
    e_col, d_col = st.columns(2, gap="small")
    with e_col:
        st.markdown("##### 單季 EPS")
        if is_etf:
            st.caption("ETF 沒有 EPS。")
        else:
            sq = single_quarter_eps(cum)
            if sq:
                last4 = sorted(sq)[-4:][::-1]
                st.dataframe(pd.DataFrame({
                    "季度": [f"{y - 1911} 年 Q{s}" for y, s in last4],
                    "EPS (NT$)": [f"{sq[k]:,.2f}" for k in last4],
                }), hide_index=True)
                st.caption("單季＝本季累計 − 上季累計")
            else:
                st.caption("公開資訊觀測站查無這家公司的季度 EPS。")
    with d_col:
        st.markdown("##### 現金股利")
        if by_year:
            ys = sorted(by_year)[-5:][::-1]
            st.dataframe(pd.DataFrame({
                year_label: [str(y) for y in ys],
                "股利 (NT$)": [f"{by_year[y]:,.2f}" for y in ys],
                "殖利率": [pct(by_year[y] / avg_px_year[y]) if y in avg_px_year.index else "—" for y in ys],
            }), hide_index=True)
            st.caption("殖利率＝當年股利 ÷ 當年平均股價。今年還沒配完，數字會偏低。")
        else:
            st.caption("查無配息紀錄。")

    # 下面：月營收
    if not is_etf:
        # ---- 月營收：月增、年增 ----
        st.markdown("##### 月營收")
        rev_rows = []
        try:
            with st.spinner("讀取月營收（第一次約 20 秒）…"):
                y, m = TODAY.year, TODAY.month
                for _ in range(7):  # 從上個月往回找，湊滿 6 個月
                    y, m = (y, m - 1) if m > 1 else (y - 1, 12)
                    month = mops_revenue_month(market, y, m)
                    if month and code in month:
                        rev_rows.append((y, m, *month[code]))
                    if len(rev_rows) == 6:
                        break
        except DataError as e:
            st.caption(f"{e}")
        if rev_rows:
            def chg(a, b):
                return (a - b, (a - b) / b * 100) if ok(a) and ok(b) and b else (None, None)
            tbl = []
            for y, m, cur, prev, ly in rev_rows:
                mom, mom_p = chg(cur, prev)
                yoy, yoy_p = chg(cur, ly)
                tbl.append({
                    "月份": f"{y - 1911}/{m:02d}",
                    "營收（億）": f"{cur / 1e5:,.2f}",
                    "月增（億）": f"{mom / 1e5:+,.2f}" if mom is not None else "—",
                    "月增 %": f"{mom_p:+.1f}%" if mom_p is not None else "—",
                    "年增（億）": f"{yoy / 1e5:+,.2f}" if yoy is not None else "—",
                    "年增 %": f"{yoy_p:+.1f}%" if yoy_p is not None else "—",
                })
            color = lambda v: "color:#e5383b" if str(v).startswith("+") else ("color:#2a9d5c" if str(v).startswith("-") else "")
            df_rev = pd.DataFrame(tbl)
            sty = df_rev.style
            sty = (sty.map if hasattr(sty, "map") else sty.applymap)(color, subset=["月增（億）", "月增 %", "年增（億）", "年增 %"])
            st.dataframe(sty, hide_index=True)
            st.caption("月增＝跟上個月比，年增＝跟去年同一個月比。紅色＝增加，綠色＝減少。"
                       "來源：公開資訊觀測站 每月營收（每月 10 日前公布上個月）")
        else:
            st.caption("查無這家公司的月營收資料。")


with fin_l, st.container(border=True, key="gloss_box"):
    st.markdown("#### 名詞小辭典")
    gq = st.text_input("想查什麼名詞？", key="gloss_q", label_visibility="collapsed",
                       placeholder="例如：PCB、MLCC、殖利率、CoWoS，或打公司名稱")

    def show_term(g, from_ai=False):
        term, zh, _, desc, cos = g
        title = f"{term}（{zh}）" if zh and zh != term else term
        st.markdown(f"<div class='gloss'><div class='gt'>{title}</div><div class='gd'>{desc}</div></div>",
                    unsafe_allow_html=True)
        if cos:
            st.caption("代表公司（點一下就查）" + ("：AI 整理，僅供參考" if from_ai else ""))
            cols = st.columns(4)
            for i, c in enumerate(cos):
                cols[i % 4].button(c, key=f"gco_{term}_{c}", on_click=set_q, args=(c.replace("-KY", ""),))

    if gq.strip():
        hits = glossary_search(gq)
        for g in hits[:5]:
            show_term(g)
        if len(hits) > 5:
            st.caption(f"還有 {len(hits) - 5} 個相關名詞，打完整一點會更準。")
        if not hits:
            st.caption(f"小辭典裡還沒有「{gq.strip()}」。")
            key = _gemini_key()
            cd = _macro_cooldown()
            if key and time.time() >= cd["until"]:
                if st.button(f"請 AI 解釋「{gq.strip()}」", key="gloss_ai_btn") or st.session_state.get("gloss_ai_for") == gq.strip():
                    st.session_state.gloss_ai_for = gq.strip()
                    try:
                        with st.spinner("AI 查詢中…"):
                            show_term(glossary_ai(gq.strip(), key), from_ai=True)
                    except ModuleNotFoundError:
                        pass
                    except Exception as e:
                        st.caption(_ai_failed(e))
            elif key:
                st.caption(f"AI 額度暫時用完，{datetime.fromtimestamp(cd['until']).strftime('%H:%M')} 之後可以再請 AI 解釋。")
    else:
        st.caption("常用：" + "、".join(g[0] for g in GLOSSARY[:9]) + "…")


def render_customers():
    if is_etf:
        return
    if re.search(r"金融|保險|銀行|證券", profile.get("industry", "")):  # 金融股不用問 AI
        cust_slot.markdown("<div class='biz'>主要客戶：一般民眾與公司行號</div>", unsafe_allow_html=True)
        return
    key = _gemini_key()
    if not key:
        return
    cd = _macro_cooldown()
    wait_msg = "主要客戶：AI 額度暫時用完，{t} 之後重新整理頁面就會補上"
    if time.time() < cd["until"]:
        cust_slot.markdown(f"<div class='biz muted'>{wait_msg.format(t=datetime.fromtimestamp(cd['until']).strftime('%H:%M'))}</div>",
                           unsafe_allow_html=True)
        return
    try:
        with cust_slot, st.spinner("AI 正在查主要客戶…"):
            custs = company_customers(code, name, key)
    except ModuleNotFoundError:
        return
    except Exception as e:
        _ai_failed(e)
        cust_slot.markdown(f"<div class='biz muted'>{wait_msg.format(t=datetime.fromtimestamp(cd['until']).strftime('%H:%M'))}</div>",
                           unsafe_allow_html=True)
        return
    txt = "、".join(custs) if custs else "查不到公開資料"
    cust_slot.markdown(f"<div class='biz'>主要客戶：{txt}<span class='muted'>（AI 整理，僅供參考）</span></div>",
                       unsafe_allow_html=True)


def render_news():
    with news_slot, st.container(border=True):
        st.markdown("#### 公司動態")
        if is_etf:
            st.caption("ETF 沒有公司重大訊息。")
            return


        try:
            with st.spinner("讀取近 1 個月重大訊息…"):
                news = mops_news(code)
        except DataError as e:
            st.caption(f"重大訊息暫時抓不到：{e}")
            return
        show_all = st.toggle("顯示全部公告（含人事等）", value=False, key="news_all")
        rows = news if show_all else [r for r in news if r[2]]
        if not rows:
            st.caption("近 1 個月沒有跟財務相關的公告。")
        html = ""
        for d, title, tag in rows[:15]:
            badge = f'<span class="t">{tag}</span>' if tag else ""
            html += f'<div class="news"><span class="d">{d:%m/%d}</span>{badge}{title}</div>'
        st.markdown(html, unsafe_allow_html=True)
        if len(rows) > 15:
            st.caption(f"只列最新 15 則，共 {len(rows)} 則。")
        with st.expander("這些分類代表什麼？"):
            st.markdown("\n".join(f"- **{t}**：{e}" for t, _, e in NEWS_TAGS))
        st.caption("來源：公開資訊觀測站「重大訊息」，公司自己發布的公告。")


render_news()
# ---------- 接下來一個月會影響這檔股票的事（跑馬燈）----------
def twse_exright():
    """證交所「除權除息預告表」：接下來要除權息的股票"""
    def fetch():
        j = get_json("twse", "https://www.twse.com.tw/rwd/zh/exRight/TWT48U?response=json")
        f = [str(x) for x in j.get("fields") or []]
        rows = j.get("data") or []
        if not f and j.get("tables"):
            t = j["tables"][0]
            f, rows = [str(x) for x in t.get("fields") or []], t.get("data") or []
        i_d = next((i for i, x in enumerate(f) if "日期" in x), None)
        i_c = next((i for i, x in enumerate(f) if "代號" in x), None)
        i_k = next((i for i, x in enumerate(f) if x.strip() in ("除權息", "除權/息", "權/息")), None)
        i_cash = next((i for i, x in enumerate(f) if "現金" in x), None)
        out = {}
        for r in rows:
            try:
                m = re.findall(r"\d+", str(r[i_d]))
                y = int(m[0]) + (1911 if int(m[0]) < 1000 else 0)
                d = date(y, int(m[1]), int(m[2]))
            except Exception:
                continue
            kind = str(r[i_k]).strip() if i_k is not None else "息"
            cash = num(r[i_cash]) if i_cash is not None else None
            out[str(r[i_c]).strip()] = (d.isoformat(), kind, cash)
        return out
    return cached(f"exright|{TODAY}", fetch, permanent=False, ttl=6 * 3600)


def upcoming_for_stock(today, days=31):
    """接下來 days 天內，跟這檔股票有關的事件。每件事：日期、標題、說明（點進去看的分析）"""
    end = today + timedelta(days=days)
    items = []
    tech = bool(set(themes) & {"晶圓代工", "IC 設計", "ASIC", "CoWoS", "AI 伺服器", "散熱", "PCB", "CCL", "ABF 載板",
                               "輝達概念股", "CPO", "矽光子", "光通訊", "記憶體模組", "DRAM", "封測"})
    fin = bool(re.search(r"金融|保險|銀行|證券", profile.get("industry", "")))

    # 1. 除權息（證交所預告表）
    try:
        ex = twse_exright().get(code)
    except DataError:
        ex = None
    if ex:
        d = date.fromisoformat(ex[0])
        if today <= d <= end:
            cash = ex[2]
            y = f"，以現在股價算殖利率約 {cash / price * 100:.2f}%" if ok(cash) and price else ""
            items.append((d, f"除{ex[1]}", f"{d:%m/%d} 除{ex[1]}" + (f"，每股配 {cash:g} 元" if ok(cash) else "") + "。" +
                          f"除息當天股價會先扣掉配息金額{y}。之後股價漲回除息前的價格叫「填息」，"
                          "填息快代表市場看好；如果你想領這次股息，要在除息日前一天收盤前買進。"))

    if not is_etf:
        # 2. 月營收：每月 10 日前公布上個月
        d = date(today.year, today.month, 10)
        if d < today:
            d = date(today.year + (today.month == 12), today.month % 12 + 1, 10)
        if d <= end:
            m = (d.month - 2) % 12 + 1
            last = globals().get("rev_rows") or []
            trend = ""
            if last:
                y0, m0, cur, prev, ly = last[0]
                if ok(cur) and ok(ly) and ly:
                    yoy = (cur - ly) / ly * 100
                    trend = (f"上一次公布的 {m0} 月營收年增 {yoy:+.1f}%。"
                             + ("如果這次繼續成長，代表生意持續變好；如果突然轉成衰退，股價可能會反應。" if yoy > 0
                                else "如果這次轉成成長，可能是好轉訊號；如果繼續衰退，要留意。"))
            items.append((d, f"{m} 月營收", f"{d:%m/%d} 前會公布 {m} 月營收。{trend}"
                          "月營收是最快能看到公司生意好壞的數字，公布後隔天股價常有反應。"))

        # 3. 財報：法定最晚公布日
        for (mm, dd), q in (((3, 31), "去年全年"), ((5, 15), "第 1 季"), ((8, 14), "第 2 季"), ((11, 14), "第 3 季")):
            d = date(today.year, mm, dd)
            if today <= d <= end:
                sqd = globals().get("sq") or {}
                eps_txt = ""
                if sqd:
                    k = sorted(sqd)[-1]
                    eps_txt = f"上一季（{k[0] - 1911} 年 Q{k[1]}）單季 EPS 是 {sqd[k]:.2f} 元，可以拿來跟這次比較。"
                items.append((d, f"{q}財報", f"{d:%m/%d} 是{q}財報最晚公布日，很多公司會提早公布。{eps_txt}"
                              "財報會告訴你這段時間真正賺了多少錢，比預期好或差都會影響股價。"))

    # 4. 總經：Fed、美國 CPI、台灣央行
    for e in macro_events(pd.Timestamp(today), days=days):
        kind_note = ""
        if e["short"] in ("Fed 利率", "美國 CPI", "非農就業"):
            if tech:
                kind_note = "這檔屬於科技／AI 題材，對美國利率比較敏感，公布前後股價可能波動比較大。"
            elif fin:
                kind_note = "金融股的獲利跟利率有關，利率維持高檔通常對銀行的利差有利。"
            else:
                kind_note = "這類消息會影響整個股市的氣氛，個股通常跟著大盤走。"
        elif e["short"] == "台灣央行":
            kind_note = ("金融股、營建股最受影響，要留意利率和房貸管制有沒有變。" if fin
                         else "對這檔股票的直接影響不大，主要影響銀行和營建股。")
        elif e["short"] == "Fed 會議紀錄":
            continue  # 影響小，不放進跑馬燈
        items.append((e["d"].date(), e["short"], f"台灣時間 {e['d']:%m/%d} {e['time']}：{e['name']}。{kind_note}"
                      f"建議：{e['strategy']}。"))
    return sorted(items, key=lambda x: x[0])


def render_ticker():
    """查詢欄下面的跑馬燈：事件由下往上捲動，填滿空位；點一下展開全部事件"""
    items = upcoming_for_stock(TODAY)
    with ticker_slot:
        if not items:
            st.caption("接下來一個月沒有查到會特別影響這檔股票的事件。")
            return
        cards = "".join(f"<div class='vt-item'><div class='vt-h'>{d:%m/%d}　{t}</div>"
                        f"<div class='vt-b'>{why}</div></div>" for d, t, why in items)
        secs = max(25, len(items) * 9)
        full = "".join(f"<div class='tk-item'><div class='tk-h'>{d:%m/%d}　{t}</div><div class='tk-b'>{why}</div></div>"
                       for d, t, why in items)
        st.markdown(f"""<details class="tk-box">
<summary><div class="vticker">
<div class="vt-win"><div class="vt-in" style="animation-duration:{secs}s">{cards}{cards}</div></div></div></summary>
<div class="tk-list">{full}
<div class="tk-note">除權息來自證交所預告表；財報、月營收是法定最晚公布日；Fed、CPI 來自官方公布的日期。僅供參考，不是投資建議。</div></div>
</details>""", unsafe_allow_html=True)


render_ticker()
render_customers()

with st.expander("這些價格是怎麼算出來的？"):
    st.markdown("""
- **資料來源**：EPS 和股利來自「公開資訊觀測站」，是公司依法申報的正式財報；股價來自證交所（上市）與櫃買中心（上櫃）。
- **個股（本益比法）**：回頭看過去 2 年，每個月的「月平均股價 ÷ 當時已公布的近四季 EPS」，
  取比較低的 10%、中間值、比較高的 10%，再乘上目前的近四季 EPS，就是便宜價、合理價、昂貴價。
- **ETF（殖利率法）**：ETF 沒有 EPS，所以改用過去 2 年的歷史殖利率。殖利率高的時候＝價格便宜，殖利率低的時候＝價格貴。
- **預測目標價**：預估 EPS × 合理本益比。預估 EPS 用「今年累計 EPS 比去年同期成長多少」來推算，並限制上下限避免太樂觀。
- **第一次查一支股票會比較慢**（約 1~2 分鐘），因為要從官方網站下載好幾年的資料，而且要放慢速度避免被網站擋下。
  下載過的資料會存在 app.py 旁邊的 `data_cache` 資料夾，之後打開就很快。
- 這些都是用「過去」推估「未來」，遇到產業大變動時可能失準，請當作參考尺，不要當成保證。
""")
