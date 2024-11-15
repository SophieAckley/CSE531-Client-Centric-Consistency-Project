import json
import time
from concurrent import futures
from branch import Branch
from customer import Customer
import server  # The `serve` function from server.py

def run_branch(branch_data):
    """Initialize and start a branch server."""
    branch = Branch(branch_data['id'], branch_data['balance'], [b['id'] for b in branches])
    server.serve(branch)

def run_customer(customer_data):
    """Create and execute events for a customer."""
    customer = Customer(customer_data['id'], customer_data['events'])
    return customer.executeEvents()

if __name__ == '__main__':
    # Load the input data
    with open('input.json', 'r') as f:
        data = json.load(f)

    # Separate branch and customer data
    branches = [item for item in data if item['type'] == 'branch']
    customers = [item for item in data if item['type'] == 'customer']

    # Output list for combined processes and events
    output = []

    # Start the branch servers
    executor = futures.ThreadPoolExecutor(max_workers=len(branches))
    branch_futures = [executor.submit(run_branch, branch) for branch in branches]

    # Give the branch servers time to initialize
    time.sleep(2)

    # Process customer events
    for customer in customers:
        result = run_customer(customer)
        output.append({
            "type": "customer",
            "id": customer['id'],
            "recv": result
        })
        # Add a delay to ensure events are processed sequentially
        time.sleep(1)

    # Append branch processes to the output
    for branch in branches:
        output.append({
            "type": "branch",
            "id": branch['id'],
            "balance": branch['balance']
        })

    # Write the combined output to a JSON file
    with open('output.json', 'w') as f:
        json.dump(output, f, indent=2)

    # Ensure all branch servers complete their tasks
    for future in branch_futures:
        future.result()

    print("All processes completed. Output written to output.json.")
