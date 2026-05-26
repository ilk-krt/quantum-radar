import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime, timedelta
import time
import requests

# ==========================================
# 🎛️ 1. STREAMLIT ARAYÜZ VE SAYFA AYARLARI
# ==========================================
st.set_page_config(page_title="ŞAHANE V650 Otopilot & Backtest", page_icon="🧿", layout="wide")

st.markdown("""
    <style>
    .main {background-color: #0E1117;}
    h1, h2, h3 {color: #00E6FF;}
    .stDataFrame {border: 1px solid #333;}
    </style>
""", unsafe_allow_html=True)

st.title("🧿 ŞAHANE V650: Otopilot Tarama & Backtest Merkezi")
st.markdown("---")

# ==========================================
# 🧠 2. ÇEKİRDEK FONKSİYONLAR
# ==========================================
@st.cache_data(ttl=3600)
def fetch_data(ticker, start_date, end_date):
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    df.dropna(inplace=True)
    return df

@st.cache_data(ttl=86400)
def get_market_tickers(market_type):
    """Otomatik hisse listelerini çeker (Wikipedia Engelini Aşan Versiyon)"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    if market_type == "S&P 500":
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        html = requests.get(url, headers=headers).text
        tables = pd.read_html(html)
        for df in tables:
            if 'Symbol' in df.columns:
                return df['Symbol'].str.replace('.', '-', regex=False).tolist()
        return []
        
    elif market_type == "NASDAQ 100":
        url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
        html = requests.get(url, headers=headers).text
        tables = pd.read_html(html)
        for df in tables:
            if 'Ticker' in df.columns:
                return df['Ticker'].tolist()
        return []
        
    elif market_type == "Space & AI Explosive (Manuel)":
        return ["ASTS", "RKLB", "SPIR", "SIDU", "AMPG", "LUNR", "SMCI", "NVDA", "PLTR", "SOFI", "IREN"]
        
    return ["QQQ", "SPY"]

def apply_sahane_logic(df, qqq_df, vwm_len=14, ema_fast=5):
    # RVOL ve Squeeze
    df['Vol_Avg'] = ta.sma(df['Volume'], length=65)
    df['RVOL'] = df['Volume'] / df['Vol_Avg']
    
    bb = ta.bbands(df['Close'], length=20, std=2.0)
    kc = ta.kc(df['High'], df['Low'], df['Close'], length=20, scalar=1.5)
    
    # Sütun isimleri farklı gelse bile hata vermemesi için dinamik yakalama
    if bb is not None and kc is not None and not bb.empty and not kc.empty:
        bbl_col = [c for c in bb.columns if c.startswith('BBL')][0]
        bbu_col = [c for c in bb.columns if c.startswith('BBU')][0]
        kcl_col = [c for c in kc.columns if c.startswith('KCL')][0]
        kcu_col = [c for c in kc.columns if c.startswith('KCU')][0]
        df['In_Squeeze'] = (bb[bbl_col] > kc[kcl_col]) & (bb[bbu_col] < kc[kcu_col])
    else:
        df['In_Squeeze'] = False

    # Efor Çizgisi ve Kırılım
    df['C_V'] = df['Close'] * df['Volume']
    df['Effort_Line'] = ta.wma(ta.wma(df['C_V'], length=vwm_len) / ta.wma(df['Volume'], length=vwm_len), length=3)
    df['Effort_Cross_Up'] = (df['Close'] > df['Effort_Line']) & (df['Close'].shift(1) <= df['Effort_Line'].shift(1))
    
    # Hedefler için ATR
    df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    return df

def run_historical_backtest(df):
    """Geçmiş Efor Kırılımlarını bulur ve hedefleri simüle eder"""
    signals = df[df['Effort_Cross_Up']]
    results = []
    
    for entry_idx in signals.index:
        entry_price = df.loc[entry_idx, 'Close']
        atr = df.loc[entry_idx, 'ATR']
        if pd.isna(atr): continue
            
        target_1 = entry_price + (atr * 2) # T1: 2 ATR uzaklık
        target_2 = entry_price + (atr * 4) # T2: 4 ATR uzaklık
        stop_loss = entry_price - (atr * 1.5)
        
        # Sinyal sonrası veriler (Forward-Looking)
        future_df = df.loc[entry_idx:].iloc[1:30] # Önündeki 30 mumu kontrol et
        
        t1_hit = False
        t2_hit = False
        days_to_t1 = None
        days_to_t2 = None
        max_price_reached = entry_price # Görülen en yüksek fiyatı takip etmek için
        
        for i in range(len(future_df)):
            current_bar = future_df.iloc[i]
            
            # Görülen en yüksek seviyeyi güncelle
            if current_bar['High'] > max_price_reached:
                max_price_reached = current_bar['High']
            
            # Stop patladıysa aramayı bırak (Stop öncesi görülen max fiyatı almış olduk)
            if current_bar['Low'] <= stop_loss:
                break
                
            # Hedef 1 vuruldu mu?
            if not t1_hit and current_bar['High'] >= target_1:
                t1_hit = True
                days_to_t1 = i + 1
                
            # Hedef 2 vuruldu mu?
            if not t2_hit and current_bar['High'] >= target_2:
                t2_hit = True
                days_to_t2 = i + 1
                break # T2 vurulduysa tamamla
                
        results.append({
            "Tarih": entry_idx.date(),
            "Giriş Fiyatı": round(entry_price, 2),
            "Target 1": round(target_1, 2),
            "T1 Vuruldu mu?": "✅" if t1_hit else "❌",
            "T1 Süre (Gün)": days_to_t1 if t1_hit else "-",
            "Target 2": round(target_2, 2),
            "T2 Vuruldu mu?": "🚀" if t2_hit else "❌",
            "T2 Süre (Gün)": days_to_t2 if t2_hit else "-",
            "Max Görülen Fiyat": round(max_price_reached, 2)
        })
        
    return pd.DataFrame(results)

# ==========================================
# 🗂️ 3. SEKMELER (TABS) ARAYÜZÜ
# ==========================================
tab1, tab2, tab3 = st.tabs(["🚀 Otopilot Makro Tarayıcı", "⏱️ Geçmiş Sinyal Backtesti", "⚛️ Quantum Fusion (Derinlik)"])

# ----------------- SEKME 1: OTOPİLOT TARAYICI -----------------
with tab1:
    st.subheader("Otomatik Yığın Tarama (Scanz/Finviz Mantığı)")
    st.markdown("Piyasadaki hisseleri otomatik çeker ve Hacim Şoku (RVOL) / Sıkışma arar.")
    
    col1, col2 = st.columns(2)
    with col1:
        market_choice = st.selectbox("Taranacak Pazar / Endeks", ["Space & AI Explosive (Manuel)", "NASDAQ 100", "S&P 500"])
    with col2:
        rvol_filter = st.slider("Min RVOL (Hacim Şoku Kat Sayısı)", 1.5, 10.0, 3.0, step=0.5)
        
    if st.button("🚀 Otopilot Taramayı Başlat", use_container_width=True):
        tickers = get_market_tickers(market_choice)
        st.info(f"Otopilot devrede: {len(tickers)} hisse taranıyor. Lütfen bekleyin...")
        
        my_bar = st.progress(0)
        explosive_list = []
        
        end_date = datetime.today()
        start_date = end_date - timedelta(days=150)
        
        if len(tickers) > 100: tickers = tickers[:100] 
            
        for i, ticker in enumerate(tickers):
            my_bar.progress((i + 1) / len(tickers), text=f"Taranıyor: {ticker}")
            try:
                df = fetch_data(ticker, start_date, end_date)
                if df.empty or len(df) < 50: continue
                
                df['Vol_Avg'] = ta.sma(df['Volume'], length=65)
                df['RVOL'] = df['Volume'] / df['Vol_Avg']
                
                latest = df.iloc[-1]
                if latest['RVOL'] >= rvol_filter:
                    explosive_list.append({
                        "Hisse": ticker,
                        "Kapanış": round(latest['Close'], 2),
                        "RVOL": f"{round(latest['RVOL'], 2)}x Hacim Şoku 🔥"
                    })
            except: continue
                
        my_bar.empty()
        if explosive_list:
            st.success("Tarama Tamamlandı! İşte Patlamaya Hazır Anomaliler:")
            st.dataframe(pd.DataFrame(explosive_list), use_container_width=True)
        else:
            st.warning("Bu kriterlere uyan hacim şoku yaşanmadı.")

# ----------------- SEKME 2: BACKTEST MOTORU -----------------
with tab2:
    st.subheader("Forward-Looking Matrix (Efor Çizgisi Hedef Simülasyonu)")
    st.markdown("Geçmişteki 'Efor Kırılımı' sinyallerinin Tahmin 1 ve Tahmin 2'ye kaç günde ulaştığını analiz eder.")
    
    b_ticker = st.text_input("Backtest Yapılacak Hisse (Örn: ASTS):", value="ASTS").upper()
    b_days = st.slider("Kaç Günlük Geçmişi Tara?", 100, 1000, 365, step=50)
    
    if st.button("⏱️ Backtesti Başlat"):
        with st.spinner("Geçmiş sinyaller simüle ediliyor..."):
            df_b = fetch_data(b_ticker, datetime.today() - timedelta(days=b_days), datetime.today())
            if not df_b.empty:
                df_b = apply_sahane_logic(df_b, df_b)
                bt_results = run_historical_backtest(df_b)
                
                if not bt_results.empty:
                    st.success(f"{b_ticker} için {len(bt_results)} adet kırılım (Yeşil Üçgen) sinyali bulundu ve simüle edildi.")
                    st.dataframe(bt_results, use_container_width=True)
                else:
                    st.info("Bu tarih aralığında Efor Çizgisi Kırılımı gerçekleşmemiş.")

# ----------------- SEKME 3: QUANTUM FUSION -----------------
with tab3:
    st.subheader("Yüklü Giriş İçin Mikro Yapı (Balina & Tuzak)")
    q_ticker = st.text_input("Analiz Sembolü (Örn: RKLB):", value="RKLB").upper()
    
    if st.button("⚛️ Fusion Analizi Yap"):
        df_q = fetch_data(q_ticker, datetime.today() - timedelta(days=90), datetime.today())
        if not df_q.empty:
            df_q['vol_avg'] = df_q['Volume'].rolling(20).mean()
            df_q['is_whale_vol'] = df_q['Volume'] > (df_q['vol_avg'] + df_q['Volume'].rolling(20).std() * 1.5)
            df_q['whale_pwr'] = (df_q['Volume'] / df_q['vol_avg']) * ((df_q['Close'] - df_q['Low']) / (df_q['High'] - df_q['Low'] + 1e-6))
            df_q['slope'] = (df_q['Close'] - df_q['Close'].shift(3)) / 3
            df_q['is_bull_trap'] = (df_q['slope'] > 0) & (df_q['whale_pwr'] < df_q['whale_pwr'].shift(1))
            
            df_q['Sinyal'] = np.where(df_q['is_bull_trap'], "⛔ TRAP", np.where(df_q['whale_pwr'] > 0.7, "🐋 WHALE IN", "⚪ WAIT"))
            st.dataframe(df_q[['Close', 'whale_pwr', 'Sinyal']].tail(10).sort_index(ascending=False), use_container_width=True)