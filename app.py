import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import graphviz
import yfinance as yf
from datetime import datetime, timedelta
import calendar
import time
import requests

# ==========================================
# 0. AYARLAR & AGRESİF DARK MODE CSS
# ==========================================
st.set_page_config(layout="wide", page_title="AETHER APEX V700 DIAMOND", page_icon="🏛️")

st.markdown('''
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
    .valuation-quote { font-style: italic; color: #a0a0a0; font-size: 1rem; border-left: 3px solid #00ff88; padding-left: 15px; margin-top: 10px; }
    </style>
''', unsafe_allow_html=True)

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
    "Yarı İletken & Fotonik": ["SOXX", "SMH", "EUV", "PHOTON"],
    "Kuantum & Hafıza (Memory)": ["QUANT", "MEMORY_AI"],
    "Enerji & Altyapı": ["XLE", "XOP", "OIH", "XLU", "URA", "ICLN", "PAVE", "JOUL"],
    "Emtia & Madencilik": ["COPX", "LIT", "REMX", "GDX", "XME"],
    "Lojistik & Havacılık": ["IYT", "JETS", "HULL"],
    "Savunma & Uzay": ["XAR", "ARKX", "UFO", "SPACE_RACE"],
    "Finans & Kripto": ["XLF", "KRE", "ARKF", "IBIT", "WGMI"],
    "Gayrimenkul & Veri Merkezleri": ["XLRE", "REZ", "SRVR", "VNQ"],
    "Özel Durumlar (IPO/Earnings/Trump)": ["TRUMP_PF", "RECENT_IPO", "EARNINGS"]
}

ETF_INFO = {
    # Klasik Tematikler
    "XLU": {"area": "Utilities & Şebeke", "stocks": ["NEE", "SO", "DUK", "CEG", "AEP", "SRE", "D", "ETR", "VST", "XEL"]},
    "PAVE": {"area": "Altyapı Yenileme", "stocks": ["ETN", "PH", "HUBB", "POWL", "TT", "CARR", "JCI", "URI", "FAST", "GWW", "VMC", "MLM", "EXP", "J", "ACM", "PWR", "EME"]},
    "XLK": {"area": "Teknoloji Devleri", "stocks": ["NVDA", "AAPL", "MSFT", "MU", "AVGO", "AMD", "INTC", "CSCO", "PLTR", "AMAT"]},
    "IGV": {"area": "Yazılım ve SaaS", "stocks": ["MSFT", "CRM", "ORCL", "ADBE", "NOW", "INTU", "WDAY", "PLTR", "PAYC", "SNOW", "DDOG", "DT", "TEAM", "PANW", "CRWD", "NET"]},
    "SMH": {"area": "Global Çip Dökümhaneleri", "stocks": ["TSM", "INTC", "ASML", "NVDA", "AMD", "AVGO", "MRVL", "QCOM", "AMAT", "LRCX", "KLAC"]},
    "URA": {"area": "Uranyum ve Nükleer", "stocks": ["CCJ", "KAP", "NXE", "UEC", "UUUU", "DNN", "BWXT", "LEU", "SMR", "CEG"]},
    "WGMI": {"area": "Bitcoin Madenciliği", "stocks": ["MARA", "RIOT", "CLSK", "HUT", "CIFR", "IREN", "WULF", "CORZ", "HIVE", "BTDR", "NVDA", "AMD"]},
    
    # Yeni Geliştirilmiş Tematik Dosyalar (Derin Sektörler)
    "PHOTON": {"area": "Fotonik ve Optik Ekosistemi", "stocks": ["IQE", "AXTI", "AAOI", "AEHR", "LWLG", "WOLF", "OPTX", "VIAV", "HIMX", "LITE", "STM", "CIEN", "TSEM", "GFS", "UMC", "MRVL", "FORM", "MTSI", "POET", "ASX", "SMTC", "LASR", "VECO", "COHR", "PLTR", "TER", "LRCX", "ONTO", "AMAT", "AMKR", "SANM", "FN", "CRDO", "TECK"]},
    "QUANT": {"area": "Kuantum Bilişim & Algoritma", "stocks": ["ARQQ", "QBTS", "RGTI", "QUBT", "IONQ", "GFS", "IBM", "COHR", "HON", "TSEM", "MRVL", "GOOGL", "FORM", "RTX", "MSFT", "RDNT", "NVDA", "INTC", "BIDU", "BABA"]},
    "CYBER": {"area": "Global Siber Güvenlik", "stocks": ["ZS", "TENB", "OKTA", "FFIV", "CRWD", "S", "RPD", "BAH", "FTNT", "CHKP", "PANW", "NET", "VRNS", "LDOS", "CSCO", "SCWX"]},
    "SPACE_RACE": {"area": "SpaceX & Uzay İnovasyonu", "stocks": ["TSLA", "RKLB", "ASTS", "FLY", "SATS", "PL", "AMZN", "TMUS", "QCOM", "SATL", "SPIR", "IRDM", "GLW", "LUNR", "BKSY", "VSAT", "MDA", "RDW", "DCO", "ATRO", "VOYG", "ARKX", "HON", "LMT", "LHX", "BA", "NOC", "RTX", "HEI", "TDG", "SPCE", "YSS", "SIDU"]},
    "MEMORY_AI": {"area": "Yapay Zeka Hafıza & Veri Gölleri", "stocks": ["MU", "ALAB", "MRVL", "DELL", "NTAP", "PSTG", "HPE", "IBM", "STX", "WDC"]},
    
    # Özel Akış / Tarama Listeleri
    "TRUMP_PF": {"area": "Trump Portföyü (İzleme Listesi)", "stocks": ["DELL", "TXN", "DVA", "JBL", "KLAC", "MARA", "ETN", "AVGO", "NVDA", "TT", "MSTR", "COST", "CDNS", "AAPL", "SNPS", "MSI", "PNC", "ORCL", "ICE", "NFLX", "COIN", "UBER", "HD", "MSFT", "CVNA", "NVR", "ADBE", "CRM", "NOW", "WDAY"]},
    "RECENT_IPO": {"area": "Son Dönem Halka Arzlar", "stocks": ["CDNL", "AMBQ", "Q", "SOLS", "CRCL", "FPS", "PTRN", "BLLN", "PAYP", "BLSH", "VOYG", "NAVN", "XE", "AVEX", "ETOR", "GLOO", "FIGR", "YSS", "SOLV", "ARXS", "ELMT", "OMDA"]},
    "EARNINGS": {"area": "Yaklaşan Bilançolar Haftası", "stocks": ["CEG", "CRCL", "RDNT", "MNDY", "ASTS", "HIMS", "PLUG", "RGTI", "SE", "CAMT", "QBTS", "SATL", "JD", "OKLO", "PAGS", "BABA", "NBIS", "TSEM", "SONY", "DT", "BIRK", "POET", "CSCO", "BOOT", "DOCS", "ONDS", "AMAT", "NU", "QUBT", "TTWO"]}
}

FUTURE_THEMES_MAP = {
    "Chokepoint (Darboğaz) Çarpanları": ["NVDA", "AVGO", "CEG", "ETN", "EQIX", "FCX", "PLD"],
    "Agentic AI & Yazılım": ["NOW", "ADEA", "DOCN", "SOUN", "ADBE", "DT", "S", "EXTR"],
    "Uzay Bilişimi & Keşif (Space Computing)": ETF_INFO["SPACE_RACE"]["stocks"],
    "Humanoid & Robotik Algı": ["MBLY", "AEVA", "OUST", "CGNX", "NOVT", "RR", "INDI", "ZBRA", "KLIC", "XPEV", "NEO", "VPG", "LASR"],
    "Kuantum Bilişim (Quantum)": ETF_INFO["QUANT"]["stocks"],
    "Fotonik & Optik Çipler": ETF_INFO["PHOTON"]["stocks"],
    "Hafıza Katmanları (Memory/HBM)": ETF_INFO["MEMORY_AI"]["stocks"],
    "Neocloud & Enerji Pivotu": ["IREN", "APLD", "CIFR", "WULF", "CORZ", "BTDR", "CLSK", "MARA", "RIOT"],
    "Çip Mimarisi & Soğutma": ["NVDA", "ARM", "ASML", "LRCX", "KLAC", "TSM", "INTC", "AMD", "CDNS", "SNPS", "MU", "VRT", "SMCI"],
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

    if trigger == "GEOPOLITICAL SHOCK":
        alerts.extend(["🌍 **SUPPLY SHOCK:** Jeopolitik tansiyon zirvede. Algoritmik fonlar $HULL (Deniz Lojistiği) ve $GASZ (Doğalgaz) sepetlerine ağır sermaye park ediyor.", "🛢️ **CONTRARIAN FLOW:** Büyüme tezi rafa kalktı. Nakit, emtia ve sert varlıklara sığınıyor."])
    elif trigger == "GAMMA SQUEEZE":
        alerts.extend(["📈 **VOLATILITY ACCELERATION:** AI Altyapı ve Çip mimarilerinde kurumsal opsiyon talebi zirvede. Kurumsal emir akışları $JOUL ve $EUV kanallarındaki likiditeyi süpürüyor.", "🤖 **RE-RATING MATRIX:** Akıllı para otonom sistemler ve $CBOT (Robotik) katmanında hacim büyütüyor."])
    elif trigger == "STAGFLATION / SUPPLY SUPER-CYCLE":
        alerts.extend(["🌾 **HARD COMMODITIES BOOM:** Arz tedarik darboğazları kalıcı enflasyonu besliyor. Sermaye $COPX (Bakır), $URA (Uranyum) ve $REMX (Nadir Elementler) şebekelerine akıyor.", "💸 **BOND CAPITULATION:** Tahvillerden kaçan para emtia bazlı hisselerin nakit akışını fiyatlıyor."])
    elif trigger == "FED HAWKISH PIVOT / LIQUIDITY CRUNCH":
        alerts.extend(["🏛️ **REVERSE REPO DRAIN:** Fed likidite musluklarını sıkıyor. Riskli varlıklardan muazzam bir çıkış var. $IBIT ve yüksek çarpanlı teknoloji hisselerinde margin call riskleri tetikleniyor.", "💵 **CASH IS KING:** Kısa vadeli tahviller ve nakit dışındaki tüm piller deşarj moduna geçti."])
    else:
        alerts.extend(["⚖️ **EQUITY NEUTRAL:** Piyasa makro kararları konsolide ediyor. Kantitatif fonlar pariteler arası istatistiksel arbitraj (Statistical Arbitrage) çalıştırıyor."])
        
    return alerts

def draw_battery(label, current, color, delta_1d=0.0, delta_1w=0.0):
    d1_icon = f"🔺+{delta_1d:.1f}" if delta_1d > 0 else f"🔻{delta_1d:.1f}" if delta_1d < 0 else "➖ 0.0"
    d1_color = "#00ff88" if delta_1d > 0 else "#ff3333" if delta_1d < 0 else "#888888"
    
    st.markdown(f'''
        <div style="margin-bottom: 2px; font-size: 0.85rem; color: #ccc; display: flex; justify-content: space-between;">
            <span>{label}</span>
            <span style="color: {d1_color}; font-weight: bold; font-size: 0.75rem;">1D Değişim: {d1_icon}</span>
        </div>
        <div class="battery-container" style="height: 20px;">
            <div class="battery-fill" style="width: {min(max(current,0), 100)}%; background-color: {color}; font-size: 0.8rem;">%{int(current)}</div>
        </div>
    ''', unsafe_allow_html=True)

def draw_etf_battery(label, current, prev_1d, prev_1w, color, delta_icon, info=""):
    chg_1d = current - prev_1d
    c1_sign = f"+{chg_1d:.1f}" if chg_1d >= 0 else f"{chg_1d:.1f}"
    c1_col = "#00ff88" if chg_1d >= 0 else "#ff3333"
    
    st.markdown(f'''
        <div style="margin-bottom: 2px; font-size: 0.85rem; color: #e0e0e0;">
            <strong>{label}</strong> {info}
            <span style="font-size:0.75rem; float:right; color:{c1_col}; font-weight:bold;">(Δ 1D: %{c1_sign}) {delta_icon}</span>
        </div>
        <div class="battery-container" style="height: 22px; margin-bottom: 12px; border-radius: 6px;">
            <div class="battery-fill" style="width: {min(max(current, 0), 100)}%; background-color: {color}; font-size: 0.8rem;">%{int(current)}</div>
        </div>
    ''', unsafe_allow_html=True)

def draw_smart_money_flow(trigger_data):
    dot = graphviz.Digraph()
    dot.attr(bgcolor='#050505', rankdir='LR', ranksep='1.5', nodesep='0.8')
    dot.attr('node', fontsize='16', fontname='Arial', margin='0.2,0.1')
    dot.attr('edge', fontsize='14')
    with dot.subgraph(name='cluster_0') as c:
        c.attr(style='dashed', color='#555', label='Kaydi Varlıklar', fontcolor='#e0e0e0', fontsize='18')
        c.node("FIAT", "Fiat\\nCurrency", shape='ellipse', style='filled', fillcolor='#4a148c', fontcolor='white')
        c.node("USD", "USD\\n(Merkez)", shape='circle', style='filled', fillcolor='#0277bd', fontcolor='white')
        c.node("STOCK", "Borsalar", shape='box', style='filled', fillcolor='#f57f17', fontcolor='white')
        c.node("BOND", "Tahviller", shape='box', style='filled', fillcolor='#2e7d32', fontcolor='white')
        c.node("CRYPTO", "Kripto", shape='box', style='filled', fillcolor='#d81b60', fontcolor='white')
    with dot.subgraph(name='cluster_1') as c:
        c.attr(style='dashed', color='#555', label='Maddi Varlıklar', fontcolor='#e0e0e0', fontsize='18')
        c.node("COMM", "Emtia &\\nEnerji", shape='circle', style='filled', fillcolor='#00695c', fontcolor='white')
        c.node("REAL", "Gayrimenkul", shape='box', style='filled', fillcolor='#827717', fontcolor='white')
    bat = trigger_data['battery']
    def get_pen(val): return str(max(2.0, val / 10))
    def get_col(val): return "#00ff88" if val >= 60 else "#ff3333" if val <= 40 else "#888"
    dot.edge("FIAT", "USD", color="#aaa", penwidth="3")
    dot.edge("USD", "STOCK", color=get_col(bat['Stocks']), penwidth=get_pen(bat['Stocks']))
    dot.edge("USD", "BOND", color=get_col(bat['Bonds']), penwidth=get_pen(bat['Bonds']))
    dot.edge("USD", "CRYPTO", color=get_col(bat['Crypto']), penwidth=get_pen(bat['Crypto']))
    dot.edge("USD", "COMM", color=get_col(bat['Commodities']), penwidth=get_pen(bat['Commodities']))
    dot.edge("COMM", "REAL", color=get_col(bat['RealEstate']), penwidth=get_pen(bat['RealEstate']), style="dashed")
    st.graphviz_chart(dot, use_container_width=True)

# ==========================================
# 3. YFINANCE PANDAS MATEMATİK & OMNI FUSION
# ==========================================
def ta_sma(series, length):
    return series.rolling(window=length, min_periods=1).mean()

def ta_ema(series, length):
    return series.ewm(span=length, adjust=False, min_periods=1).mean()

def ta_wma(series, length):
    weights = np.arange(1, length + 1)
    return series.rolling(window=length, min_periods=length).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

def ta_rsi(series, length=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(alpha=1/length, min_periods=length, adjust=False).mean()
    ma_down = down.ewm(alpha=1/length, min_periods=length, adjust=False).mean()
    rs = ma_up / ma_down.replace(0, 0.001)
    return 100 - (100 / (1 + rs))

def ta_mfi(high, low, close, volume, length=14):
    typ = (high + low + close) / 3
    mf = typ * volume
    pos_mf = np.where(typ > typ.shift(1), mf, 0)
    neg_mf = np.where(typ < typ.shift(1), mf, 0)
    pos_mf_sum = pd.Series(pos_mf).rolling(window=length).sum()
    neg_mf_sum = pd.Series(neg_mf).rolling(window=length).sum().replace(0, 0.001)
    return 100 - (100 / (1 + (pos_mf_sum / neg_mf_sum)))

def ta_cci(high, low, close, length=20):
    typ = (high + low + close) / 3
    sma = typ.rolling(window=length).mean()
    mad = typ.rolling(window=length).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    return (typ - sma) / (0.015 * mad)

@st.cache_data
def fetch_matrix_data(bypass_stamp):
    all_etfs = list(set([etf for etfs in GLOBAL_MAP.values() for etf in etfs]))
    all_etfs.extend(list(MAIN_SECTORS.keys()))
    end_date = datetime.now()
    raw_data = yf.download(all_etfs, start=end_date - timedelta(days=90), end=end_date, interval="1d", group_by='ticker', progress=False)
    matrix_results = []
    for t in all_etfs:
        try:
            df = raw_data[t].dropna() if len(all_etfs) > 1 else raw_data.dropna()
            if len(df) < 25: continue
            close = df['Close']
            
            rsi_series = ta_rsi(close, 14)
            r14_current = rsi_series.iloc[-1]
            r14_1d_ago = rsi_series.iloc[-2] if len(rsi_series) > 1 else r14_current
            r14_1w_ago = rsi_series.iloc[-6] if len(rsi_series) > 5 else r14_current
            
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
        except: continue
    return pd.DataFrame(matrix_results)

def apply_sahane_logic_v700(df):
    if len(df) < 30: return df
    
    close, high, low, open_p, vol = df['Close'], df['High'], df['Low'], df['Open'], df['Volume']
    hlc3 = (high + low + close) / 3

    # ==========================
    # APEX V700 PINE SCRIPT PORT
    # ==========================
    # --- 1. Momentum Consensus ---
    rsi_fast = ta_rsi(close, 7)
    rsi_mid = ta_rsi(close, 14)
    mfi_val = pd.Series(ta_mfi(high, low, close, vol, 14), index=df.index)
    
    cci_val = ta_cci(high, low, close, 20)
    cci_norm = np.clip((cci_val + 200) / 4, 0, 100)
    
    pc = close.diff()
    double_smoothed_pc = ta_ema(ta_ema(pc, 25), 13)
    double_smoothed_abs_pc = ta_ema(ta_ema(pc.abs(), 25), 13)
    tsi_val = 100 * (double_smoothed_pc / np.maximum(double_smoothed_abs_pc, 0.001))
    tsi_norm = np.clip(tsi_val + 50, 0, 100)
    
    raw_omni = (rsi_fast + rsi_mid + mfi_val + cci_norm + tsi_norm) / 5
    mom_consensus = ta_wma(raw_omni, 3)

    # --- 2. Whale Power (w_pwr) ---
    c_range = np.maximum(high - low, 0.001)
    upper_wick = high - np.maximum(open_p, close)
    lower_wick = np.minimum(open_p, close) - low
    wick_delta = np.where(c_range > 0, (lower_wick - upper_wick) / c_range, 0)
    
    delta = ((close - low) - (high - close)) / c_range
    vol_sma_len = 20
    delta_vol = ta_sma(delta * vol, vol_sma_len) / np.maximum(ta_sma(vol, vol_sma_len), 0.001)
    v_avg = ta_sma(vol, vol_sma_len)
    
    rvol_raw = vol / np.maximum(v_avg, 1)
    rvol = np.where(rvol_raw > 2.5, 2.5 + np.log(np.maximum(rvol_raw - 1.5, 0.001)), rvol_raw)
    
    fvg_bull = (low > high.shift(2)) & (close > open_p)
    logic_pwr_base = ((ta_rsi(close, 14) - 50) + (delta_vol * 40) + (wick_delta * 20)) * rvol * 1.5 / 5
    logic_pwr = np.log(1 + np.exp(np.clip(logic_pwr_base, -50, 50))) * 5
    logic_pwr = np.where(fvg_bull, logic_pwr + 35, logic_pwr)
    
    w_pwr_raw = np.power(np.log10(np.maximum(1 + logic_pwr, 1.001)) * 65, 0.8) * 1.8
    w_pwr = ta_wma(pd.Series(np.minimum(w_pwr_raw, 100), index=df.index), 2)
    pct_pro = ta_ema(w_pwr, 3)

    # Whale States
    wh_yellow_last_3 = (pct_pro.shift(1) > w_pwr.shift(1)) & (pct_pro.shift(2) > w_pwr.shift(2)) & (pct_pro.shift(3) > w_pwr.shift(3))
    wh_red_covers = w_pwr >= pct_pro
    wh_w_pwr_inc = w_pwr > w_pwr.shift(1)
    wh_w_pwr_dec = w_pwr < w_pwr.shift(1)

    wh_db = (wh_yellow_last_3 & wh_red_covers & wh_w_pwr_inc) | ((w_pwr.shift(1) < 1) & (w_pwr >= 20))
    wh_red = (w_pwr.shift(1) >= pct_pro.shift(1)) & wh_w_pwr_dec & (pct_pro > w_pwr)
    
    # --- 3. Omni RS Dynamic Effort ---
    raw_effort = ta_wma(close * vol, 14) / ta_wma(vol, 14).replace(0, 0.001)
    smoothed_effort = ta_wma(raw_effort, 3)

    rs_f_macd = ta_ema(close, 12) - ta_ema(close, 26)
    rs_f_speed = ((rs_f_macd - rs_f_macd.rolling(100).min()) / np.maximum(rs_f_macd.rolling(100).max() - rs_f_macd.rolling(100).min(), 0.001) * 100) - 50
    rs_f_sig = ta_ema(rs_f_speed, 9)

    rs_s_macd = ta_ema(hlc3, 12) - ta_ema(hlc3, 26)
    rs_s_speed = ((rs_s_macd - rs_s_macd.rolling(100).min()) / np.maximum(rs_s_macd.rolling(100).max() - rs_s_macd.rolling(100).min(), 0.001) * 100) - 50
    
    rs_cross = (rs_f_speed > rs_f_sig) & (rs_f_speed.shift(1) <= rs_f_sig.shift(1)) | (rs_f_speed < rs_f_sig) & (rs_f_speed.shift(1) >= rs_f_sig.shift(1))
    
    rs_color_code = pd.Series(0, index=df.index)
    rs_color_code = np.where(rs_cross, 0,
        np.where((rs_f_speed > rs_f_sig) & ((mom_consensus >= 50) & (rs_s_speed > rs_s_speed.shift(1)) | (rs_s_speed <= rs_s_speed.shift(1))), 1,
        np.where((rs_f_speed < rs_f_sig) & ((mom_consensus < 50) & (rs_s_speed < rs_s_speed.shift(1)) | (rs_s_speed >= rs_s_speed.shift(1))), -1, rs_color_code)))

    rs_db = (pd.Series(rs_color_code).shift(1) == 0) & (close.shift(1) > smoothed_effort.shift(1)) & (rs_color_code == 1) & (close > smoothed_effort)
    rs_red = (close < smoothed_effort) & (rs_color_code == -1) & (pd.Series(rs_color_code).shift(1) != -1)

    # --- 4. APEX Engine Points ---
    apx_f_hist_val = (rs_f_speed - rs_f_sig) * 1.5
    apx_omni_center = mom_consensus - 50

    fus_db = (apx_f_hist_val > 0) & (apx_f_hist_val.shift(1) <= 0)
    fus_red = (apx_f_hist_val < 0) & (apx_f_hist_val.shift(1) >= 0)
    
    syn_db = (rs_s_speed > 0) & (rs_s_speed.shift(1) <= 0)
    syn_red = (rs_s_speed < 0) & (rs_s_speed.shift(1) >= 0)

    omni_db = (apx_omni_center > 0) & (apx_omni_center.shift(1) <= 0)
    omni_red = (apx_omni_center < 0) & (apx_omni_center.shift(1) >= 0)

    spd_db = (rs_f_speed > rs_f_sig) & (rs_f_speed.shift(1) <= rs_f_sig.shift(1))
    spd_red = (rs_f_speed < rs_f_sig) & (rs_f_speed.shift(1) >= rs_f_sig.shift(1))

    any_apx_db = fus_db.astype(int) + syn_db.astype(int) + omni_db.astype(int) + spd_db.astype(int)
    any_apx_red = fus_red.astype(int) + syn_red.astype(int) + omni_red.astype(int) + spd_red.astype(int)

    # 1-Period confirmed EMA trap conditions (Replaced text with pure emojis)
    ema1_s3 = ta_ema(close, 5)
    bear_trap = (low < ema1_s3) & (close > ema1_s3) & (vol > v_avg * 1.8)
    bull_trap = (high > ema1_s3) & (close < ema1_s3) & (vol > v_avg * 1.8)

    # Compile Final Signals
    df['w_pwr'] = w_pwr
    df['w_pwr_pct'] = pct_pro
    df['mom_consensus'] = mom_consensus
    df['wh_db'] = wh_db
    df['rs_db'] = rs_db
    df['any_apx_db'] = any_apx_db
    df['wh_red'] = wh_red
    df['rs_red'] = rs_red
    df['any_apx_red'] = any_apx_red
    df['bear_trap'] = bear_trap
    df['bull_trap'] = bull_trap
    
    # Diamond Fusion Aggregator
    df['Diamond_Blue'] = wh_db | rs_db | (any_apx_db >= 2)
    df['Diamond_Red'] = wh_red | rs_red | (any_apx_red >= 2)

    return df

@st.cache_data
def calculate_signals(ticker_list, interval="1d", bypass_stamp=""):
    if not ticker_list: return pd.DataFrame()
    end_date = datetime.now()
    
    try:
        if interval == "1d":
            raw_data = yf.download(ticker_list, start=end_date - timedelta(days=120), end=end_date, interval="1d", group_by='ticker', progress=False)
        elif interval == "4h":
            raw_data = yf.download(ticker_list, start=end_date - timedelta(days=60), end=end_date, interval="1h", group_by='ticker', progress=False)
        elif interval == "1wk":
            raw_data = yf.download(ticker_list, start=end_date - timedelta(days=365), end=end_date, interval="1wk", group_by='ticker', progress=False)
    except: return pd.DataFrame()

    results = []
    for t in ticker_list:
        try:
            df = raw_data[t].copy().dropna() if len(ticker_list) > 1 else raw_data.copy().dropna()
            if len(df) < 50: continue

            if interval == "4h":
                df.index = pd.to_datetime(df.index)
                df = df.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()

            df = apply_sahane_logic_v700(df)
            
            close = df['Close']
            pct_1d = (close.iloc[-1] / close.iloc[-2] - 1) * 100 if len(close) > 1 else 0
            pct_1w = (close.iloc[-1] / close.iloc[-6] - 1) * 100 if len(close) > 5 else 0

            latest = df.iloc[-1]
            
            sig = "⚪ WAIT"
            if interval == "1wk":
                sma20 = ta_sma(close, 20)
                prior_momentum = (df['Low'].shift(1) >= df['Low'].shift(2)) & (df['High'].shift(1) >= df['High'].shift(2)) & (df['Close'].shift(1) > sma20.shift(1))
                bull_gap = (df['Open'] > df['High'].shift(1)) & (df['Close'] > df['Open'])
                
                if prior_momentum.iloc[-1] and bull_gap.iloc[-1]: sig = "🚀 MOMENTUM GAP (UP)"
                elif latest['w_pwr'] > 80: sig = "🐋 WHALE ACCUMULATION"
                elif ta_rsi(close, 14).iloc[-1] < 35: sig = "🕳️ DEEP VALUE (DCA)"
            else:
                if latest['Diamond_Blue']: sig = "💎 MAVİ DIAMOND"
                elif latest['Diamond_Red']: sig = "🩸 KIRMIZI DIAMOND"
                elif latest['w_pwr'] >= 85: sig = "🐋 WHALE IN"
                elif latest['bull_trap']: sig = "⛔"
                elif latest['bear_trap']: sig = "✅"
                elif latest['w_pwr'] > latest['w_pwr_pct'] and df['w_pwr'].shift(1).iloc[-1] < df['w_pwr_pct'].shift(1).iloc[-1]: sig = "🔄 WHALE RE-ENTRY"

            # Synthetic Efor
            eff_status = "🟢 POZ" if latest['Close'] > ta_sma(close, 14).iloc[-1] else "🔴 NEG"

            results.append({
                "Ticker": t, "Sinyal": sig, "Efor": eff_status, "Fiyat": f"${latest['Close']:.2f}",
                "Whale Power": float(f"{latest['w_pwr']:.1f}"), "Fusion": int(latest['mom_consensus']),
                "1 Gün (%)": round(pct_1d, 2), "1 Hafta (%)": round(pct_1w, 2)
            })
        except Exception as e:
            continue
            
    if results: return pd.DataFrame(results).sort_values(by="Fusion", ascending=False)
    return pd.DataFrame()

@st.cache_data
def fetch_fundamental_data(ticker_list):
    funds = []
    today = datetime.now().date()
    for t in ticker_list:
        try:
            tk = yf.Ticker(t)
            info = tk.info
            target = info.get('targetMeanPrice', None)
            fv = f"${target:.2f}" if target else "N/A"
            cal = tk.calendar
            earn_date = "N/A"
            days_to_earn = 999
            if cal and 'Earnings Date' in cal and len(cal['Earnings Date']) > 0:
                e_date = cal['Earnings Date'][0].date()
                earn_date = e_date.strftime('%Y-%m-%d')
                days_to_earn = (e_date - today).days
                
            funds.append({
                "Ticker": t, 
                "Fair Value": fv, 
                "Bilanço": earn_date, 
                "DaysToEarn": days_to_earn,
                "MarketCap": info.get('marketCap', 0),
                "PE": info.get('trailingPE', 0),
                "PS": info.get('priceToSalesTrailing12Months', 0)
            })
        except: 
            funds.append({"Ticker": t, "Fair Value": "N/A", "Bilanço": "N/A", "DaysToEarn": 999, "MarketCap": 0, "PE": 0, "PS": 0})
    return pd.DataFrame(funds)

# --- STYLER YARDIMCILARI ---
def style_signals(val):
    if isinstance(val, str):
        if 'GAP' in val: return 'background-color: #00e676; color: black; font-weight: bold;'
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

for k, v in ETF_INFO.items():
    raw_tickers.extend(v['stocks'])
portfolio_tickers = sorted(list(set(raw_tickers)))

etf_name_map = {k: v for k, v in MAIN_SECTORS.items()}
for k, v in ETF_INFO.items(): etf_name_map[k] = f"Alt Sektör: {v['area']}"

with st.spinner("Piyasa Radar Kontrolü (Bilanço & Değer)..."):
    df_alerts = fetch_fundamental_data(portfolio_tickers)
    urgent_earn = df_alerts[(df_alerts['DaysToEarn'] >= 0) & (df_alerts['DaysToEarn'] <= 7)]
    if not urgent_earn.empty:
        st.warning(f"🔔 **YAKLAŞAN BİLANÇO DİKKAT:** {', '.join(urgent_earn['Ticker'].tolist())} hisselerinin bilançosuna 7 günden az kaldı!")

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
# TAB 1: MAKRO & OPEX KOKPİT
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
        st.markdown(f"<div style='border-left: 3px solid {SYSTEM_TRIGGERS[st.session_state.active_trigger]['color']}; padding-left: 10px; margin-bottom: 10px; font-size:1rem; background-color:#1a1a1a; padding:10px; border-radius:5px;'>{alert}</div>", unsafe_allow_html=True)
    
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
            st.dataframe(
                df_bird[['Kapsam', 'Ticker', 'Sinyal', 'Efor', 'Fiyat', '1 Gün (%)', '1 Hafta (%)', 'Whale Power']].style.map(style_signals, subset=['Sinyal']).map(style_percentages, subset=['1 Gün (%)', '1 Hafta (%)']).map(style_efor, subset=['Efor']),
                use_container_width=True, height=400, hide_index=True
            )
            c_heat1, c_heat2 = st.columns(2)
            with c_heat1: st.markdown(render_heatmap(df_bird, '1 Gün (%)', "Günlük (1D) Isı Haritası"), unsafe_allow_html=True)
            with c_heat2: st.markdown(render_heatmap(df_bird, '1 Hafta (%)', "Haftalık (1W) Isı Haritası"), unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 4: VALUATION GAP (ÇARPAN UÇURUMU) YENİ
# ---------------------------------------------------------
with tab4:
    st.subheader("⚖️ Sektörel Çarpan Uçurumu (Valuation Gap) Radarı")
    st.markdown("Aynı işi yapan şirketleri gruplandırarak, sektör liderinin çarpanlarına göre aşırı iskontolu (veya pahalı) kalmış fırsatları tespit eder.")
    
    val_groups = {
        "Yarı İletken & Fotonik Optik Cihazlar": ETF_INFO["PHOTON"]["stocks"] + ["NVDA", "AMD", "ARM"],
        "Siber Güvenlik (Cybersecurity)": ETF_INFO["CYBER"]["stocks"],
        "Kuantum Bilişim (Quantum)": ETF_INFO["QUANT"]["stocks"],
        "Uzay Ekosistemi & SpaceX": ETF_INFO["SPACE_RACE"]["stocks"],
        "Hafıza Katmanları (Memory)": ETF_INFO["MEMORY_AI"]["stocks"],
        "Bulut & Kurumsal Yazılım": ETF_INFO["IGV"]["stocks"],
        "Nükleer & Enerji Altyapı": ETF_INFO["URA"]["stocks"] + ["CEG", "VST"],
        "Kripto Madencilik": ETF_INFO["WGMI"]["stocks"],
        "Trump Portföy İzleme Listesi": ETF_INFO["TRUMP_PF"]["stocks"]
    }
    
    group_choice = st.selectbox("Analiz Edilecek Tematik Grup", list(val_groups.keys()))
    
    if st.button("Valuation Gap Hesapla"):
        with st.spinner(f"{group_choice} değerlemeleri çekiliyor..."):
            tickers = list(set(val_groups[group_choice]))
            val_data = df_alerts[df_alerts['Ticker'].isin(tickers)]
            
            if not val_data.empty:
                val_data = val_data[val_data['MarketCap'] > 0]
                val_data = val_data.sort_values(by='MarketCap', ascending=False)
                
                if len(val_data) > 1:
                    leader = val_data.iloc[0]
                    st.markdown(f"<div class='valuation-leader'>🏆 Grup Lideri: {leader['Ticker']} (Market Cap: ${leader['MarketCap']/1e9:.1f}B, F/K: {leader['PE']:.1f})</div>", unsafe_allow_html=True)
                    
                    st.write("---")
                    
                    for i in range(1, len(val_data)):
                        row = val_data.iloc[i]
                        gap_mc = leader['MarketCap'] / row['MarketCap'] if row['MarketCap'] > 0 else 0
                        
                        pe_str = f"F/K: {row['PE']:.1f}" if row['PE'] > 0 else f"P/S: {row['PS']:.1f}"
                        leader_pe_str = f"F/K: {leader['PE']:.1f}" if leader['PE'] > 0 else f"P/S: {leader['PS']:.1f}"
                        
                        st.markdown(f'''
                            <div class="valuation-gap-card">
                                <h3><span class="valuation-laggard">{row['Ticker']}</span> <span style="font-size:0.9rem; color:#888;">(Market Cap: ${row['MarketCap']/1e9:.1f}B | {pe_str})</span></h3>
                                <div class="valuation-quote">
                                    "The valuation gap between ${leader['Ticker']} and ${row['Ticker']} is way too appealing. Roughly <strong>{gap_mc:.1f}x</strong> apart in market scale..."
                                </div>
                            </div>
                        ''', unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 5 & 6: MOMENTUM VE RADAR
# ---------------------------------------------------------
with tab5:
    st.subheader("🦈 Haftalık Momentum-Gap Avcısı")
    with st.spinner("1W Kinetik Boşluklar aranıyor..."):
        df_wk = calculate_signals(list(MAIN_SECTORS.keys()) + list(ETF_INFO.keys()), interval="1wk")
        if not df_wk.empty:
            st.dataframe(df_wk.style.map(style_signals, subset=['Sinyal']), use_container_width=True, hide_index=True)

with tab6:
    st.subheader("🚨 OMNI RADAR: Tüm Hisseler Günlük Tarama")
    with st.spinner("Piyasa taranıyor..."):
        df_radar = calculate_signals(portfolio_tickers, interval="1d")
        if not df_radar.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 🔄 Günlük Whale Re-Entry")
                st.dataframe(df_radar[df_radar['Sinyal'] == '🔄 WHALE RE-ENTRY'].style.map(style_signals, subset=['Sinyal']), use_container_width=True, hide_index=True)
            with c2:
                st.markdown("#### 💎 Mavi Diamond (V700)")
                st.dataframe(df_radar[df_radar['Sinyal'] == '💎 MAVİ DIAMOND'].style.map(style_signals, subset=['Sinyal']), use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# TAB 7: V700 DIAMOND BACKTEST (Quantum Fusion Update)
# ---------------------------------------------------------
with tab7:
    st.subheader("⏱️ ŞAHANE V700: OMNI-DIAMOND CONFLUENCE BACKTEST")
    st.markdown("Apex V700'ün elmas konfigürasyonlarını tarayarak geçmiş major trend dönüşlerindeki (Reversal) mükemmel noktaları tespit eder.")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        b_ticker = st.text_input("Backtest Hisse/ETF:", value="NVDA").upper()
    with col_b2:
        b_days = st.slider("Geçmiş Tarama (Gün)", 100, 1500, 365)
        
    if st.button("⚛️ V700 Fusion Reversal Analizi Yap", use_container_width=True):
        with st.spinner("Algoritmalar geçmişi simüle ediyor..."):
            df_b = yf.download(b_ticker, start=datetime.today() - timedelta(days=b_days), end=datetime.today(), progress=False)
            if not df_b.empty:
                df_b.columns = [c[0] for c in df_b.columns] if isinstance(df_b.columns, pd.MultiIndex) else df_b.columns
                df_b = apply_sahane_logic_v700(df_b)
                
                # Sadece Mavi ve Kırmızı Diamond'ların basıldığı günleri listele
                diamonds = df_b[df_b['Diamond_Blue'] | df_b['Diamond_Red']].copy()
                
                if not diamonds.empty:
                    diamonds['Renk'] = np.where(diamonds['Diamond_Blue'], "💎 MAVİ (Dip Onayı/Alım)", "🩸 KIRMIZI (Tepe Onayı/Satış)")
                    res = diamonds[['Close', 'Renk', 'w_pwr', 'mom_consensus']].tail(15)
                    res.index = res.index.strftime('%Y-%m-%d')
                    
                    st.success(f"{b_ticker} için son {b_days} günde {len(diamonds)} adet Reversal Diamond bulundu!")
                    st.dataframe(res.style.map(style_signals, subset=['Renk']), use_container_width=True)
                else:
                    st.info("Bu periyotta kesinleşmiş bir Diamond Confluence kesişimi bulunamadı.")

# ---------------------------------------------------------
# TAB 8: FUTURE THEMES
# ---------------------------------------------------------
with tab8:
    st.subheader("🚀 FUTURE THEMES: Geleceğin Teknolojileri")
    future_tickers = list(set([t for tkrs in FUTURE_THEMES_MAP.values() for t in tkrs]))
    with st.spinner("Future Themes evreni taranıyor..."):
        df_future = calculate_signals(future_tickers, interval="1d")
        if not df_future.empty:
            st.dataframe(df_future.style.map(style_signals, subset=['Sinyal']), use_container_width=True, hide_index=True)
