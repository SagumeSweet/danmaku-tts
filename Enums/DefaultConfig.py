from enum import StrEnum


class DefaultConfigName(StrEnum):
    danmaku_client = "danmakuClient"
    rsocket_ws_url = "rsocketUrL"
    task_ids = "taskIds"
    tts_client = "ttsClient"
    ai = "ai"
    api_url = "apiUrl"
    ref_audio_root = "refAudioRoot"
    target_lang = "targetLang"
    max_queue_size = "maxQueueSize"
    gs_root = "GPT-SoVitsRoot"
