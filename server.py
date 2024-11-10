import grpc
from concurrent import futures
import time
import banks_pb2_grpc
from branch import Branch

def serve(branch):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    banks_pb2_grpc.add_BankServiceServicer_to_server(branch, server)
    server.add_insecure_port(f'[::]:{50000 + branch.id}')
    server.start()
    print(f"Branch server {branch.id} started at port {50000 + branch.id}")
    server.wait_for_termination()
