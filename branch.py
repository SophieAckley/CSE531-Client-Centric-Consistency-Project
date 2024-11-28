import grpc
import banks_pb2_grpc
import banks_pb2
from concurrent import futures
import logging
import time
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Branch(banks_pb2_grpc.BankServiceServicer):
    def __init__(self, id, balance, branches):
        self.id = id
        self.balance = balance
        self.branches = branches
        self.stubList = []
        self.recvMsg = []
        self.writeset = set()
        self.lock = threading.Lock()
        
        for branch_id in self.branches:
            if branch_id != self.id:
                channel = grpc.insecure_channel(f'localhost:{50000 + branch_id}')
                stub = banks_pb2_grpc.BankServiceStub(channel)
                self.stubList.append(stub)

    def MsgDelivery(self, request, context):
        self.recvMsg.append(request)
        
        if request.interface == "query":
            return self.Query(request, context)
        elif request.interface == "deposit":
            return self.Deposit(request, context)
        elif request.interface == "withdraw":
            return self.Withdraw(request, context)
        elif request.interface == "propagate_deposit":
            return self.Propagate_Deposit(request, context)
        elif request.interface == "propagate_withdraw":
            return self.Propagate_Withdraw(request, context)
        else:
            logger.error(f"Invalid interface requested: {request.interface}")
            return banks_pb2.Response(interface="error", result="Invalid interface")

    def Query(self, request, context):
        with self.lock:
            return banks_pb2.QueryResponse(balance=self.balance)

    def Deposit(self, request, context):
        with self.lock:
            if request.money < 0:
                logger.error("Deposit amount cannot be negative.")
                return banks_pb2.Response(interface="deposit", result="fail")

            client_writeset = set(request.writeset)
            if not client_writeset.issubset(self.writeset):
                logger.error("Monotonic write consistency violated.")
                return banks_pb2.Response(interface="deposit", result="fail")

            self.balance += request.money
            new_write_id = max(self.writeset) + 1 if self.writeset else 1
            self.writeset.add(new_write_id)
            self.Propagate_To_Branches("propagate_deposit", request.money, new_write_id)
            return banks_pb2.Response(interface="deposit", result="success", write_id=new_write_id)

    def Withdraw(self, request, context):
        with self.lock:
            if request.money < 0:
                logger.error("Withdrawal amount cannot be negative.")
                return banks_pb2.Response(interface="withdraw", result="fail")

            client_writeset = set(request.writeset)
            if not client_writeset.issubset(self.writeset):
                logger.error("Monotonic write consistency violated.")
                return banks_pb2.Response(interface="withdraw", result="fail")

            if self.balance >= request.money:
                self.balance -= request.money
                new_write_id = max(self.writeset) + 1 if self.writeset else 1
                self.writeset.add(new_write_id)
                self.Propagate_To_Branches("propagate_withdraw", request.money, new_write_id)
                return banks_pb2.Response(interface="withdraw", result="success", write_id=new_write_id)
            else:
                return banks_pb2.Response(interface="withdraw", result="fail")

    def Propagate_Deposit(self, request, context):
        with self.lock:
            self.balance += request.money
            self.writeset.add(request.write_id)
            return banks_pb2.Response(interface="propagate_deposit", result="success")

    def Propagate_Withdraw(self, request, context):
        with self.lock:
            self.balance -= request.money
            self.writeset.add(request.write_id)
            return banks_pb2.Response(interface="propagate_withdraw", result="success")

    def Propagate_To_Branches(self, interface, money, write_id):
        for stub in self.stubList:
            try:
                request = banks_pb2.Request(interface=interface, money=money, write_id=write_id)
                stub.MsgDelivery(request)
                time.sleep(0.1)
            except grpc.RpcError as e:
                logger.error(f"Error propagating to branch: {e.details()}")

def serve(branch):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    banks_pb2_grpc.add_BankServiceServicer_to_server(branch, server)
    server.add_insecure_port(f'[::]:{50000 + branch.id}')
    server.start()
    logger.info(f"Branch server started at port {50000 + branch.id}")
    server.wait_for_termination()
