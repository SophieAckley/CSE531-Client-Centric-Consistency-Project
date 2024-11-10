import grpc
import banks_pb2
import banks_pb2_grpc

class Branch(banks_pb2_grpc.BankServiceServicer):
    def __init__(self, id, balance, branches):
        self.id = id
        self.balance = balance
        self.branches = branches
        self.logical_clock = 0

    def MsgDelivery(self, request, context):
        self.logical_clock = max(self.logical_clock, request.logical_clock) + 1
        if request.interface == "query":
            return banks_pb2.Response(
                interface="query",
                result="success",
                balance=self.balance,
                logical_clock=self.logical_clock
            )
        elif request.interface == "deposit":
            self.balance += request.money
            self.logical_clock += 1
            return banks_pb2.Response(
                interface="deposit",
                result="success",
                balance=self.balance,
                logical_clock=self.logical_clock
            )
        elif request.interface == "withdraw":
            if self.balance >= request.money:
                self.balance -= request.money
                self.logical_clock += 1
                return banks_pb2.Response(
                    interface="withdraw",
                    result="success",
                    balance=self.balance,
                    logical_clock=self.logical_clock
                )
            else:
                return banks_pb2.Response(
                    interface="withdraw",
                    result="fail",
                    balance=self.balance,
                    logical_clock=self.logical_clock
                )
