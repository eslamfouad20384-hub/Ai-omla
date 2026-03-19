import requests

def get_coin_data(contract):
    url = f"https://api.dexscreener.com/latest/dex/pairs/bsc/{contract}"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        pair = data['pair']
        print("اسم الزوج:", pair['baseToken']['symbol'], "/", pair['quoteToken']['symbol'])
        print("السعر الحالي:", pair['priceUsd'])
        print("السيولة:", pair['liquidityUsd'])
        print("حجم التداول 24 ساعة:", pair['volumeUsd'])
    else:
        print("مفيش بيانات متاحة للـ Contract ده")

# مثال على TRUMP/USDT على BSC
get_coin_data("0xd3ea9671245a6a08c546c1e0495c2d83613556e2")
