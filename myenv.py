from dotenv import load_dotenv
import os

load_dotenv(".env")
MQ_URL = os.getenv("MQ_URL")  # "amqp://admin:IxvaikQqFDcnZeOS@hdx.iptime.org:5672"  # os.getenv("MQ_URL")
MQ_CONSUME_QUEUE = os.getenv("MQ_QUEUE")  # "comfyui.request"  # os.getenv("MQ_QUEUE")

print('myenv.py')
print(MQ_URL)
print(MQ_CONSUME_QUEUE)
