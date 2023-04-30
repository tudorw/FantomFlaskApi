# python my_script.py deploy <private_key>
# python my_script.py read <contract_address>
# python my_script.py write <contract_address> <private_key> <function_args>
# python my_script.py events <contract_address> <event_name> --from_block <from_block> --to_block <to_block>
# python my_script.py send_raw_transaction <private_key> <raw_transaction>
#
# untested, use at your own risk!

import click
from flask import Flask, request, jsonify
from web3 import Web3
from solc import compile_source
from eth_account import Account
from web3.exceptions import ValidationError, TimeExhausted
import threading

# Set up Flask app
app = Flask(__name__)

# Connect to Fantom blockchain
w3 = Web3(Web3.HTTPProvider("https://rpc.ftm.tools"))

# Load and compile smart contract
with open("my_smart_contract.sol", "r") as file:
    contract_source_code = file.read()

compiled_contract = compile_source(contract_source_code)
contract_interface = compiled_contract['<stdin>:MySmartContract']
abi = contract_interface["abi"]
bytecode = contract_interface["bin"]

def get_contract_instance(contract_address):
    return w3.eth.contract(address=contract_address, abi=abi)

# API endpoint to deploy the smart contract
@app.route("/deploy", methods=["POST"])
def deploy_route():
    private_key = request.json["private_key"]
    return deploy(private_key)

@click.command("deploy")
@click.argument("private_key")
def deploy(private_key):
    try:
            private_key = request.json["private_key"]

    # Deploy the contract
    account = Account.from_key(private_key)
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.getTransactionCount(account.address)
    txn = contract.constructor().buildTransaction({
        'from': account.address,
        'gas': 1500000,
        'gasPrice': w3.eth.gasPrice,
        'nonce': nonce,
    })

    signed_txn = account.sign_transaction(txn)
    txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    txn_receipt = w3.eth.waitForTransactionReceipt(txn_hash)

    return jsonify({'contract_address': txn_receipt['contractAddress']})
    except (ValidationError, TimeExhausted) as e:
        return jsonify({"error": str(e)}), 400



    # API endpoint to read data from the smart contract
@app.route("/read", methods=["GET"])
def read_data_route():
    contract_address = request.args.get("contract_address")
    return read_data(contract_address)

@click.command("read")
@click.argument("contract_address")
def read_data(contract_address):
    try:
          contract_address = request.args.get("contract_address")
    	contract = get_contract_instance(contract_address)
	result = contract.functions.myFunction().call()
    	return jsonify({"data": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# API endpoint to write data to the smart contract
@app.route("/write", methods=["POST"])
def write_data_route():
    contract_address = request.json["contract_address"]
    private_key = request.json["private_key"]
    function_args = request.json["function_args"]
    return write_data(contract_address, private_key, function_args)

@click.command("write")
@click.argument("contract_address")
@click.argument("private_key")
@click.argument("function_args", nargs=-1)
def write_data(contract_address, private_key, function_args):
    try:
          contract_address = request.json["contract_address"]
    private_key = request.json["private_key"]
    # Replace with the appropriate function arguments
    function_args = request.json["function_args"]

    account = Account.from_key(private_key)
    contract = get_contract_instance(contract_address)
    nonce = w3.eth.getTransactionCount(account.address)

    txn = contract.functions.myFunction(*function_args).buildTransaction({
        'from': account.address,
        'gas': 1500000,
        'gasPrice': w3.eth.gasPrice,
        'nonce': nonce,
    })

    signed_txn = account.sign_transaction(txn)
    txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    txn_receipt = w3.eth.waitForTransactionReceipt(txn_hash)

    return jsonify({"transaction_hash": txn_hash.hex()})
    except (ValidationError, TimeExhausted) as e:
        return jsonify({"error": str(e)}), 400

# API endpoint to get events emitted by the smart contract
@app.route("/events", methods=["GET"])
def get_events_route():
    contract_address = request.args.get("contract_address")
    event_name = request.args.get("event_name")
    from_block = int(request.args.get("from_block", 0))
    to_block = request.args.get("to_block", "latest")
    return get_events(contract_address, event_name, from_block, to_block)

@click.command("events")
@click.argument("contract_address")
@click.argument("event_name")
@click.option("--from_block", default=0, type=int)
@click.option("--to_block", default="latest")
def get_events(contract_address, event_name, from_block, to_block):
    try:
         contract_address = request.args.get("contract_address")
    event_name = request.args.get("event_name")
    from_block = int(request.args.get("from_block", 0))
    to_block = request.args.get("to_block", "latest")

    contract = get_contract_instance(contract_address)
    event_filter = contract.events[event_name].createFilter(
        fromBlock=from_block,
        toBlock=to_block,
    )
    events = event_filter.get_all_entries()

    return jsonify({"events": events})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# API endpoint to send raw transactions
@app.route("/send_raw_transaction", methods=["POST"])
def send_raw_transaction_route():
    private_key = request.json["private_key"]
    raw_transaction = request.json["raw_transaction"]
    return send_raw_transaction(private_key, raw_transaction)

@click.command("send_raw_transaction")
@click.argument("private_key")
@click.argument("raw_transaction")
def send_raw_transaction(private_key, raw_transaction):
    try:
        private_key = request.json["private_key"]
        raw_transaction = request.json["raw_transaction"]

        account = Account.from_key(private_key)
        signed_txn = account.sign_transaction(raw_transaction)
        txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        txn_receipt = w3.eth.waitForTransactionReceipt(txn_hash)

        return jsonify({"transaction_hash": txn_hash.hex()})
    except (ValidationError, TimeExhausted) as e:
        return jsonify({"error": str(e)}), 400



@click.group()
def cli():
    pass
  
# Add commands to the CLI group
cli.add_command(deploy)
cli.add_command(read_data)
cli.add_command(write_data)
cli.add_command(get_events)
cli.add_command(send_raw_transaction)

# Run the Flask app and the CLI
if __name__ == "__main__":
    # Start the Flask app in a separate thread
    flask_thread = threading.Thread(target=app.run, kwargs={"debug": True})
    flask_thread.start()

    # Run the CLI
    cli()
