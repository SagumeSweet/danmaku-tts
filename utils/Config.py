import json

from Enums import DefaultConfigName


class ConfigGenerator:
    @classmethod
    def get_default_config(cls):
        default_config = {
            DefaultConfigName.rsocket_uri: "ws://localhost:9000",
            DefaultConfigName.task_id: [
                "id"
            ],
            DefaultConfigName.ttl_client: {
                DefaultConfigName.ai: {
                    DefaultConfigName.api_url: "http://localhost:9001",
                    DefaultConfigName.ref_audio_path: "audio",
                    DefaultConfigName.prompt_lang: "zh",
                    DefaultConfigName.target_lang: "zh",
                    DefaultConfigName.max_queue_size: 5
                }
            }
        }
        return default_config


    @classmethod
    def generate_temple_file(cls, path="../configTemple.json"):
        with open(path, "w", encoding="utf-8") as config_file:
            config_file.write(json.dumps(cls.get_default_config(), indent=2))

if __name__ == "__main__":
    ConfigGenerator.generate_temple_file()