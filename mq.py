import pika
from util.logger import lg
import json
import os
import traceback
from myenv import MQ_URL


class RabbitMqStatus:
    Done = "Done"
    Rejected = "Rejected"
    Failed = "Failed"
    Error = "Error"


class RabbitMqPublisher:
    def __init__(self, mq_url):
        self.mq_url = mq_url
        # params = pika.URLParameters(mq_url)
        params = pika.URLParameters(f"{mq_url}/?heartbeat=20")
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)

    def publish(self, body: dict, publish_queue: str = None):
        with lg.context("mq.RabbitMqPublish.publish"):
            body = json.dumps(body)
            self.channel.basic_publish(exchange="", routing_key=publish_queue, body=body)

    def close(self):
        self.connection.close()


class RabbitMqConsumer:
    def __init__(self, mq_url, consume_queue, callback):
        self.mq_url = mq_url
        self.consume_queue = consume_queue
        self.callback = callback
        params = pika.URLParameters(f"{mq_url}/?heartbeat=20")
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)

    def subscribe(self):
        def on_message_callback(channel, method, props, input_body):
            try:
                with lg.context("mq.RabbitMqConsume.subscribe.on_message_callback"):
                    input_body = json.loads(input_body)
                    json_data = input_body["data"]["json"]
                    publish_queue = input_body["data"]["publish_queue"]
                    lg.verbose(f"consume: {input_body}")
                    try:
                        response = self.callback(json_data)
                        out_body = {
                            "pattern": publish_queue,
                            "data": {
                                "status": "Done",
                                "message": "",
                                "response": response
                            }
                        }
                    except Exception as e:
                        stack = traceback.format_exc()
                        out_body = {
                            "pattern": publish_queue,
                            "data": {
                                "status": RabbitMqStatus.Error,
                                "message": str(e),
                                "stack": stack,
                                "jobId": input_body["data"]["jobId"]
                            }
                        }
                        lg.warn(e)
                        lg.warn(stack)
                    lg.verbose(f"publish: {out_body}")
                    self.publish(out_body, publish_queue=publish_queue)
                    channel.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                lg.error(e)
                lg.error(traceback.format_exc())

        with lg.context("mq.RabbitMq.subscribe"):
            try:
                self.channel.basic_consume(queue=self.consume_queue, on_message_callback=on_message_callback)
                lg.log("waiting")
                self.channel.start_consuming()
            except KeyboardInterrupt:
                lg.log("interrupted by user")
                self.close()

    def close(self):
        self.connection.close()
