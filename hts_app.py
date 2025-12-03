# HTS 전체 초기화 (EventBus, Services, etc.)

from core.event_bus import event_bus
from services.data_cache import data_cache

def init_hts_app():
    print("[HTS] Application initialized")
