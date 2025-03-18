use anyhow::{anyhow, Result};
use clap::{Parser, Subcommand};
use elements::{Address, OutPoint, Txid};
use script::create_p2tr_address;
use transaction::{spend_key_path, spend_script_path};

use std::env;
use std::path::PathBuf;
use std::str::FromStr;

mod esplora;
mod keys;
mod script;
mod transaction;

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Show a P2TR address to receive funds and lock them within a STARK vault
    Address {
        /// Path to the simfony program file
        #[arg(long)]
        simf_file: PathBuf,

        /// Path to the .env file containing MNEMONIC
        #[arg(long, default_value = ".env")]
        env_file: PathBuf,

        /// Account index
        #[arg(long, default_value = "0")]
        account: u32,

        /// Show the secret key
        #[arg(long, default_value = "false")]
        show_secret: bool,
    },
    /// Spend the funds locked in a STARK vault
    Spend {
        /// Path to the simfony program file
        #[arg(long)]
        simf_file: PathBuf,

        /// Path to the JSON file containing the witness values (for script path)
        #[arg(long)]
        wit_file: Option<PathBuf>,

        /// Path to the .env file containing MNEMONIC
        #[arg(long, default_value = ".env")]
        env_file: PathBuf,

        /// Account index
        #[arg(long, default_value = "0")]
        account: u32,

        /// Transaction hash (TXID) of the UTXO to spend
        #[arg(long)]
        txid: String,

        /// Output index (VOUT) of the UTXO to spend
        #[arg(long, default_value = "0")]
        vout: u32,

        /// Address to send the funds to
        #[arg(long)]
        address: String,

        /// Dry run
        #[arg(long, default_value = "false")]
        dry_run: bool,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match &cli.command {
        Commands::Address {
            simf_file,
            env_file,
            account,
            show_secret,
        } => {
            dotenv::from_path(env_file).map_err(|_| anyhow!("Failed to load .env file"))?;

            let mnemonic_str =
                env::var("MNEMONIC").map_err(|_| anyhow!("MNEMONIC not found in .env file"))?;
            let keypair = keys::derive_keypair_from_mnemonic(&mnemonic_str, *account)?;

            if *show_secret {
                println!("Secret key: {}", hex::encode(keypair.secret_bytes()));
            }

            let program = script::load_program(simf_file)?;
            let address = create_p2tr_address(program, keypair)?;
            println!("P2TR address: {}", address.to_string());
        }
        Commands::Spend {
            simf_file,
            env_file,
            account,
            txid,
            vout,
            address,
            wit_file,
            dry_run,
        } => {
            dotenv::from_path(env_file).map_err(|_| anyhow!("Failed to load .env file"))?;

            let mnemonic_str =
                env::var("MNEMONIC").map_err(|_| anyhow!("MNEMONIC not found in .env file"))?;
            let key_pair: secp256k1::Keypair =
                keys::derive_keypair_from_mnemonic(&mnemonic_str, *account)?;

            let txid: Txid = Txid::from_str(txid).map_err(|_| anyhow!("Invalid TXID format"))?;
            let outpoint = OutPoint::new(txid, *vout);
            let utxo = esplora::fetch_utxo(outpoint)?;

            let address =
                Address::from_str(address).map_err(|_| anyhow!("Invalid address format"))?;

            let program = script::load_program(simf_file)?;

            // Create and sign transaction using the transaction module
            let tx = match wit_file {
                Some(path) => {
                    let witness_values = script::parse_witness(path)?;
                    spend_script_path(outpoint, utxo, address, key_pair, program, witness_values)?
                }
                None => spend_key_path(outpoint, utxo, address, key_pair, program)?,
            };

            if !dry_run {
                let txid = esplora::broadcast_tx(tx)?;
                println!("Transaction ID: {}", txid);
            } else {
                println!("{:#?}", tx);
                println!(
                    "\nTransaction hex: {}",
                    elements::encode::serialize_hex(&tx)
                );
            }
        }
    }

    Ok(())
}
