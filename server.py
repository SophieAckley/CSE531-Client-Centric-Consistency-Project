import json
import time
from concurrent import futures
import grpc
import banks_pb2
import banks_pb2_grpc
from branch import Branch

def serve(branch):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    banks_pb2_grpc.add_BankServiceServicer_to_server(branch, server)
    server.add_insecure_port(f'[::]:{50000 + branch.id}')
    server.start()
    return server

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python server.py input.json")
        sys.exit(1)

    input_file = sys.argv[1]
    
    with open(input_file, 'r') as f:
        data = json.load(f)

    branches = [item for item in data if item['type'] == 'branch']
    branch_processes = []

    for branch_data in branches:
        branch = Branch(
            id=branch_data['id'],
            balance=branch_data['balance'],
            branches=[b['id'] for b in branches]
        )
        server = serve(branch)
        branch_processes.append((branch, server))

    print(f"Started {len(branch_processes)} branch servers")

    try:
        while True:
            time.sleep(86400)  # Sleep for a day
    except KeyboardInterrupt:
        print("Stopping servers...")
        for _, server in branch_processes:
            server.stop(0)
