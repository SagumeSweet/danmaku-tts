from enum import StrEnum


class DefaultConfigName(StrEnum):
    danmaku_client = "danmakuClient"
    rsocket_ws_url = "rsocketUrL"
    task_id = "taskId"
    ttl_client = "ttlClient"
    ai = "ai"
    api_url = "apiUrl"
    ref_audio_root = "refAudioRoot"
    prompt_lang = "promptLang"
    target_lang = "targetLang"
    max_queue_size = "maxQueueSize"
    gs_root = "GPT-SoVitsRoot"