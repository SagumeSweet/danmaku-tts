import logging

from Clients import AITTSClient
from Gui.ManagerCard import WeightsManagerCard
from test_utils import TTSHandlerTest

logging.basicConfig(
    level=logging.DEBUG
)

if __name__ == "__main__":
    tester = TTSHandlerTest(AITTSClient, WeightsManagerCard)
    tester.run()
