import logging

from src.client import client

#import src.io.input.image
#import src.io.input.reset
#import src.io.input.start

import src.io.output.image

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.WARNING
)

client.parse_mode = 'html'
client.run_until_disconnected()
