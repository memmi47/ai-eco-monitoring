import pandas as pd
import yfinance as yf
import numpy as np
import requests
import time

# 환율 캐시 (통화 -> USD 환율)
exchange_rates = {"USD": 1.0}

def get_exchange_rate(currency):
    """지정된 통화를 USD로 변환하는 환율을 반환합니다."""
    if not currency or pd.isna(currency) or currency == "USD":
        return 1.0
    if currency in exchange_rates:
        return exchange_rates[currency]
    
    # 공통적인 환율 티커 패턴 시도 (예: KRWUSD=X 또는 USDKRW=X)
    try:
        # 1. {currency}USD=X (1 EUR = X USD 등)
        rate = yf.Ticker(f"{currency}USD=X").history(period="1d")["Close"].iloc[-1]
        if not pd.isna(rate) and rate > 0:
            exchange_rates[currency] = rate
            return rate
    except:
        pass

    try:
        # 2. USD{currency}=X (1 USD = X KRW 등) -> 역산
        rate = yf.Ticker(f"USD{currency}=X").history(period="1d")["Close"].iloc[-1]
        if not pd.isna(rate) and rate > 0:
            usd_rate = 1.0 / rate
            exchange_rates[currency] = usd_rate
            return usd_rate
    except:
        pass

    print(f"Warning: {currency} 환율을 가져올 수 없습니다. 1.0을 사용합니다.")
    exchange_rates[currency] = 1.0
    return 1.0

# 1. 파일 로드 및 열 삽입 구조화
file_path = '/Users/jungdo/Desktop/AI_Factory_Ecosystem_Database.csv'
df = pd.read_csv(file_path)

target_col_index = df.columns.get_loc('상장여부') + 1
df.insert(target_col_index, 'Ticker', np.nan)
df.insert(target_col_index + 1, '보고통화', np.nan)
df.insert(target_col_index + 2, '시가총액(USD M)', np.nan)
df.insert(target_col_index + 3, '매출액(USD M)', np.nan)

# 2. 기업명 기반 티커 자동 검색 함수
def get_ticker_from_name(company_name):
    # Yahoo Finance API 검색 엔드포인트 활용
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={company_name}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        
        # 검색된 결과 중 첫 번째 일반 주식(EQUITY) 티커 반환
        for quote in data.get('quotes', []):
            if quote.get('quoteType') == 'EQUITY':
                return quote.get('symbol')
        return None
    except Exception:
        return None

# 3. 재무 데이터 크롤링 함수
def fetch_financials(ticker_symbol):
    if not pd.isna(ticker_symbol) and ticker_symbol:
        try:
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            
            # 통화 정보 확인
            currency = info.get('currency', 'USD')
            rate = get_exchange_rate(currency)
            
            # 원시 데이터 가져오기
            mkt_cap_raw = info.get('marketCap', 0)
            revenue_raw = info.get('totalRevenue', 0)
            
            # USD로 변환 및 백만 달러($M) 단위로 조정
            mkt_cap_usd = (mkt_cap_raw * rate) / 1_000_000
            revenue_usd = (revenue_raw * rate) / 1_000_000
            
            # 데이터가 0인 경우 NaN 처리
            return round(mkt_cap_usd, 2) if mkt_cap_usd > 0 else np.nan, \
                   round(revenue_usd, 2) if revenue_usd > 0 else np.nan, \
                   currency
        except Exception as e:
            return np.nan, np.nan, 'Unknown'
    return np.nan, np.nan, np.nan

# 4. 데이터 자동 매핑 실행 (상장사에 한함)
print("상장사 티커 및 재무 데이터 검색을 시작합니다. (약 1~2분 소요)")
for index, row in df.iterrows():
    if row['상장여부'] == '상장':
        company_name = row['회사명']
        
        # 기업명에 티커가 이미 포함된 경우(예: Forgent (NYSE: FPS)) 예외 처리 로직 추가 가능
        
        # 티커 자동 검색
        ticker = get_ticker_from_name(company_name)
        df.at[index, 'Ticker'] = ticker
        
        # 재무 데이터 추출 (USD 변환 및 보고통화 감지)
        mkt_cap_usd, revenue_usd, reporting_currency = fetch_financials(ticker)
        df.at[index, '보고통화'] = reporting_currency
        df.at[index, '시가총액(USD M)'] = mkt_cap_usd
        df.at[index, '매출액(USD M)'] = revenue_usd
        
        # API 과부하 방지 딜레이
        time.sleep(0.5)

# 5. 최종 파일 저장
output_filename = 'Updated_AI_Factory_Ecosystem_Auto.xlsx'
df.to_excel(output_filename, index=False)
print(f"작업 완료: {output_filename} 파일이 생성되었습니다. 'Ticker' 열의 정확성을 확인해주세요.")