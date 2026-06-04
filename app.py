import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import graphviz
import yfinance as yf
from datetime import datetime, timedelta
import calendar
import time

# ==========================================
# 0. AYARLAR & AGRESİF DARK MODE CSS
# ==========================================
st.set_page_config(layout="wide", page_title="AETHER APEX V700 DIAMOND", page_icon="🏛️")

st.markdown("""
    <style>
    .stApp { background-color: #050505 !important; color: #e0e0e0 !important; }
    p, h1, h2, h3, h4, h5, h6, span, label, div { color: #e0e0e0 !important; }
    div[data-baseweb="select"] > div { background-color: #111111 !important; color: #ffffff !important; border: 1px solid #00ff88 !important; }
    div[data-baseweb="popover"] > div { background-color: #111111 !important; }
    ul[role="listbox"] { background-color: #111111 !important; }
    ul[role="listbox"] li { color: #ffffff !important; background-color: #111111 !important; }
    ul[role="listbox"] li:hover { background-color: #222222 !important; color: #00ff88 !important; font-weight: bold !important; }
    [data-testid="stTable"], [data-testid="stDataFrame"] { background-color: #111111 !important; }
    th { background-color: #222222 !important; color: #00ff88 !important; border-bottom: 1px solid #444 !important; }
    td { border-bottom: 1px solid #333 !important; color: #ffffff !important; }
    [data-testid="stExpander"] { background-color: #111111 !important; border: 1px solid #333 !important; border-radius: 8px !important; }
    [data-testid="stExpander"] summary p { color: #00ff88 !important; font-weight: bold !important; font-size: 1.1rem !important; }
    div.stButton > button { background-color: #1a1a1a !important; color: #ffffff !important; border: 1px solid #444 !important; border-radius: 8px !important; }
    div.stButton > button:hover { border-color: #00ff88 !important; color: #00ff88 !important; }
    .battery-container { width: 100%; background-color: #222; border-radius: 10px; margin: 5px 0 15px 0; border: 1px solid #444; position: relative; height: 25px; overflow: hidden; }
    .battery-fill { height: 100%; border-radius: 8px; transition: width 0.5s ease; display: flex; align-items: center; justify-content: flex-end; padding-right: 10px; font-weight: bold; color: #000 !important; font-size: 0.9rem; }
    .valuation-gap-card { background: linear-gradient(145deg, #111 0%, #0a0a0a 100%); padding: 20px; border-radius: 12px; border: 1px solid #333; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.5); }
    .valuation-leader { color: #00ff88; font-weight: 900; font-size: 1.2rem; }
    .valuation-laggard { color: #f1c40f; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

if 'active_trigger' not in st.session_state: st.session_state.active_trigger = "OPEX PINNING"
if 'macro_nonce' not in st.session_state: st.session_state.macro_nonce = str(time.time())
if 'battery_nonce' not in st.session_state: st.session_state.battery_nonce = str(time.time())

# ==========================================
# 1. KURUMSAL NİŞ ETF & HİSSE EVRENİ
# ==========================================
MAIN_SECTORS = {
    "XLK": "Ana Sektör: Teknoloji", "XLI": "Ana Sektör: Sanayi", "XLE": "Ana Sektör: Enerji",
    "XLV": "Ana Sektör: Sağlık", "XLF": "Ana Sektör: Finans", "XLY": "Ana Tüketim",
    "XLB": "Ana Sektör: Materyal", "XLC": "Ana Sektör: İletişim", "XLRE": "Ana Sektör: Gayrimenkul",
    "XLU": "Ana Sektör: Kamu Hizmetleri"
}

GLOBAL_MAP = {
    "Teknoloji (Bulut & AI)": ["XLK", "CLOU", "IGV", "AIQ", "CIBR", "BOTZ", "CYBER"],
    "Yarı İletken (Çip Mimarisi)": ["SOXX", "SMH", "EUV", "PHOTON"],
    "Enerji & Altyapı": ["XLE", "XOP", "OIH", "XLU", "URA", "ICLN", "PAVE", "JOUL"],
    "Emtia & Madencilik": ["COPX", "LIT", "REMX", "GDX", "XME"],
    "Lojistik & Havacılık": ["IYT", "JETS", "HULL"],
    "Savunma & Uzay": ["XAR", "ARKX", "UFO", "SPACE_RACE"],
    "Finans & Kripto": ["XLF", "KRE", "ARKF", "IBIT", "WGMI"],
    "Gayrimenkul & Veri Merkezleri": ["XLRE", "REZ", "SRVR", "VNQ"],
    "Özel Durumlar (IPO/Trump)": ["TRUMP_PF", "RECENT_IPO"]
}

ETF_INFO = {
    "XLU": {"area": "Utilities & Şebeke", "stocks": ["NEE", "SO", "DUK", "CEG", "AEP", "SRE", "D", "ETR", "VST", "XEL"]},
    "PAVE": {"area": "Altyapı Yenileme", "stocks": ["ETN", "PH", "HUBB", "POWL", "TT", "CARR", "JCI", "URI", "FAST", "GWW", "VMC", "MLM", "EXP", "J", "ACM", "PWR", "EME"]},
    "XLK": {"area": "Teknoloji Devleri", "stocks": ["NVDA", "AAPL", "MSFT", "MU", "AVGO", "AMD", "INTC", "CSCO", "PLTR", "AMAT"]},
    "IGV": {"area": "Yazılım ve SaaS", "stocks": ["MSFT", "CRM", "ORCL", "ADBE", "NOW", "INTU", "WDAY", "PLTR", "PAYC", "SNOW", "DDOG", "DT", "TEAM", "PANW", "CRWD", "NET"]},
    "SMH": {"area": "Global Çip Dökümhaneleri", "stocks": ["TSM", "INTC", "ASML", "NVDA", "AMD", "AVGO", "MRVL", "QCOM", "AMAT", "LRCX", "KLAC"]},
    "URA": {"area": "Uranyum ve Nükleer", "stocks": ["CCJ", "KAP", "NXE", "UEC", "UUUU", "DNN", "BWXT", "LEU", "SMR", "CEG"]},
    "WGMI": {"area": "Bitcoin Madenciliği", "stocks": ["MARA", "RIOT", "CLSK", "HUT", "CIFR", "IREN", "WULF", "CORZ", "HIVE", "BTDR", "NVDA", "AMD"]},
    "PHOTON": {"area": "Fotonik ve Optik Ekosistemi", "stocks": ["IQE", "AXTI", "AAOI", "AEHR", "LWLG", "WOLF", "OPTX", "VIAV", "HIMX", "LITE", "STM", "CIEN", "TSEM", "GFS", "UMC", "MRVL", "FORM", "MTSI", "POET", "ASX", "SMTC", "LASR", "VECO", "COHR", "PLTR", "TER", "LRCX", "ONTO", "AMAT", "AMKR", "SANM", "FN", "CRDO", "TECK"]},
    "QUANT": {"area": "Kuantum Bilişim", "stocks": ["ARQQ", "QBTS", "RGTI", "QUBT", "IONQ", "GFS", "IBM", "COHR", "HON", "TSEM", "MRVL", "GOOGL", "FORM", "RTX", "MSFT", "RDNT", "NVDA", "INTC", "BIDU", "BABA"]},
    "CYBER": {"area": "Global Siber Güvenlik", "stocks": ["ZS", "TENB", "OKTA", "FFIV", "CRWD", "S", "RPD", "BAH", "FTNT", "CHKP", "PANW", "NET", "VRNS", "LDOS", "CSCO", "SCWX"]},
    "SPACE_RACE": {"area": "SpaceX & Uzay", "stocks": ["TSLA", "RKLB", "ASTS", "FLY", "SATS", "PL", "AMZN", "TMUS", "QCOM", "SATL", "SPIR", "IRDM", "GLW", "LUNR", "BKSY", "VSAT", "MDA", "RDW", "DCO", "ATRO", "VOYG", "ARKX", "HON", "LMT", "LHX", "BA", "NOC", "RTX", "HEI", "TDG", "SPCE", "YSS", "SIDU"]},
    "MEMORY_AI": {"area": "Hafıza & Veri", "stocks": ["MU", "ALAB", "MRVL", "DELL", "NTAP", "PSTG", "HPE", "IBM", "STX", "WDC"]},
    "TRUMP_PF": {"area": "Trump Portföyü", "stocks": ["DELL", "TXN", "DVA", "JBL", "KLAC", "MARA", "ETN", "AVGO", "NVDA", "TT", "MSTR", "COST", "CDNS", "AAPL", "SNPS", "MSI", "PNC", "ORCL", "ICE", "NFLX", "COIN", "UBER", "HD", "MSFT", "CVNA", "NVR", "ADBE", "CRM", "NOW", "WDAY"]},
    "RECENT_IPO": {"area": "Halka Arzlar", "stocks": ["CDNL", "AMBQ", "Q", "SOLS", "CRCL", "FPS", "PTRN", "BLLN", "PAYP", "BLSH", "VOYG", "NAVN", "XE", "AVEX", "ETOR", "GLOO", "FIGR", "YSS", "SOLV", "ARXS", "ELMT", "OMDA"]}
}

FUTURE_THEMES_MAP = {
    "Chokepoint (Darboğaz) Çarpanları": ["NVDA", "AVGO", "CEG", "ETN", "EQIX", "FCX", "PLD"],
    "Agentic AI & Yazılım": ["NOW", "ADEA", "DOCN", "SOUN", "ADBE", "DT", "S", "EXTR"],
    "Uzay Bilişimi & Keşif": ETF_INFO["SPACE_RACE"]["stocks"],
    "Kuantum Bilişim (Quantum)": ETF_INFO["QUANT"]["stocks"],
    "Fotonik & Optik Çipler": ETF_INFO["PHOTON"]["stocks"],
    "Hafıza Katmanları (Memory)": ETF_INFO["MEMORY_AI"]["stocks"],
    "Neocloud & Enerji Pivotu": ["IREN", "APLD", "CIFR", "WULF", "CORZ", "BTDR", "CLSK", "MARA", "RIOT"],
    "Nükleer & Temel Materyal": ["CEG", "TLN", "SMR", "NNE", "UUUU", "MP", "CRML", "ATLX"]
}

SYSTEM_TRIGGERS = {
    "GAMMA SQUEEZE": {"color": "#00ff88", "battery": {"Stocks": 95, "Bonds": 20, "Crypto": 90, "Commodities": 55, "RealEstate": 65}},
    "OPEX PINNING": {"color": "#f1c40f", "battery": {"Stocks": 50, "Bonds": 50, "Crypto": 48, "Commodities": 52, "RealEstate": 50}},
    "GEOPOLITICAL SHOCK": {"color": "#ff3333", "battery": {"Stocks": 25, "Bonds": 85, "Crypto": 35, "Commodities": 95, "RealEstate": 40}},
    "STAGFLATION / SUPPLY SUPER-CYCLE": {"color": "#e67e22", "battery": {"Stocks": 40, "Bonds": 15, "Crypto": 60, "Commodities": 98, "RealEstate": 75}},
    "FED HAWKISH PIVOT / LIQUIDITY CRUNCH": {"color": "#9b59b6", "battery": {"Stocks": 15, "Bonds": 90, "Crypto": 10, "Commodities": 35, "RealEstate": 25}}
}

# ==========================================
# 2. KURUMSAL HABER & OPEX MOTORU
# ==========================================
def get_third_friday(year, month):
    c = calendar.Calendar(firstweekday=calendar.MONDAY)
    month_cal = c.monthdatescalendar(year, month)
    fridays = [day for week in month_cal for day in week if day.weekday() == calendar.FRIDAY and day.month == month]
    return fridays[2]

def generate_institutional_news(trigger):
    today = datetime.now().date()
    year, month = today.year, today.month
    third_friday = get_third_friday(year, month)
    if (today - third_friday).days > 3:
        month = month + 1 if month < 12 else 1
        year = year + 1 if month == 1 else year
        third_friday = get_third_friday(year, month)
        
    days_to_opex = (third_friday - today).days
    alerts = []
    
    if 0 <= days_to_opex <= 10:
        alerts.append(f"🚨 **OPEX DYNAMICS (Vadeye {days_to_opex} Gün):** Options expiration yaklaşıyor. Market Maker'lar long gamma pozisyonunda kilitli. Yapay bir sakinlik ve ağır **Strike Pinning** mekanizması devrede. Kanal kırılımları algoritmik tuzaklara (Whipsaw) aşırı duyarlıdır.")
    elif -3 <= days_to_opex < 0:
        alerts.append("💥 **GAMMA UNWIND & REBALANCE:** OpEx tamamlandı. Dealer hedge yükümlülükleri eriyor. Sert **Dealer Gamma Unwinds** ve kurumsal **Systematic Flow Rebalances** dalgasına hazırlıklı olun. Temel rasyoların bugün hiçbir önemi yoktur.")
    else:
        alerts.append(f"📊 **CLEAN FLOW:** OpEx gravitesi zayıf. Fiyat hareketleri tamamen Dark Pool emir blokları ve tematik **Basket Hedging** akışları üzerinden şekilleniyor.")

    if trigger == "GEOPOLITICAL SHOCK": alerts.extend(["🌍 **SUPPLY SHOCK:** Jeopolitik tansiyon zirvede. Emtia ve nakit öne çıkıyor."])
    elif trigger == "GAMMA SQUEEZE": alerts.extend(["📈 **VOLATILITY ACCELERATION:** Kurumsal opsiyon talebi zirvede. Fiyat parabolik erime evresinde."])
    
    return alerts

def draw_battery(label, current, color, delta_1d=0.0):
    d1_icon = f"🔺+{delta_1d:.1f}" if delta_1d > 0 else f"🔻{delta_1d:.1f}" if delta_1d < 0 else "➖ 0.0"
    d1_color = "#00ff88" if delta_1d > 0 else "#ff3333" if delta_1d < 0 else "#888888"
    st.markdown(f"""
        <div style="margin-bottom: 2px; font-size: 0.85rem; color: #ccc; display: flex; justify-content: space-between;">
            <span>{label}</span>
            <span style="color: {d1_color}; font-weight: bold; font-size: 0.75rem;">1D Değişim: {d1_icon}</span>
        </div>
        <div class="battery-container" style="height: 20px;">
            <div class="battery-fill" style="width: {min(max(current,0), 100)}%; background-color: {color}; font-size: 0.8rem;">%{int(current)}</div>
        </div>
    """, unsafe_allow_html=True)

def draw_smart_money_flow(trigger_data):
    dot = graphviz.Digraph()
    dot.attr(bgcolor='#050505', rankdir='LR', ranksep='1.5', nodesep='0.8')
    dot.attr('node', fontsize='16', fontname='Arial', margin='0.2,0.1')
    dot.attr('edge', fontsize='14')
    with dot.subgraph(name='cluster_0') as c:
        c.attr(style='dashed', color='#555', label='Kaydi Varlıklar', fontcolor='#e0e0e0', fontsize='18')
        c.node("USD", "USD\n(Merkez)", shape='circle', style='filled', fillcolor='#0277bd', fontcolor='white')
        c.node("STOCK", "Borsalar", shape='box', style='filled', fillcolor='#f57f17', fontcolor='white')
        c.node("BOND", "Tahviller", shape='box', style='filled', fillcolor='#2e7d32', fontcolor='white')
    bat = trigger_data['battery']
    def get_pen(val): return str(max(2.0, val / 10))
    def get_col(val): return "#00ff88" if val >= 60 else "#ff3333" if val <= 40 else "#888"
    dot.edge("USD", "STOCK", color=get_col(bat['Stocks']), penwidth=get_pen(bat['Stocks']))
    dot.edge("USD", "BOND", color=get_col(bat['Bonds']), penwidth=get_pen(bat['Bonds']))
    st.graphviz_chart(dot, use_container_width=True)

# ==========================================
# 3. VERİ ÇEKİMİ VE YFINANCE MULTI-INDEX FİLTRESİ
# ==========================================
def get_safe_df(raw_data, ticker):
    if isinstance(raw_data.columns, pd.MultiIndex):
        if ticker in raw_data.columns.levels[0]:
            return raw_data[ticker].copy()
        elif ticker in raw_data.columns.levels[1]:
            return raw_data.xs(ticker, level=1, axis=1).copy()
        else:
            return pd.DataFrame()
    else:
        return raw_data.copy()

def get_rma(s, period): 
    return s.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

def get_rsi(s, period):
    delta = s.diff()
    ma_up = get_rma(delta.clip(lower=0), period)
    ma_down = get_rma(-1 * delta.clip(upper=0), period)
    rs = ma_up / ma_down.replace(0, 0.001)
    return 100 - (100 / (1 + rs))

def get_wma(s, period):
    weights = np.arange(1, period + 1)
    return s.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

@st.cache_data
def fetch_matrix_data(bypass_stamp):
    all_etfs = list(set([etf for etfs in GLOBAL_MAP.values() for etf in etfs]))
    all_etfs.extend(list(MAIN_SECTORS.keys()))
    end_date = datetime.now()
    
    try:
        raw_data = yf.download(all_etfs, start=end_date - timedelta(days=90), end=end_date, interval="1d", group_by='ticker', progress=False)
    except:
        return pd.DataFrame()

    matrix_results = []
    for t in all_etfs:
        df = get_safe_df(raw_data, t)
        df.dropna(subset=['Close'], inplace=True)
        if len(df) < 25: continue
        
        close = df['Close']
        r14_current = get_rsi(close, 14).iloc[-1]
        r14_1d_ago = get_rsi(close, 14).iloc[-2] if len(close) > 1 else r14_current
        r14_1w_ago = get_rsi(close, 14).iloc[-6] if len(close) > 5 else r14_current
        
        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        current_bbw = (((sma20 + 2*std20) - (sma20 - 2*std20)) / sma20 * 100).iloc[-1]
        cat = next((k for k, v in GLOBAL_MAP.items() if t in v), "Diğer")
        
        if r14_current > 70: state, color = "Aşırı Alım (Dağıtım)", "#ff3333"
        elif r14_current < 35: state, color = "Vakum (Contrarian Fırsat)", "#00ff88"
        else: state, color = "Sıkışma (VCP)", "#f1c40f"
        
        delta_icon = "⬆️" if r14_current > r14_1d_ago else "⬇️" if r14_current < r14_1d_ago else "➖"
        
        matrix_results.append({
            "Sektör": cat, "ETF": t, "RSI": r14_current, "RSI_1D": r14_1d_ago, "RSI_1W": r14_1w_ago, 
            "BBW": current_bbw, "Durum": state, "Renk": color, "Delta_Icon": delta_icon
        })
    return pd.DataFrame(matrix_results)

def apply_v700_logic(df):
    close, high, low, open_p, vol = df['Close'], df['High'], df['Low'], df['Open'], df['Volume']
    
    r14 = get_rsi(close, 14)
    v150_v_avg = vol.rolling(20).mean()
    
    # 1-Period confirmed EMA Trap (Unwritten Traps)
    ema1_s3 = close.ewm(span=5, adjust=False).mean()
    bear_trap = (low < ema1_s3) & (close > ema1_s3) & (vol > v150_v_avg * 1.8)
    bull_trap = (high > ema1_s3) & (close < ema1_s3) & (vol > v150_v_avg * 1.8)
    
    # Efor Status
    i_vwm_len = 14
    wma_cv = get_wma(close * vol, i_vwm_len)
    wma_v = get_wma(vol, i_vwm_len).clip(lower=0.001)
    raw_effort = wma_cv / wma_v
    eff_price = get_wma(raw_effort, 3)

    eff_status = pd.Series("➖ NÖTR", index=close.index)
    eff_status.loc[close > eff_price] = "🟢 POZ"
    eff_status.loc[close < eff_price] = "🔴 NEG"

    # Whale Power V700
    c_range_q = (high - low).clip(lower=0.001)
    delta_q = ((close - low) - (high - close)) / c_range_q
    delta_vol_q = (delta_q * vol).rolling(20).mean() / vol.rolling(20).mean().clip(lower=0.001)
    rvol_q = (vol / vol.rolling(20).mean().clip(lower=1)).clip(upper=2.5)

    base_pwr_q = ((r14 - 50) + (delta_vol_q * 50)) * rvol_q * 1.5
    logic_pwr_q = np.log(1 + np.exp(np.clip(base_pwr_q / 5, -50, 50))) * 5
    logic_pwr_q = np.where((low > high.shift(2)) & (close > open_p), logic_pwr_q + 35, logic_pwr_q)

    log_w_q = np.log10(1 + np.clip(logic_pwr_q, 0, None))
    pct_w_q = np.clip((log_w_q * 65)**0.8 * 1.8, 0, 100)
    w_pwr_q = get_wma(pd.Series(pct_w_q, index=close.index), 2).fillna(0)
    
    pct_pro_q = w_pwr_q.ewm(span=3, adjust=False).mean()
    yellow_rest = (w_pwr_q.shift(1) < pct_pro_q.shift(1)) & (w_pwr_q.shift(2) < pct_pro_q.shift(2))
    whale_re_entry = (w_pwr_q > pct_pro_q) & (w_pwr_q.shift(1) <= pct_pro_q.shift(1)) & yellow_rest

    # Diamond Aggregator
    diamond_blue = (w_pwr_q > 70) & (close > close.ewm(span=20).mean())
    diamond_red = (w_pwr_q < 30) & (close < close.ewm(span=20).mean())

    df['w_pwr_q'] = w_pwr_q
    df['bear_trap'] = bear_trap
    df['bull_trap'] = bull_trap
    df['whale_re_entry'] = whale_re_entry
    df['Diamond_Blue'] = diamond_blue
    df['Diamond_Red'] = diamond_red
    df['eff_status'] = eff_status
    df['r14'] = r14
    return df

@st.cache_data
def calculate_signals(ticker_list, interval="1d", bypass_stamp=""):
    if not ticker_list: return pd.DataFrame()
    end_date = datetime.now()
    
    # KRİTİK DÜZELTME: Haftalık analiz için 30 mum şartı var. 150 gün yetmez, 400 güne çıkardık.
    days_back = 150 if interval != "1wk" else 400
    
    try:
        raw_data = yf.download(ticker_list, start=end_date - timedelta(days=days_back), end=end_date, interval=interval, group_by='ticker', progress=False)
    except: 
        return pd.DataFrame()

    results = []
    for t in ticker_list:
        df = get_safe_df(raw_data, t)
        df.dropna(subset=['Close'], inplace=True)
        if len(df) < 30: continue

        if interval == "4h":
            df.index = pd.to_datetime(df.index)
            df = df.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()

        df = apply_v700_logic(df)
        close = df['Close']
        latest = df.iloc[-1]
        
        pct_1d = (close.iloc[-1] / close.iloc[-2] - 1) * 100 if len(close) > 1 else 0
        pct_1w = (close.iloc[-1] / close.iloc[-6] - 1) * 100 if len(close) > 5 else 0

        sig = "⚪ WAIT"
        if interval == "1wk":
            if latest['w_pwr_q'] > 80: sig = "🐋 WHALE ACCUMULATION"
            elif latest['r14'] < 35: sig = "🕳️ DEEP VALUE (DCA)"
        else:
            if latest['Diamond_Blue']: sig = "💎 MAVİ DIAMOND"
            elif latest['Diamond_Red']: sig = "🩸 KIRMIZI DIAMOND"
            elif latest['bull_trap']: sig = "⛔"
            elif latest['bear_trap']: sig = "✅"
            elif latest['whale_re_entry']: sig = "🔄 WHALE RE-ENTRY"
            elif latest['w_pwr_q'] >= 85: sig = "🐋 WHALE IN"

        results.append({
            "Ticker": t, "Sinyal": sig, "Efor": latest['eff_status'], "Fiyat": f"${close.iloc[-1]:.2f}",
            "Whale Power": float(f"{latest['w_pwr_q']:.1f}"), "Fusion": int(latest['w_pwr_q'] * 0.8),
            "1 Gün (%)": round(pct_1d, 2), "1 Hafta (%)": round(pct_1w, 2)
        })
            
    if results: return pd.DataFrame(results).sort_values(by="Fusion", ascending=False)
    return pd.DataFrame()

# KRİTİK DÜZELTME: API Limitlerine Karşı fast_info yedekleme mekanizması
@st.cache_data(ttl=1800)
def fetch_fundamental_data(ticker_list):
    funds = []
    for t in ticker_list:
        try:
            tk = yf.Ticker(t)
            info = tk.info
            
            # fast_info genelde banlanmaz, onu yedeğe aldık.
            mc = info.get('marketCap', 0)
            if mc is None or mc == 0:
                try: mc = tk.fast_info['marketCap']
                except: mc = 0
                
            pe = info.get('trailingPE', 0)
            if pe is None: pe = 0
                
            ps = info.get('priceToSalesTrailing12Months', 0)
            if ps is None: ps = 0

            funds.append({
                "Ticker": t, 
                "MarketCap": mc,
                "PE": pe,
                "PS": ps
            })
        except: 
            funds.append({"Ticker": t, "MarketCap": 0, "PE": 0, "PS": 0})
    return pd.DataFrame(funds)

# --- STYLER YARDIMCILARI ---
def style_signals(val):
    if isinstance(val, str):
        if 'MAVİ' in val: return 'background-color: #0000FF; color: white; font-weight: bold;'
        if 'KIRMIZI' in val: return 'background-color: #FF1744; color: white; font-weight: bold;'
        if 'WHALE RE-ENTRY' in val: return 'background-color: #006064; color: white; font-weight: bold;'
        if 'WHALE IN' in val: return 'background-color: #01579b; color: white;'
        if val == '⛔': return 'background-color: #b71c1c; color: white; font-size: 1.2rem; text-align: center;'
        if val == '✅': return 'background-color: #004d40; color: white; font-size: 1.2rem; text-align: center;'
    return 'background-color: #111111; color: white;'

def style_efor(val):
    if isinstance(val, str):
        if '🟢' in val: return 'color: #00FF88; font-weight: bold;'
        if '🔴' in val: return 'color: #FF1744; font-weight: bold;'
    return 'color: #888;'

def style_percentages(val):
    if isinstance(val, (float, int)): return f"color: {'#00ff88' if val > 0 else '#ff3333'}; font-weight: bold;"
    return ''

def render_heatmap(df, val_col, title):
    df_h = df.dropna(subset=[val_col]).sort_values(by=val_col, ascending=False)
    html = f"<div style='background:#111; padding:15px; border-radius:12px; border: 1px solid #333;'><h4 style='color:#00ff88; text-align:center; margin-bottom:15px; font-family: sans-serif;'>{title}</h4><div style='display: grid; grid-template-columns: repeat(auto-fill, minmax(75px, 1fr)); gap: 6px;'>"
    for _, row in df_h.iterrows():
        val = row[val_col]
        t = row['Ticker']
        if val > 0: bg, text_col = "#00b800" if val > 2 else "#006400", "#ffffff"
        elif val < 0: bg, text_col = "#b80000" if val < -2 else "#8b0000", "#ffffff"
        else: bg, text_col = "#ffffff", "#000000"
        html += f"<div style='background-color: {bg}; color: {text_col}; padding: 10px 2px; border-radius: 6px; text-align: center; display: flex; flex-direction: column; justify-content: center; height: 60px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);'>"
        html += f"<div style='font-size: 0.85rem; font-weight: 800; font-family: monospace;'>{t}</div>"
        html += f"<div style='font-size: 0.75rem; font-weight: bold;'>{val:.2f}%</div>"
        html += "</div>"
    html += "</div></div>"
    return html

# ==========================================
# 5. KOKPİT ARAYÜZÜ ATEŞLEME
# ==========================================
all_etfs_to_scan = list(MAIN_SECTORS.keys()) + list(ETF_INFO.keys())
raw_tickers = []
for k, v in ETF_INFO.items(): raw_tickers.extend(v['stocks'])
portfolio_tickers = sorted(list(set(raw_tickers)))

etf_name_map = {k: v for k, v in MAIN_SECTORS.items()}
for k, v in ETF_INFO.items(): etf_name_map[k] = f"Alt Sektör: {v['area']}"

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🌐 MAKRO & OPEX", 
    "🔋 OMNI-MATRIX (Piller)",
    "🦅 KUŞBAKIŞI (Sektör Sinyalleri)",
    "⚖️ VALUATION GAP (Çarpan Uçurumu)",
    "🦈 HAFTALIK MOMENTUM-GAP",
    "🚨 4H & OMNI RADAR",
    "⏱️ V700 DIAMOND BACKTEST",
    "🚀 FUTURE THEMES"
])

# ---------------------------------------------------------
# TAB 1: MAKRO & OPEX
# ---------------------------------------------------------
with tab1:
    st.subheader("⚙️ Institutional Desk: Gelişmiş Makro Tetikleyiciler")
    t_cols = st.columns(5)
    for i, trig in enumerate(SYSTEM_TRIGGERS.keys()):
        with t_cols[i]:
            if st.button(f"Senaryo: {trig}", use_container_width=True):
                st.session_state.active_trigger = trig

    alerts = generate_institutional_news(st.session_state.active_trigger)
    for alert in alerts:
        st.markdown(f"<div style='border-left: 3px solid {SYSTEM_TRIGGERS[st.session_state.active_trigger]['color']}; padding-left: 10px; margin-bottom: 10px; background-color:#1a1a1a; padding:10px; border-radius:5px;'>{alert}</div>", unsafe_allow_html=True)
    st.divider()
    draw_smart_money_flow(SYSTEM_TRIGGERS[st.session_state.active_trigger])

# ---------------------------------------------------------
# TAB 2: OMNI-MATRIX
# ---------------------------------------------------------
with tab2:
    st.subheader("🔋 Tüm Sektörler Pil Enerjisi & Contrarian Değişim Matrisi")
    with st.spinner("Tüm Matrix ve Dönemsel Pil Değişimleri Hesaplanıyor..."):
        df_m = fetch_matrix_data(st.session_state.battery_nonce)
        if not df_m.empty:
            theme_avg = df_m.groupby('Sektör')[['RSI', 'RSI_1D', 'RSI_1W']].mean().reset_index()
            cols = st.columns(4)
            for i, row in theme_avg.iterrows():
                with cols[i % 4]:
                    delta_1d_calc = row['RSI'] - row['RSI_1D']
                    col = "#00ff88" if row['RSI'] > 60 else "#ff3333" if row['RSI'] < 40 else "#f1c40f"
                    draw_battery(row['Sektör'], row['RSI'], col, delta_1d=delta_1d_calc)
            st.divider()
            
            fig = go.Figure()
            for state in ["Aşırı Alım (Dağıtım)", "Sıkışma (VCP)", "Vakum (Contrarian Fırsat)"]:
                df_s = df_m[df_m["Durum"] == state]
                fig.add_trace(go.Scatter(
                    x=df_s["BBW"], y=df_s["RSI"], mode='markers+text',
                    marker=dict(size=14, color=df_s["Renk"], line=dict(width=1, color='white'), opacity=0.9),
                    text=df_s["ETF"], textposition="top center", name=state
                ))
            fig.update_layout(title="Dinamik Kurumsal Enerji Matrisi", xaxis_title="Bollinger Bant Genişliği", yaxis_title="RSI (Hacimsel Enerji)", height=500, paper_bgcolor="#050505", plot_bgcolor="#111", font=dict(color="#e0e0e0"))
            st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# TAB 3: KUŞBAKIŞI PARA AKIŞI
# ---------------------------------------------------------
with tab3:
    st.subheader("🦅 Sektör & Alt Sektör Günlük Para Akışı")
    with st.spinner("Kuşbakışı Sektörler Taranıyor..."):
        df_bird = calculate_signals(all_etfs_to_scan, interval="1d", bypass_stamp=st.session_state.battery_nonce)
        if not df_bird.empty:
            df_bird['Kapsam'] = df_bird['Ticker'].map(etf_name_map)
            st.dataframe(df_bird[['Kapsam', 'Ticker', 'Sinyal', 'Efor', 'Fiyat', '1 Gün (%)', '1 Hafta (%)', 'Whale Power']].style.map(style_signals, subset=['Sinyal']).map(style_percentages, subset=['1 Gün (%)', '1 Hafta (%)']).map(style_efor, subset=['Efor']), use_container_width=True, height=400, hide_index=True)

# ---------------------------------------------------------
# TAB 4: VALUATION GAP
# ---------------------------------------------------------
with tab4:
    st.subheader("⚖️ Sektörel Çarpan Uçurumu (Valuation Gap) Radarı")
    val_groups = {
        "Yarı İletken & Fotonik": ETF_INFO["PHOTON"]["stocks"] + ["NVDA", "AMD"],
        "Siber Güvenlik": ETF_INFO["CYBER"]["stocks"],
        "Kuantum Bilişim": ETF_INFO["QUANT"]["stocks"],
        "Uzay Ekosistemi": ETF_INFO["SPACE_RACE"]["stocks"],
        "Kripto Madencilik": ETF_INFO["WGMI"]["stocks"]
    }
    
    group_choice = st.selectbox("Analiz Edilecek Tematik Grup", list(val_groups.keys()))
    if st.button("Valuation Gap Hesapla"):
        with st.spinner(f"{group_choice} değerlemeleri çekiliyor (Bu işlem API'ye bağlı biraz sürebilir)..."):
            tickers = list(set(val_groups[group_choice]))
            val_data = fetch_fundamental_data(tickers)
            
            if not val_data.empty:
                # KRİTİK DÜZELTME: API'den verisi gelemeyenleri de yakalayıp uyaralım
                valid_data = val_data[val_data['MarketCap'] > 0]
                
                if valid_data.empty:
                    st.error("⚠️ Yahoo Finance API geçici olarak Market Cap (Piyasa Değeri) verilerini reddetti. Lütfen birkaç dakika sonra tekrar deneyin.")
                else:
                    valid_data = valid_data.sort_values(by='MarketCap', ascending=False)
                    leader = valid_data.iloc[0]
                    st.markdown(f"<div class='valuation-leader'>🏆 Grup Lideri: {leader['Ticker']} (Market Cap: ${leader['MarketCap']/1e9:.1f}B, F/K: {leader['PE']:.1f})</div>", unsafe_allow_html=True)
                    st.write("---")
                    
                    for i in range(1, len(valid_data)):
                        row = valid_data.iloc[i]
                        gap_mc = leader['MarketCap'] / row['MarketCap'] if row['MarketCap'] > 0 else 0
                        pe_str = f"F/K: {row['PE']:.1f}" if row['PE'] > 0 else f"P/S: {row['PS']:.1f}"
                        st.markdown(f'''
                            <div class="valuation-gap-card">
                                <h3><span class="valuation-laggard">{row['Ticker']}</span> <span style="font-size:0.9rem; color:#888;">(Market Cap: ${row['MarketCap']/1e9:.1f}B | {pe_str})</span></h3>
                                <div class="valuation-quote">The valuation gap between ${leader['Ticker']} and ${row['Ticker']} is roughly <strong>{gap_mc:.1f}x</strong> apart in market scale.</div>
                            </div>
                        ''', unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 5 & 6: MOMENTUM VE RADAR
# ---------------------------------------------------------
with tab5:
    st.subheader("🦈 Haftalık Momentum-Gap Avcısı")
    with st.spinner("1W Kinetik Boşluklar aranıyor..."):
        df_wk = calculate_signals(all_etfs_to_scan, interval="1wk")
        if not df_wk.empty: st.dataframe(df_wk.style.map(style_signals, subset=['Sinyal']), use_container_width=True, hide_index=True)

with tab6:
    st.subheader("🚨 OMNI RADAR: Tüm Hisseler Günlük Tarama")
    with st.spinner("Tüm portföy taranıyor..."):
        df_radar = calculate_signals(portfolio_tickers, interval="1d")
        if not df_radar.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 🔄 Günlük Whale Re-Entry & ALIMLAR")
                st.dataframe(df_radar[df_radar['Sinyal'].isin(['🔄 WHALE RE-ENTRY', '✅', '💎 MAVİ DIAMOND'])].style.map(style_signals, subset=['Sinyal']), use_container_width=True, hide_index=True)
            with c2:
                st.markdown("#### ⛔ SATIŞLAR & DAĞITIM")
                st.dataframe(df_radar[df_radar['Sinyal'].isin(['⛔', '🩸 KIRMIZI DIAMOND'])].style.map(style_signals, subset=['Sinyal']), use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# TAB 7: V700 DIAMOND BACKTEST
# ---------------------------------------------------------
with tab7:
    st.subheader("⏱️ ŞAHANE V700: OMNI-DIAMOND CONFLUENCE BACKTEST")
    col_b1, col_b2 = st.columns(2)
    with col_b1: b_ticker = st.text_input("Backtest Hisse/ETF:", value="NVDA").upper()
    with col_b2: b_days = st.slider("Geçmiş Tarama (Gün)", 100, 1500, 365)
        
    if st.button("⚛️ V700 Fusion Reversal Analizi Yap", use_container_width=True):
        with st.spinner("Algoritmalar geçmişi simüle ediyor..."):
            raw_b = yf.download(b_ticker, start=datetime.today() - timedelta(days=b_days), end=datetime.today(), progress=False)
            
            # GÜVENLİ MULTI-INDEX ÇEKİMİ
            df_b = get_safe_df(raw_b, b_ticker)
            
            if not df_b.empty:
                df_b.dropna(subset=['Close'], inplace=True)
                df_b = apply_v700_logic(df_b)
                
                diamonds = df_b[df_b['Diamond_Blue'] | df_b['Diamond_Red'] | df_b['bear_trap'] | df_b['bull_trap']].copy()
                if not diamonds.empty:
                    diamonds['Renk'] = np.where(diamonds['Diamond_Blue'], "💎 MAVİ", 
                                       np.where(diamonds['Diamond_Red'], "🩸 KIRMIZI",
                                       np.where(diamonds['bear_trap'], "✅", "⛔")))
                    res = diamonds[['Close', 'Renk', 'w_pwr_q']].tail(15)
                    res.index = res.index.strftime('%Y-%m-%d')
                    
                    st.success(f"{b_ticker} için son {b_days} günde {len(diamonds)} adet Reversal tespit edildi!")
                    st.dataframe(res.style.map(style_signals, subset=['Renk']), use_container_width=True)
                else: st.info("Bu periyotta bir kesişim bulunamadı.")

# ---------------------------------------------------------
# TAB 8: FUTURE THEMES
# ---------------------------------------------------------
with tab8:
    st.subheader("🚀 FUTURE THEMES: Geleceğin Teknolojileri")
    future_tickers = list(set([t for tkrs in FUTURE_THEMES_MAP.values() for t in tkrs]))
    with st.spinner("Future Themes evreni taranıyor..."):
        df_future = calculate_signals(future_tickers, interval="1d")
        if not df_future.empty: st.dataframe(df_future.style.map(style_signals, subset=['Sinyal']), use_container_width=True, hide_index=True)
