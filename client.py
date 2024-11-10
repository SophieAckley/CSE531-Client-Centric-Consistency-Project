import json
import grpc
import banks_pb2
import banks_pb2_grpc
import time

def run_customer(customer_id, events):
    channel = grpc.insecure_channel(f'localhost:{50000 + customer_id}')
    stub = banks_pb2_grpc.BankServiceStub(channel)

    for event in events:
        request = banks_pb2.Request(
            id=event['id'],
            interface=event['interface'],
            money=event.get('money', 0),
            logical_clock=0  # Initial clock value; will be updated in responses
        )
        response = stub.MsgDelivery(request)
        print(f"Customer {customer_id} received response: {response}")
        time.sleep(0.5)

# Load input and run clients
with open('input.json') as f:
    data = json.load(f)
    customers = [item for item in data if item['type'] == 'customer']

for customer in customers:
    run_customer(customer['id'], customer['events'])
