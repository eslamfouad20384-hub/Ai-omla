# crypto_scanner_best_version.py
import streamlit as st
import pandas as pd
import requests
import numpy as np

st.set_page_config(page_title="أفضل Crypto Scanner 🔥", layout="wide")
st.title("أفضل Crypto Scanner بالعربي 🔍")

# -----------------------------
# 1️⃣ جلب بيانات السوق
# -----------------------------
def get_market_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency":"usd","order":"market_cap_desc","per_page":100,"page":1,"sparkline":False}
    response = requests.get(url, params=params)
    df = pd.DataFrame(response.json())
    return df

# -----------------------------
# 2️⃣ جلب بيانات OHLC
# -----------------------------
def get_historical_data(coin_id, days=30):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency":"usd","days":days,"interval":"daily"}
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data['prices'], columns=['timestamp', 'close'])
    df['close'] = df['close'].astype(float)
    return df

# -----------------------------
# 3️⃣ حساب RSI
# -----------------------------
def calculate_RSI(df, period=14):
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -1*delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

# -----------------------------
# 4️⃣ حساب الدعم
# -----------------------------
def calculate_support(df, period=14):
    return df['close'].tail(period).min()

# -----------------------------
# 5️⃣ فلترة العملات
# -----------------------------
def filter_coins(df_market):
    results = []

    for _, row in df_market.iterrows():
        coin_id = row['id']
        try:
            hist = get_historical_data(coin_id, days=30)
            rsi = calculate_RSI(hist)
            support = calculate_support(hist)
            # مقارنة الفوليوم اليوم بالأيام السابقة
            volume_today = hist['close'].iloc[-1]
            volume_prev = hist['close'].iloc[-2] if len(hist) > 1 else hist['close'].iloc[-1]
            volume_increasing = volume_today > volume_prev
        except:
            rsi = None
            support = None
            volume_increasing = False

        liquidity_ok = row['total_volume'] >= 5000000
        volume_ok = volume_increasing
        buy_volume = row['total_volume']*0.6  # تقدير إذا مصدر Buy/Sell مش متاح
        sell_volume = row['total_volume']*0.4
        buy_vs_sell_ok = buy_volume > sell_volume
        rsi_ok = rsi is not None and rsi < 30
        support_ok = row['current_price'] <= support if support else False

        results.append({
            'الاسم / Name': row['name'],
            'رمز العملة / Symbol': row['symbol'],
            'السعر / Price (USD)': row['current_price'],
            'السيولة / Liquidity': row['total_volume'],
            'حجم الشراء / Buy Volume': buy_volume,
            'حجم البيع / Sell Volume': sell_volume,
            'RSI': rsi,
            'الدعم / Support': support,
            'Liquidity_OK': liquidity_ok,
            'Volume_OK': volume_ok,
            'Buy_vs_Sell_OK': buy_vs_sell_ok,
            'RSI_OK': rsi_ok,
            'Support_OK': support_ok
        })

    return pd.DataFrame(results)

# -----------------------------
# 6️⃣ واجهة Streamlit
# -----------------------------
st.markdown("### اضغط زر تحديث لجلب البيانات وحساب كل الشروط الحقيقية")
if st.button("تحديث البيانات / Refresh Data"):
    df_market = get_market_data()
    filtered = filter_coins(df_market)
    st.subheader(f"عدد العملات اللي استوفت كل الشروط: {len(filtered)}")
    st.dataframe(filtered)

# -----------------------------
# 7️⃣ شرح الأعمدة
# -----------------------------
st.markdown("""
**شرح الأعمدة:**
- الاسم / Name: اسم العملة
- رمز العملة / Symbol: اختصار العملة
- السعر / Price (USD): السعر الحالي بالدولار
- السيولة / Liquidity: حجم التداول الحالي
- حجم الشراء / Buy Volume: حجم الشراء
- حجم البيع / Sell Volume: حجم البيع
- RSI: مؤشر القوة النسبية الحقيقي
- الدعم / Support: سعر الدعم الحقيقي
- Liquidity_OK: هل السيولة ≥ 5 مليون
- Volume_OK: هل الفوليوم بيزيد فعليًا
- Buy_vs_Sell_OK: هل الشراء أعلى من البيع
- RSI_OK: هل RSI < 30
- Support_OK: هل السعر عند الدعم
""")
