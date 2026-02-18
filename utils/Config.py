import json

from Enums import DefaultConfigName


class ConfigGenerator:
    @classmethod
    def get_default_config(cls):
        default_config = {
            DefaultConfigName.danmaku_client: {
                DefaultConfigName.rsocket_ws_url: "ws://localhost:9000",
                DefaultConfigName.task_ids: [
                    "id"
                ],
            },
            DefaultConfigName.tts_client: {
                DefaultConfigName.max_queue_size: 5,
                DefaultConfigName.ai: {
                    DefaultConfigName.gs_root: "test/GPT-SoVITS",
                    DefaultConfigName.api_url: "http://localhost:9001",
                    DefaultConfigName.ref_audio_root: "test/audio",
                }
            }
        }
        return default_config

    @classmethod
    def generate_temple_file(cls, path="./configTemple.json"):
        with open(path, "w", encoding="utf-8") as config_file:
            config_file.write(json.dumps(cls.get_default_config(), indent=2))


if __name__ == "__main__":
    ConfigGenerator.generate_temple_file()
