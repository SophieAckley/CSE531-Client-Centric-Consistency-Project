import grpc
import banks_pb2
import banks_pb2_grpc
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Customer:
    def __init__(self, id, events, sleep_duration=0.5):
        self.id = id
        self.events = events  # Store customer events
        self.recvMsg = []  # Messages received from the server
        self.stub = None  # gRPC stub
        self.sleep_duration = sleep_duration
        self.writeset = set()  # Writeset to track write operations

    def createStub(self, branch_id):
        """Create a gRPC stub for the specified branch."""
        try:
            channel = grpc.insecure_channel(f'localhost:{50000 + branch_id}')
            self.stub = banks_pb2_grpc.BankServiceStub(channel)
            logger.info(f"Stub created for Customer {self.id} to connect to Branch {branch_id}")
        except grpc.RpcError as e:
            logger.error(f"Failed to create stub for Customer {self.id} to Branch {branch_id}: {e.details()}")

    async def execute_event(self, event):
        """Execute a single event for the customer."""
        interface = event.get("interface")
        branch_id = event.get("branch")

        if interface not in ["query", "deposit", "withdraw"]:
            logger.error(f"Invalid interface '{interface}' in event {event['id']}")
            return

        self.createStub(branch_id)

        try:
            # Create request based on the interface
            request = banks_pb2.Request(
                id=event["id"],
                interface=interface,
                money=event.get("money", 0),
                writeset=list(self.writeset)
            )

            # Send the request and process the response
            response = self.stub.MsgDelivery(request)
            if interface == "query":
                self.recvMsg.append({
                    "id": event["id"],
                    "interface": "query",
                    "balance": response.balance
                })
            else:
                self.recvMsg.append({
                    "id": event["id"],
                    "interface": interface,
                    "result": response.result
                })
                if response.result == "success" and interface in ["deposit", "withdraw"]:
                    self.writeset.add(response.write_id)

        except grpc.RpcError as e:
            logger.error(f"Error executing {interface} for Customer {self.id} on Branch {branch_id}: {e.details()}")

        await asyncio.sleep(self.sleep_duration)

    async def execute_events(self):
        """Execute all events sequentially."""
        tasks = [self.execute_event(event) for event in self.events]
        await asyncio.gather(*tasks)
        return self.recvMsg

    async def run(self):
        """Run the customer operations."""
        return await self.execute_events()
