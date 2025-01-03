import json
import time
import grpc
import banks_pb2
import banks_pb2_grpc
from customer import Customer
import asyncio

async def run_customer(customer_data):
    customer = Customer(customer_data['id'], customer_data['events'])
    return await customer.execute_events()

def create_stub(branch_id):
    """Create a gRPC stub for the specified branch ID."""
    port = 50000 + branch_id  # Map branch ID to its port
    channel = grpc.insecure_channel(f'localhost:{port}')
    return banks_pb2_grpc.BankServiceStub(channel)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python client.py input.json")
        sys.exit(1)

    input_file = sys.argv[1]
    
    with open(input_file, 'r') as f:
        data = json.load(f)

    customers = [item for item in data if item['type'] == 'customer']
    output = []

    async def main():
        for customer in customers:
            result = await run_customer(customer)
            if any(event['interface'] == 'query' for event in customer['events']):
                output.append({"id": customer['id'], "balance": result})
            else:
                output.append({"id": customer['id'], "balance": result[-1] if result else 0})
            await asyncio.sleep(0.5)

    asyncio.run(main())

    with open('output.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("All customer processes completed. Output written to output.json")
