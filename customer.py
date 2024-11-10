import grpc
import banks_pb2
import banks_pb2_grpc
import time

class Customer:
    def __init__(self, id, events):
        self.id = id
        self.events = events
        self.recvMsg = []
        self.stub = None

    def createStub(self):
        channel = grpc.insecure_channel(f'localhost:{50000 + self.id}')
        self.stub = banks_pb2_grpc.BankServiceStub(channel)

    def executeEvents(self):
        if not self.stub:
            self.createStub()

        logical_clock = 0
        for event in self.events:
            logical_clock += 1  # Increment clock for each event
            request = banks_pb2.Request(
                id=event['id'],
                interface=event['interface'],
                money=event.get('money', 0),
                logical_clock=logical_clock
            )
            response = self.stub.MsgDelivery(request)
            logical_clock = max(logical_clock, response.logical_clock) + 1
            self.recvMsg.append(response)
            time.sleep(0.5)
        return self.recvMsg
