import json
import time
from concurrent import futures
import grpc
import banks_pb2
import banks_pb2_grpc
from branch import Branch, serve
from customer import Customer
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_branch(branch_data, branches):
    branch = Branch(branch_data['id'], branch_data['balance'], [b['id'] for b in branches])
    serve(branch)

def run_customer(customer_data):
    customer = Customer(customer_data['id'], customer_data['events'])
    return customer.execute_events()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        logger.error("Usage: python main.py input.json")
        sys.exit(1)

    input_file = sys.argv[1]

    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"{input_file} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Error decoding {input_file}. Please check the file format.")
        sys.exit(1)

    branches = [item for item in data if item['type'] == 'branch']
    customers = [item for item in data if item['type'] == 'customer']

    executor = futures.ThreadPoolExecutor(max_workers=len(branches))
    branch_futures = [executor.submit(run_branch, branch, branches) for branch in branches]
    logger.info(f"Started {len(branches)} branch servers")

    time.sleep(2)

    output = []
    for customer in customers:
        result = run_customer(customer)
        output.append({"id": customer['id'], "balance": result})
        time.sleep(0.5)

    try:
        with open('output.json', 'w') as f:
            json.dump(output, f, indent=2)
        logger.info("Output successfully written to output.json")
    except IOError as e:
        logger.error(f"Failed to write output.json: {e}")

    executor.shutdown(wait=True)
    logger.info("All processes completed.")
