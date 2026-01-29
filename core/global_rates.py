from datetime import date
from typing import Dict

# 🔒 읽기 전용으로 쓰는 전역 상태
FX_DATE: date | None = None

FX_RATES: Dict[str, float] = {
    # 기준: KRW
    # "HKD": 170.23,
    # "USD": 1325.5,
}
