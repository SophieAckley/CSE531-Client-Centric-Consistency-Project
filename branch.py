import grpc
import banks_pb2
import banks_pb2_grpc

class Branch(banks_pb2_grpc.BankServiceServicer):
    def __init__(self, id, balance, branches):
        self.id = id
        self.balance = balance
        self.branches = branches
        self.writeset = set()  # Store IDs of processed write operations

    def Deposit(self, request, context):
        # Generate unique write ID
        write_id = f"{self.id}-deposit-{len(self.writeset) + 1}"
        self.writeset.add(write_id)
        self.balance += request.amount

        # Return response
        return banks_pb2.DepositResponse(result="success", writeset=list(self.writeset))

    def Withdraw(self, request, context):
        # Generate unique write ID
        write_id = f"{self.id}-withdraw-{len(self.writeset) + 1}"
        if self.balance >= request.amount:
            self.writeset.add(write_id)
            self.balance -= request.amount
            return banks_pb2.WithdrawResponse(result="success", writeset=list(self.writeset))
        else:
            return banks_pb2.WithdrawResponse(result="fail", writeset=list(self.writeset))

    def Query(self, request, context):
        # Update writeset with missing writes from the customer
        for write_id in request.writeset:
            if write_id not in self.writeset:
                self.writeset.add(write_id)

        # Return balance and updated writeset
        return banks_pb2.QueryResponse(balance=self.balance, writeset=list(self.writeset))

    # Add Propagation Methods for Inter-Branch Communication if Necessary
