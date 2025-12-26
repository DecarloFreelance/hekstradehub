import requests
symbols = [
    'XBTUSDTM', 'XBTUSDM', 'XBTUSDCM', 'ETHUSDCM', 'ETHUSDM', 'ETHUSDTM',
    'SOLUSDM', 'SOLUSDTM', 'SOLUSDCM', 'BEATUSDTM', 'XRPUSDCM', 'XRPUSDM', 'XRPUSDTM',
    'RAVEUSDTM', 'ZECUSDTM', 'PIPPINUSDTM', 'HUSDTM', 'DOGEUSDCM', 'DOGEUSDM', 'DOGEUSDTM',
    'NIGHTUSDTM', 'BNBUSDTM', 'ANIMEUSDTM', 'SUIUSDCM', 'SUIUSDM', 'SUIUSDTM', 'AVAXUSDTM',
    'ASTERUSDTM', 'FOLKSUSDTM', 'HYPEUSDTM'
]
def kucoin_to_binance_symbol(symbol):
    s = symbol.replace('USDTM', 'USDT').replace('USDM', 'USDT').replace('USDCM', 'USDT')
    if s.startswith('XBT'):
        s = s.replace('XBT', 'BTC')
    return s
for symbol in symbols:
    binance_symbol = kucoin_to_binance_symbol(symbol)
    url = f'https://fapi.binance.com/fapi/v1/klines?symbol={binance_symbol}&interval=15m&limit=5'
    resp = requests.get(url)
    print(f'{symbol} -> {binance_symbol}: {resp.status_code} {resp.text[:100]}')
