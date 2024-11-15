import argparse
import json
import multiprocessing
import os
from concurrent import futures
from time import sleep

import grpc
from termcolor import colored

import branch_pb2_grpc
from Branch import Branch
from Customer import Customer

# Global var to store output file name
output_filename = None

# Start branch gRPC server process
def serveBranch(branch):
    branch.createStubs()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    branch_pb2_grpc.add_BranchServicer_to_server(branch, server)
    port = str(50000 + branch.id)
    server.add_insecure_port("[::]:" + port)
    server.start()
    server.wait_for_termination()


# Start customer gRPC client processes
def serveCustomer(customer, output_filename):
    # Execute events and get Customer balance output
    output = customer.executeEvents()

    # Interpret existing contents as JSON array & append new output entry
    output_json = json.load(open(output_filename))
    output_json.append(output)

    # Overwrite contents of output file with updated JSON
    output_file = open(output_filename, "w")
    output_file.write(json.dumps(output_json, indent=4))
    output_file.close()


# Parse JSON & create objects/processes
def createProcesses(processes):
    # List of Customer objects
    customers = []
    # List of Customer processes
    customerProcesses = []
    # List of Branch objects
    branches = []
    # List of Branch IDs
    branchIds = []
    # List of Branch processes
    branchProcesses = []

    # Instantiate Branch objects
    for process in processes:
        if process["type"] == "bank":
            branch = Branch(process["id"], process["balance"], branchIds)
            branches.append(branch)
            branchIds.append(branch.id)

    # Spawn Branch processes
    for branch in branches:
        branch_process = multiprocessing.Process(target=serveBranch, args=(branch,))
        branchProcesses.append(branch_process)
        branch_process.start()

    # Allow branch processes to start
    sleep(0.25)

    # Instantiate Customer objects
    for process in processes:
        if process["type"] == "customer":
            customer = Customer(process["id"], process["events"])
            customers.append(customer)

    # Spawn Customer processes
    for customer in customers:
        customer_process = multiprocessing.Process(target=serveCustomer, args=(customer, output_filename))
        customerProcesses.append(customer_process)
        customer_process.start()

    # Wait for Customer processes to complete
    for customerProcess in customerProcesses:
        customerProcess.join()

    # Terminate Branch processes
    for branchProcess in branchProcesses:
        branchProcess.terminate()


if __name__ == "__main__":
    # Setup command line argument for 'input_file'
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    args = parser.parse_args()

    try:
        # Load JSON file from 'input_file' arg
        input_file = open(args.input_file)
        input_json = json.load(input_file)

        # Initialize output file
        output_filename = "output/" + os.path.basename(input_file.name)
        output_file = open(output_filename, "w")
        output_file.write("[]")
        output_file.close()

        # Create objects/processes from input file
        createProcesses(input_json)
    except FileNotFoundError:
        print(colored("Could not find input file '" + args.input_file + "'", "red"))
    except json.decoder.JSONDecodeError:
        print(colored("Error decoding JSON file", "red"))
