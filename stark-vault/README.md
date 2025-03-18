# Simfony Transaction CLI

A simple CLI application for creating and signing Bitcoin transactions with Simfony programs.

## Prerequisites

- Rust and Cargo installed
- A Bitcoin wallet with a mnemonic phrase

## Installation

Clone the repository and build the application:

```bash
git clone <repository-url>
cd simfony-stark-verifier
cargo build --release
```

## Usage

The CLI application supports two commands:

### Create a transaction

Creates a transaction with a Simfony program:

```bash
cargo run --bin elementsd-tests -- create --simf <path-to-simf-file> --txid <txid> --vout <vout> [--env-file <path-to-env-file>]
```

Arguments:
- `--simf`: Path to the Simfony program file
- `--txid`: Transaction hash (TXID) of the UTXO to spend
- `--vout`: Output index (VOUT) of the UTXO to spend
- `--env-file`: (Optional) Path to the .env file containing MNEMONIC variable (default: .env)

### Spend a transaction

Spends a UTXO locked with a Simfony program:

```bash
cargo run --bin elementsd-tests -- spend --simf <path-to-simf-file> --wit <path-to-witness-file> --txid <txid> --vout <vout> [--env-file <path-to-env-file>]
```

Arguments:
- `--simf`: Path to the Simfony program file
- `--wit`: Path to the witness file
- `--txid`: Transaction hash (TXID) of the UTXO to spend
- `--vout`: Output index (VOUT) of the UTXO to spend
- `--env-file`: (Optional) Path to the .env file containing MNEMONIC variable (default: .env)

## Environment Variables

The application requires a `.env` file with the following variable:

```
MNEMONIC="your mnemonic phrase here"
```

## Example

1. Create a transaction:

```bash
cargo run --bin elementsd-tests -- create --simf examples/p2pkh.simf --txid abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890 --vout 0
```

2. Spend a transaction:

```bash
cargo run --bin elementsd-tests -- spend --simf examples/p2pkh.simf --wit examples/p2pkh.wit --txid abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890 --vout 0
```

## Output

The application will output the transaction as a hexadecimal string, which can be broadcast to the Bitcoin network using a Bitcoin client or API.
