from dotenv import load_dotenv
import os

load_dotenv(".env")
MQ_URL = "amqp://admin:IxvaikQqFDcnZeOS@hdx.iptime.org:5672"  # os.getenv("MQ_URL")
MQ_CONSUME_QUEUE = "comfyui.request"  # os.getenv("MQ_QUEUE")
