import grpc
import banks_pb2
import banks_pb2_grpc
import time
import logging

# 添加调试信息
print(dir(banks_pb2))  # 打印 banks_pb2 模块中的所有属性和方法

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Customer:
    def __init__(self, id, events, sleep_duration=0.5):
        self.id = id
        self.events = events
        self.recvMsg = []
        self.stub = None
        self.sleep_duration = sleep_duration
        self.writeset = set()

    def createStub(self, branch_id):
        try:
            channel = grpc.insecure_channel(f'localhost:{50000 + branch_id}')
            self.stub = banks_pb2_grpc.BankServiceStub(channel)
            logger.info(f"Stub created for Customer {self.id} to connect to Branch {branch_id}")
        except grpc.RpcError as e:
            logger.error(f"Failed to create stub for Customer {self.id} to Branch {branch_id}: {e.details()}")

    def execute_events(self):
        for event in self.events:
            interface = event.get('interface')
            branch_id = event.get('branch')
            
            if interface not in ['query', 'deposit', 'withdraw']:
                logger.error(f"Invalid interface '{interface}' in event {event['id']}")
                continue

            self.createStub(branch_id)

            try:
                # 检查 banks_pb2 是否包含 Request
                if not hasattr(banks_pb2, 'Request'):
                    logger.error("banks_pb2 does not have attribute 'Request'")
                request = banks_pb2.Request(
                    id=event['id'],
                    interface=interface,
                    money=event.get('money', 0),
                    writeset=list(self.writeset)
                )

                response = self.stub.MsgDelivery(request)
                if interface == 'query':
                    self.recvMsg.append({
                        "id": event['id'],
                        "interface": "query",
                        "balance": response.balance
                    })
                else:
                    self.recvMsg.append({
                        "id": event['id'],
                        "interface": interface,
                        "result": response.result
                    })
                    if response.result == "success" and interface in ['deposit', 'withdraw']:
                        self.writeset.add(response.write_id)

            except grpc.RpcError as e:
                logger.error(f"Error executing {interface} for Customer {self.id} on Branch {branch_id}: {e.details()}")

            time.sleep(self.sleep_duration)

        return self.recvMsg
