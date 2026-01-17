from faststream.rabbit import RabbitBroker
from src.conf.settings import settings

broker = RabbitBroker(settings.RABBIT_BROKER_URL)
