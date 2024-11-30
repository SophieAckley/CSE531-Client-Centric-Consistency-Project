import grpc
import banks_pb2
import banks_pb2_grpc

class Customer:
    def __init__(self, id, requests):
        self.id = id
        self.requests = requests
        self.writeset = set()

    def execute_requests(self):
        responses = []
        for req in self.requests:
            with grpc.insecure_channel(f'localhost:{50000 + req["dest"]}') as channel:
                stub = banks_pb2_grpc.BankServiceStub(channel)
                if req["interface"] == "deposit":
                    response = stub.Deposit(banks_pb2.DepositRequest(
                        customer_id=self.id,
                        amount=req["money"],
                        writeset=list(self.writeset)
                    ))
                    self.writeset.update(response.writeset)
                elif req["interface"] == "withdraw":
                    response = stub.Withdraw(banks_pb2.WithdrawRequest(
                        customer_id=self.id,
                        amount=req["money"],
                        writeset=list(self.writeset)
                    ))
                    self.writeset.update(response.writeset)
                elif req["interface"] == "query":
                    response = stub.Query(banks_pb2.QueryRequest(
                        customer_id=self.id,
                        writeset=list(self.writeset)
                    ))
                    responses.append({
                        "interface": "query",
                        "branch": req["dest"],
                        "balance": response.balance
                    })
        return responses
