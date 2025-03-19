# Simfony wallet

A simple CLI application for spending funds locked with a Simplicity script, compiled down from a Simfony program.

## Prerequisites

- Rust and Cargo installed
- `.env` file with `MNEMONIC` variable set (generate random)

## Usage

### Show address

```bash
cargo run -- address --simf-file <path-to-simf-file> [--env-file <path-to-env-file>] [--account <account-index>] [--show-secret]
```

Arguments:
- `--simf-file`: Path to the Simfony program file
- `--env-file`: (Optional) Path to the .env file containing MNEMONIC variable (default: .env)
- `--account`: (Optional) Account index to derive keys from (default: 0)
- `--show-secret`: (Optional) Show the secret key (default: false)

### Spend funds locked in a STARK vault

```bash
cargo run -- spend --simf-file <path-to-simf-file> --txid <txid> --vout <vout> --address <recipient-address> [--wit-file <path-to-witness-file>] [--env-file <path-to-env-file>] [--account <account-index>] [--dry-run]
```

Arguments:
- `--simf-file`: Path to the Simfony program file
- `--txid`: Transaction hash (TXID) of the UTXO to spend
- `--vout`: Output index (VOUT) of the UTXO to spend (default: 0)
- `--address`: Address to send the funds to
- `--wit-file`: (Optional) Path to the JSON file containing witness values (for script path spending)
- `--env-file`: (Optional) Path to the .env file containing MNEMONIC variable (default: .env)
- `--account`: (Optional) Account index to derive keys from (default: 0)
- `--dry-run`: (Optional) Perform a dry run without broadcasting the transaction (default: false)

## Environment Variables

The application requires a `.env` file with the following variable:

```
MNEMONIC="your mnemonic phrase here"
```

## Example

1. Generate an address to receive funds:

```bash
cargo run -- address --simf-file examples/p2pkh.simf
```

2. Spend funds using key path:

```bash
cargo run -- spend --simf-file examples/p2pkh.simf --txid abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890 --vout 0 --address bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq
```

3. Spend funds using script path (with witness):

```bash
cargo run -- spend --simf-file examples/p2pkh.simf --wit-file examples/p2pkh.wit --txid abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890 --vout 0 --address bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq
```

## Output

When using the `address` command, the application will output a P2TR address that can be used to receive funds.

When using the `spend` command, the application will output the transaction ID after broadcasting the transaction. If using the `--dry-run` flag, it will output the transaction in hexadecimal format instead.
