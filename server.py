import grpc
from concurrent import futures
import banks_pb2_grpc
from branch import Branch

def serve(branch, port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    banks_pb2_grpc.add_BankServiceServicer_to_server(branch, server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"Branch {branch.id} started on port {port}")
    return server

if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) != 2:
        print("Usage: python server.py input.json")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        data = json.load(f)

    branches = [item for item in data if item["type"] == "branch"]
    servers = []
    for branch_data in branches:
        branch = Branch(branch_data["id"], branch_data["balance"], [b["id"] for b in branches])
        port = 50000 + branch_data["id"]
        servers.append(serve(branch, port))

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        for server in servers:
            server.stop(0)
