from fake_useragent import UserAgent
from web3 import Web3, HTTPProvider, Account
import requests
import json, random, time
import os
import colorlog
import logging
from colorama import init, Fore
from datetime import datetime



with open("Json_data.JSON", 'r') as f:
    config = json.load(f)
with open('private_keys.txt', 'r') as keys_file:
    private_keys = keys_file.read().splitlines()




desired_gas_price = int(input("Please enter your desired gas price: "))
min_delay = int(input("Please enter your minimum delay: "))
max_delay = int(input("Please enter your maximum delay: "))
Invite_per_linc = int(input("How mach refs per account you want?: "))


class ReferralSystem:
    def __init__(self, filename, usage_file='link_usage.json'):
        """
        Initialize the ReferralSystem with the provided filenames.

        Parameters:
        - filename: The name of the file containing the list of referral links.
        - usage_file: The name of the file tracking the usage of each link. Defaults to 'link_usage.json'.
        """
        self.filename = filename
        self.usage_file = usage_file

        # Load the list of referral links from the provided file.
        with open(filename, 'r') as f:
            self.links = f.read().splitlines()

        # If a usage file exists, load the link usage data; otherwise, initialize an empty dictionary.
        if os.path.exists(usage_file):
            with open(usage_file, 'r') as f:
                self.link_usage = json.load(f)
        else:
            self.link_usage = {}

    def get_link(self):
        """
        Fetch a referral link that hasn't reached its maximum usage limit.

        Returns:
        - A referral link as a string, or None if all links have reached their maximum usage.
        """
        for link in self.links:
            # Initialize the link usage count if not already tracked.
            if link not in self.link_usage:
                self.link_usage[link] = 0

            # Return the link if it hasn't reached the maximum usage limit.
            if self.link_usage[link] < Invite_per_linc:
                return link

        # If all links have reached their maximum usage, return None.
        return None

    def increment_link_usage(self, link):
        """
        Increment the usage count for a given referral link.

        Parameters:
        - link: The referral link whose usage is to be incremented.
        """
        # If the link exists in the usage data, increment its count.
        if link in self.link_usage:
            self.link_usage[link] += 1

            # Save the updated usage data to the file.
            self.save_link_usage()

            # If the link has reached its maximum usage, cleanup the links list.
            if self.link_usage[link] == Invite_per_linc:
                self.cleanup_links()

    def save_link_usage(self):
        """Save the current link usage data to the usage file."""
        with open(self.usage_file, 'w') as f:
            json.dump(self.link_usage, f)

    def cleanup_links(self):
        """
        Remove referral links from the list that have reached their maximum usage limit and update the links file.
        """
        # Filter out links that have reached their maximum usage.
        self.links = [link for link in self.links if self.link_usage.get(link, 0) < Invite_per_linc]

        # Save the cleaned-up list of links back to the file.
        with open(self.filename, 'w') as f:
            for link in self.links:
                f.write(link + '\n')
def SetupGayLogger(logger_name):
    """
    SetupGayLogger initializes a colorful logging mechanism, presenting each log message in a beautiful
    rainbow sequence. The function accepts a logger name and returns a logger instance that can be used
    for logging messages.

    Parameters:
    - logger_name (str): A name for the logger.

    Returns:
    - logger (Logger): A configured logger instance.
    """

    # Initialize the colorama library, which provides an interface for producing colored terminal text.
    init()

    def rainbow_colorize(text):
        """
        Transforms a given text into a sequence of rainbow colors.

        Parameters:
        - text (str): The text to be colorized.

        Returns:
        - str: The rainbow colorized text.
        """
        # Define the sequence of colors to be used.
        colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
        colored_message = ''

        # For each character in the text, assign a color from the sequence.
        for index, char in enumerate(text):
            color = colors[index % len(colors)]
            colored_message += color + char

        # Return the colorized text and reset the color.
        return colored_message

    class RainbowColoredFormatter(colorlog.ColoredFormatter):
        """
        Custom logging formatter class that extends the ColoredFormatter from the colorlog library.
        This formatter first applies rainbow colorization to the entire log message before using the
        standard level-based coloring.
        """

        def format(self, record):
            """
            Format the log record. Overridden from the base class to apply rainbow colorization.

            Parameters:
            - record (LogRecord): The log record.

            Returns:
            - str: The formatted log message.
            """
            # First rainbow colorize the entire message.
            message = super().format(record)
            rainbow_message = rainbow_colorize(message)
            return rainbow_message

    # Obtain an instance of a logger for the provided name.
    logger = colorlog.getLogger(logger_name)

    # Ensure that if there are any pre-existing handlers attached to this logger, they are removed.
    # This prevents duplicate messages from being displayed.
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])

    # Create a stream handler to output log messages to the console.
    handler = colorlog.StreamHandler()

    # Assign the custom formatter to the handler.
    handler.setFormatter(
        RainbowColoredFormatter(
            "|%(log_color)s%(asctime)s| - Profile [%(name)s] - %(levelname)s - %(message)s",
            datefmt=None,
            reset=False,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={},
            style='%'
        )
    )

    # Attach the handler to the logger.
    logger.addHandler(handler)

    # Set the minimum logging level to DEBUG. This means messages of level DEBUG and above will be processed.
    logger.setLevel(logging.DEBUG)

    return logger
def wait_for_gas_price_to_decrease(node_url, desired_gas_price):
    """
    This function checks the current base fee of Ethereum blockchain from a specific node
    and waits until it decreases to the desired level.

    :param node_url: URL of the Ethereum node.
    :param desired_gas_price: Desired base fee in Gwei.
    """
    while True:
        try:
            # Fetching the base fee for the latest block
            data = {
                "jsonrpc":"2.0",
                "method":"eth_getBlockByNumber",
                "params":['latest', True],
                "id":1
            }

            headers = {'Content-Type': 'application/json'}
            response = requests.post(node_url, headers=headers, data=json.dumps(data))
            response.raise_for_status()

            result = response.json()['result']
            current_base_fee = int(result['baseFeePerGas'], 16) / 10**9  # Convert from Wei to Gwei

        except requests.exceptions.HTTPError as errh:
            print(f"HTTP Error: {errh}")
            time.sleep(10)  # Retry after 10 sec in case of a HTTP error
            continue
        except requests.exceptions.ConnectionError as errc:
            print(f"Error Connecting: {errc}")
            time.sleep(10)  # Retry after 10 sec in case of a connection error
            continue

        if current_base_fee <= desired_gas_price:
            break  # Exit the loop if the base fee is less than or equal to the desired level
        else:
            print(
                f"Current base fee ({current_base_fee} Gwei) is higher than desired ({desired_gas_price} Gwei). Waiting...",
                end="", flush=True)
            time.sleep(10)  # Message displayed for 10 seconds
            print("\033[K", end="\r", flush=True)  # Check the base fee every 10 sec
def get_sign(main_address: str, referrer: str):
    """
    Fetches a signature for a given main address and referrer using a third-party API.

    Parameters:
    - main_address: The primary Ethereum address.
    - referrer: The referring Ethereum address.

    Returns:
    - The signature as a string.
    """
    while True:
        try:
            # Construct the URL for the third-party API endpoint.
            url = f'https://mint.fun/api/mintfun/fundrop/mint?address={main_address}&referrer={referrer}'

            # Define headers for the request, including a random user agent.
            headers = {
                'User-Agent': UserAgent().random,
                'Referer': f'https://mint.fun/fundrop?ref={referrer}',
            }

            # Make the GET request.
            resp = requests.get(url, headers=headers)

            # If the response is successful, extract the signature and return it.
            if resp.status_code == 200:
                response_data = json.loads(resp.text)
                return response_data['signature']

        except Exception as e:
            # Log any exceptions encountered during the request.
            print(f"Error encountered: {e}")
def mint(config, private_key, logger):
    """
    Executes a minting operation on the Ethereum blockchain using the "MintFun" contract.

    Parameters:
    - config: Configuration data containing network and contract details.
    - private_key: The private key used to sign and send the transaction.
    - logger: A logging object to record process information.

    Returns:
    - 1 if the transaction was successful, 0 otherwise.
    """
    # Initialize a connection to the Ethereum network.
    w3 = Web3(HTTPProvider(config['networks']['Ethereum']['url']))

    # Derive the account details from the given private key.
    account = w3.eth.account.from_key(private_key)
    address_checksum = w3.to_checksum_address(account.address)

    # Extract the contract details from the provided configuration.
    contract_name = "MintFun"
    contract_details = config['contracts'][contract_name]
    contract_address = w3.to_checksum_address(contract_details['address'])
    contract = w3.eth.contract(address=contract_address, abi=contract_details['abi'])

    # Fetch the current base fee from the Ethereum network.
    base_fee = w3.eth.fee_history(w3.eth.get_block_number(), 'latest')['baseFeePerGas'][-1]
    priority_max = w3.to_wei(0.6, 'gwei')

    # Fetch a referral link from the ReferralSystem.
    ref_sys = ReferralSystem('ref_links.txt')
    link = ref_sys.get_link()
    if link is None:
        logger.error("No referral links available. Exiting...")
        exit("System termination")

    # Convert the referral link to a checksum address.
    referrer = w3.to_checksum_address(str(link))

    # Get a signature for the transaction.
    signature = get_sign(address_checksum, referrer)

    # Build the minting transaction.
    mint_txn = contract.functions.mint(referrer, signature).build_transaction({
        'from': address_checksum,
        'nonce': w3.eth.get_transaction_count(account.address),
        'maxFeePerGas': base_fee + priority_max,
        'maxPriorityFeePerGas': priority_max
    })

    # Estimate the gas limit for the transaction and update the transaction details.
    estimated_gas_limit = round(w3.eth.estimate_gas(mint_txn))
    mint_txn.update({'gas': estimated_gas_limit})

    # Sign the transaction using the private key.
    signed_txn = w3.eth.account.sign_transaction(mint_txn, private_key)

    # Send the signed transaction to the Ethereum network and wait for a receipt.
    try:
        txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        txn_receipt = w3.eth.wait_for_transaction_receipt(txn_hash, timeout=666)
    except (ValueError, Exception) as e:  # Handling both exceptions.
        logger.warning(f"Error sending transaction: {e}")
        with open('failed_transactions.txt', 'a') as f:
            f.write(f'{address_checksum}, transaction failed due to error: {e}\n')
        return 0

    # Check the transaction status and handle accordingly.
    if txn_receipt['status'] == 1:
        ref_sys.increment_link_usage(link)
        if private_key in private_keys:  # Assuming private_keys is a global variable.
            private_keys.remove(private_key)

        # Save the updated private keys list.
        with open('private_keys.txt', 'w') as keys_file:
            for key in private_keys:
                keys_file.write(key + '\n')

        logger.info(f"Transaction successful. Txn hash: https://etherscan.io/tx/{txn_hash.hex()}")
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open('successful_transactions.txt', 'a') as f:
            f.write(
                f'{current_timestamp}, {address_checksum}, successful transaction, Txn hash: https://etherscan.io/tx/{txn_hash.hex()}\n')
        return 1
    else:
        logger.warning(f"Transaction failed. Txn hash: https://etherscan.io/tx/{txn_hash.hex()}")
        with open('failed_transactions.txt', 'a') as f:
            f.write(f'{address_checksum}, transaction failed, Txn hash: https://etherscan.io/tx/{txn_hash.hex()}\n')
        return 0


def main():
    """
    The main execution point of the script.

    The function initializes a logger, shuffles a list of private keys, and processes each private key to perform minting operations.
    After each minting operation, the script waits for a random duration before processing the next key.
    """
    # Print the author's channel (consider removing or updating this for security and professionalism).
    print("Author channel: https://t.me/CryptoBub_ble")

    # Shuffle the list of private keys for randomness (assuming private_keys is a global variable).
    random.shuffle(private_keys)

    # Initialize the logger.
    logger = SetupGayLogger("logger")  # Consider renaming the function for professionalism.

    # Iterate through each private key.
    for id, private_key in enumerate(private_keys):
        # Derive the Ethereum address from the private key.
        account = Account.from_key(private_key)

        # Wait until the gas price decreases to the desired level.
        wait_for_gas_price_to_decrease("https://ethereum.publicnode.com",
                                       desired_gas_price)  # Assuming desired_gas_price is a global variable.

        # Log the start of the minting operation for the current address.
        logger.info(f"Started work with wallet: {account.address}")

        # Perform the minting operation.
        mint(config, private_key, logger)  # Assuming config is a global variable.

        # Wait for a random duration between min_delay and max_delay before the next minting operation.
        sleep_duration = random.randint(min_delay, max_delay)  # Assuming min_delay and max_delay are global variables.
        logger.warning(f"Sleeping for {sleep_duration} seconds before next operation...")

        # Log the author's channel again (consider removing or updating this for security and professionalism).
        logger.error("Subscribe - https://t.me/CryptoBub_ble")

        # Sleep for the determined duration.
        time.sleep(sleep_duration)


# Execute the main function when the script is run.
if __name__ == '__main__':
    main()