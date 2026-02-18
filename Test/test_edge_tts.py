import logging

from Clients import EdgeTTSClient
from test_utils import TTSHandlerTest

logging.basicConfig(
    level=logging.DEBUG
)

if __name__ == "__main__":
    tester = TTSHandlerTest(EdgeTTSClient)
    tester.run()