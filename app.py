import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime, timedelta
import time

# ==========================================
# 🎛️ 1. STREAMLIT ARAYÜZ VE SAYFA AYARLARI
# ==========================================
st.set_page_config(page_title="ŞAHANE V650 & Quantum", page_icon="🧿", layout="wide")

st.markdown("""
    <style>
    .main {background-color: #0E1117;}
    h1, h2, h3 {color: #00E6FF;}
    .stDataFrame {border: 1px solid #333;}
    </style>
""", unsafe_allow_html=True)

st.title("🧿 ŞAHANE V650: Quantum Omni-Fusion Terminali")
st.markdown("---")

# ==========================================
# 🧠 2. QUANTUM FUSION MANTIĞI (Tekil Hisse İçin)
# ==========================================
def apply_quantum_fusion(df):
    df['vol_avg'] = df['Volume'].rolling(window=20).mean()
    df['std_vol'] = df['Volume'].rolling(window=20).std()
    df['is_whale_vol'] = df['Volume'] > (df['vol_avg'] + (df['std_vol'] * 1.5))
    df['whale_pwr'] = (df['Volume'] / df['vol_avg']) * ((df['Close'] - df['Low']) / (df['High'] - df['Low'] + 1e-6))
    
    df['fusion_score'] = 0
    df['ema_1'] = df['Close'].ewm(span=1, adjust=False).mean()
    df.loc[df['Close'] > df['ema_1'], 'fusion_score'] += 1
    
    df['slope'] = (df['Close'] - df['Close'].shift(3)) / 3
    df.loc[df['slope'] > 0.1, 'fusion_score'] += 1
    df.loc[df['whale_pwr'] > 0.5, 'fusion_score'] += 2
    df.loc[df['is_whale_vol'], 'fusion_score'] += 1

    df['is_bull_trap'] = (df['slope'] > 0) & (df['whale_pwr'] < df['whale_pwr'].shift(1))
    return df

def get_signal_label(row):
    if row['fusion_score'] >= 4 and not row['is_bull_trap']: return "💎 ANY BUY"
    elif row['is_whale_vol'] and row['whale_pwr'] > 0.7: return "🐋 WHALE IN"
    elif row['is_bull_trap'] and row['slope'] > 0: return "⛔ TRAP"
    return "⚪ WAIT"

# ==========================================
# 🚀 3. ŞAHANE V650 TARAYICI MANTIĞI (Çoklu Tarama İçin)
# ==========================================
@st.cache_data(ttl=3600)
def fetch_data(ticker, start_date, end_date):
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    df.dropna(inplace=True)
    return df

def apply_sahane_logic(df, qqq_df, vwm_len=14, ema_fast=5):
    df['Vol_Avg'] = ta.sma(df['Volume'], length=65)
    df['RVOL'] = df['Volume'] / df['Vol_Avg']
    
    bb = ta.bbands(df['Close'], length=20, std=2.0)
    kc = ta.kc(df['High'], df['Low'], df['Close'], length=20, scalar=1.5)
    
    if bb is not None and kc is not None:
        df['BB_Low'] = bb[f'BBL_20_2.0']
        df['BB_Up'] = bb[f'BBU_20_2.0']
        df['KC_Low'] = kc[f'KCLe_20_1.5']
        df['KC_Up'] = kc[f'KCUe_20_1.5']
        df['In_Squeeze'] = (df['BB_Low'] > df['KC_Low']) & (df['BB_Up'] < df['KC_Up'])
    else:
        df['In_Squeeze'] = False

    aligned_qqq = qqq_df['Close'].reindex(df.index).ffill()
    df['RS_Rating'] = (df['Close'] / aligned_qqq).pct_change(periods=50) * 100
    
    df['C_V'] = df['Close'] * df['Volume']
    df['Effort_Line'] = ta.wma(ta.wma(df['C_V'], length=vwm_len) / ta.wma(df['Volume'], length=vwm_len), length=3)
    df['EMA_5'] = ta.ema(df['Close'], length=ema_fast)
    return df

def check_tactical_triggers(df):
    df['Effort_Cross_Up'] = (df['Close'] > df['Effort_Line']) & (df['Close'].shift(1) <= df['Effort_Line'].shift(1))
    df['EMA_1_Breakout'] = (df['Close'] > df['EMA_5']) & (df['Close'].shift(1) <= df['EMA_5'].shift(1))
    vol_avg_20 = ta.sma(df['Volume'], length=20)
    df['Bear_Trap_OK'] = (df['Low'] < df['EMA_5']) & (df['Close'] > df['EMA_5']) & (df['Volume'] > vol_avg_20 * 1.8)
    return df

# ==========================================
# 🗂️ 4. SEKMELER (TABS) ARAYÜZÜ
# ==========================================
tab1, tab2 = st.tabs(["⚛️ Quantum Fusion (Tekil Hisse)", "🚀 ŞAHANE V650 Makro Tarayıcı"])

with tab1:
    st.subheader("Balina ve Tuzak Detay Analizi")
    st.markdown("İstediğiniz tek bir hisseyi buraya girerek mikro yapıdaki tuzakları ve balina girişlerini analiz edin.")
    
    col_q1, col_q2 = st.columns([1, 3])
    with col_q1:
        q_ticker = st.text_input("Hisse Sembolü:", value="NVDA").upper()
        q_days = st.number_input("Gün Sayısı:", min_value=30, max_value=300, value=90)
        q_run = st.button("Analiz Et", type="primary")
        
    with col_q2:
        if q_run:
            with st.spinner(f"{q_ticker} verileri analiz ediliyor..."):
                start_date = datetime.today() - timedelta(days=q_days)
                df_q = fetch_data(q_ticker, start_date, datetime.today())
                
                if not df_q.empty:
                    df_q = apply_quantum_fusion(df_q)
                    df_q['Sinyal'] = df_q.apply(get_signal_label, axis=1)
                    
                    disp_df = df_q[['Close', 'Volume', 'whale_pwr', 'fusion_score', 'Sinyal']].tail(10)
                    st.dataframe(disp_df.sort_index(ascending=False), use_container_width=True)
                    
                    latest = df_q.iloc[-1]
                    st.success(f"**Son Durum ({q_ticker}):** {latest['Sinyal']} | Skor: {latest['fusion_score']} | Whale Power: {latest['whale_pwr']:.2f}")
                else:
                    st.error("Veri çekilemedi.")

with tab2:
    st.subheader("Patlayıcı ve Yüklü Giriş Fırsatlarını Tarama")
    
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        default_tickers = "ASTS, RKLB, SPIR, SIDU, AMPG, NVDA, TSLA, PLTR, SOFI, IREN"
        ticker_input = st.text_area("Taranacak Hisseler (Virgülle ayırın)", value=default_tickers)
    with col_t2:
        benchmark_sym = st.text_input("Göreceli Güç Endeksi", value="QQQ")
        rvol_threshold = st.slider("Min RVOL (Hacim Şoku)", 1.5, 10.0, 3.0, step=0.5)
    with col_t3:
        lookback_days = st.slider("Geriye Dönük Veri", 100, 500, 200, step=50)
        vwm_len = st.number_input("Efor Çizgisi Periyodu", 5, 50, 14)
        
    TICKERS = [t.strip().upper() for t in ticker_input.split(",")]
    
    if st.button("🚀 QUANTUM TARAMAYI BAŞLAT", use_container_width=True):
        end_date = datetime.today()
        start_date = end_date - timedelta(days=lookback_days)
        my_bar = st.progress(0, text="Endeks verisi senkronize ediliyor...")
        
        try:
            qqq_df = fetch_data(benchmark_sym, start_date, end_date)
        except Exception as e:
            st.error(f"Endeks alınamadı: {e}")
            st.stop()

        explosive_list = []
        tactical_list = []
        total_tickers = len(TICKERS)
        
        for i, ticker in enumerate(TICKERS):
            my_bar.progress((i + 1) / total_tickers, text=f"Taranıyor: {ticker}")
            try:
                df = fetch_data(ticker, start_date, end_date)
                if df.empty or len(df) < 70: continue
                    
                df = apply_sahane_logic(df, qqq_df, vwm_len=vwm_len)
                df = check_tactical_triggers(df)
                latest = df.iloc[-1]
                
                is_explosive = (latest['RVOL'] >= rvol_threshold) and (df['In_Squeeze'].tail(10).any()) and (latest['RS_Rating'] > 0)
                if is_explosive:
                    explosive_list.append({"Hisse": ticker, "Kapanış": round(latest['Close'], 2), "RVOL (Şok)": f"{round(latest['RVOL'], 2)}x", "Göreceli Güç": f"%{round(latest['RS_Rating'], 2)}", "Sıkışma": "Evet 🕳️"})
                
                signal_str = ""
                if latest['Bear_Trap_OK']: signal_str += "✅ Bear Trap "
                if latest['EMA_1_Breakout']: signal_str += "📈 1-EMA Kırılımı "
                if latest['Effort_Cross_Up']: signal_str += "🚀 Efor Kırılımı "
                
                if signal_str != "" or (latest['Close'] > latest['Effort_Line'] and latest['Bear_Trap_OK']):
                    tactical_list.append({"Hisse": ticker, "Kapanış": round(latest['Close'], 2), "Efor Çizgisi": round(latest['Effort_Line'], 2), "Durum": "Efor Üstünde 🟢" if latest['Close'] > latest['Effort_Line'] else "Efor Altında 🔴", "Tetikleyici": signal_str if signal_str else "Beklemede"})
                    
                time.sleep(0.1)
                
            except Exception as e:
                continue
                
        my_bar.empty()
        st.success("✅ Tarama başarıyla tamamlandı!")

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🔥 Makro Tema (Patlayıcı Adaylar)")
            if explosive_list: st.dataframe(pd.DataFrame(explosive_list), use_container_width=True, hide_index=True)
            else: st.info("Mevcut kriterleri karşılayan hacim şoku adayı bulunamadı.")
                
        with c2:
            st.subheader("🎯 Taktik Giriş (Retest & Tuzaklar)")
            if tactical_list: st.dataframe(pd.DataFrame(tactical_list), use_container_width=True, hide_index=True)
            else: st.info("Şu an efor hattında işlem fırsatı veren hisse bulunamadı.")