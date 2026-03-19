import streamlit as st
import pandas as pd
import numpy as np
import aiohttp
import asyncio
import time

st.set_page_config(page_title="Crypto Scanner أسرع نسخة 🔥", layout="wide")
st.title("Crypto Scanner بالعربي 🔍 - النسخة النهائية للسوق كله")

# -----------------------------
# جلب كل العملات من CoinGecko
# -----------------------------
async def fetch_page(session, page):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": str(250),
        "page": str(page),
        "sparkline": "false"
    }
    async with session.get(url, params=params) as resp:
        return await resp.json()

async def get_market_data_all():
    all_data = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        for page in range(1, 21):  # يغطي ~5000 عملة
            tasks.append(fetch_page(session, page))
        pages = await asyncio.gather(*tasks)
        for page_data in pages:
            if not page_data:
                continue
            all_data.extend(page_data)
    return pd.DataFrame(all_data)

# -----------------------------
# جلب بيانات OHLC لكل عملة
# -----------------------------
async def fetch_ohlc(session, coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency":"usd","days":30,"interval":"daily"}
    try:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            df = pd.DataFrame(data['prices'], columns=['timestamp','close'])
            df['close'] = df['close'].astype(float)
            return df
    except:
        return None

# -----------------------------
# حساب RSI
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
# حساب الدعم
# -----------------------------
def calculate_support(df, period=14):
    return df['close'].tail(period).min()

# -----------------------------
# معالجة كل العملات بالتوازي
# -----------------------------
async def process_coin(session, row):
    coin_id = row['id']
    hist = await fetch_ohlc(session, coin_id)
    if hist is None or hist.empty:
        return None

    rsi = calculate_RSI(hist)
    support = calculate_support(hist)
    volume_today = hist['close'].iloc[-1]
    volume_prev = hist['close'].iloc[-2] if len(hist)>1 else hist['close'].iloc[-1]
    volume_increasing = volume_today > volume_prev

    liquidity_ok = row['total_volume'] >= 5000000
    volume_ok = volume_increasing
    buy_volume = row['total_volume']*0.6
    sell_volume = row['total_volume']*0.4
    buy_vs_sell_ok = buy_volume > sell_volume
    rsi_ok = rsi < 30
    support_ok = row['current_price'] <= support

    return {
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
    }

async def process_all_coins(df_market):
    results = []
    async with aiohttp.ClientSession() as session:
        tasks = [process_coin(session, row) for _, row in df_market.iterrows()]
        all_results = await asyncio.gather(*tasks)
        for res in all_results:
            if res:
                results.append(res)
    return pd.DataFrame(results)

# -----------------------------
# واجهة Streamlit
# -----------------------------
st.markdown("### اضغط زر تحديث لجلب بيانات السوق كله وحساب كل الشروط بدقة")
if st.button("تحديث البيانات / Refresh Data"):
    st.info("جاري جلب بيانات السوق وحساب RSI لكل عملة... قد يستغرق دقيقة أو أكثر حسب عدد العملات")
    start_time = time.time()
    df_market = asyncio.run(get_market_data_all())
    filtered = asyncio.run(process_all_coins(df_market))
    st.subheader(f"عدد العملات اللي استوفت كل الشروط: {len(filtered)}")
    st.dataframe(filtered)
    st.success(f"تم التحديث في {time.time()-start_time:.2f} ثانية")
