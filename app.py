import logging

from src.client import client
import src.start_handler
import src.reset_handler
import src.image_input
import src.image_output

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.WARNING
)

client.parse_mode = 'html'
client.run_until_disconnected()
