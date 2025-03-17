use anyhow::{anyhow, Result};
use clap::{Parser, Subcommand};
use elements::Txid;
use simfony::CompiledProgram;
use std::env;
use std::fs;
use std::path::PathBuf;
use std::str::FromStr;
use std::sync::Arc;

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
    /// Lock funds with a simfony program
    Lock {
        /// Path to the simfony program file
        #[arg(short, long)]
        simf_file: PathBuf,

        /// Path to the .env file containing MNEMONIC
        #[arg(short, long, default_value = ".env")]
        env_file: PathBuf,

        /// Transaction hash (TXID) of the UTXO to spend
        #[arg(short, long)]
        txid: String,

        /// Output index (VOUT) of the UTXO to spend
        #[arg(short, long)]
        vout: u32,
    },
    /// Unlock a UTXO locked with a simfony program
    Unlock {
        /// Path to the simfony program file
        #[arg(short, long)]
        simf_file: PathBuf,

        /// Path to the .env file containing MNEMONIC
        #[arg(short, long, default_value = ".env")]
        env_file: PathBuf,

        /// Transaction hash (TXID) of the UTXO to spend
        #[arg(short, long)]
        txid: String,

        /// Output index (VOUT) of the UTXO to spend
        #[arg(short, long)]
        vout: u32,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match &cli.command {
        Commands::Lock {
            simf_file,
            env_file,
            txid,
            vout,
        } => {
            lock_transaction(simf_file, env_file, txid, *vout)?;
        }
        Commands::Unlock {
            simf_file,
            env_file,
            txid,
            vout,
        } => {
            unlock_transaction(simf_file, env_file, txid, *vout)?;
        }
    }

    Ok(())
}

/// Lock funds with a simfony program
fn lock_transaction(
    simf_path: &PathBuf,
    env_path: &PathBuf,
    txid_str: &str,
    vout: u32,
) -> Result<()> {
    // Load environment variables from .env file
    dotenv::from_path(env_path)?;

    // Get mnemonic from environment
    let mnemonic_str =
        env::var("MNEMONIC").map_err(|_| anyhow!("MNEMONIC not found in .env file"))?;

    // Derive keypair from mnemonic
    let keypair = keys::derive_keypair_from_mnemonic(&mnemonic_str)?;

    // Read and compile the simfony program
    let simf_content = fs::read_to_string(simf_path)?;
    let compiled = CompiledProgram::new(
        Arc::from(simf_content.as_str()),
        simfony::Arguments::default(),
    )
    .map_err(|e| anyhow!("Failed to compile simfony program: {}", e))?;

    // Parse txid
    let txid =
        Txid::from_str(txid_str).map_err(|_| anyhow!("Invalid TXID format: {}", txid_str))?;

    // Create and sign transaction using the transaction module
    let tx = transaction::lock(txid, vout, compiled, keypair)?;

    // Print the transaction as hex
    println!("{}", hex::encode(elements::encode::serialize(&tx)));

    Ok(())
}

/// Unlock a UTXO locked with a simfony program
fn unlock_transaction(
    simf_path: &PathBuf,
    env_path: &PathBuf,
    txid_str: &str,
    vout: u32,
) -> Result<()> {
    // Load environment variables from .env file
    dotenv::from_path(env_path)?;

    // Get mnemonic from environment
    let mnemonic_str =
        env::var("MNEMONIC").map_err(|_| anyhow!("MNEMONIC not found in .env file"))?;

    // Derive keypair from mnemonic
    let keypair = keys::derive_keypair_from_mnemonic(&mnemonic_str)?;
    let (x_only_public_key, _) = keypair.x_only_public_key();

    // Read and compile the simfony program
    let simf_content = fs::read_to_string(simf_path)?;
    let compiled = CompiledProgram::new(
        Arc::from(simf_content.as_str()),
        simfony::Arguments::default(),
    )
    .map_err(|e| anyhow!("Failed to compile simfony program: {}", e))?;

    // Parse txid
    let txid = Txid::from_str(txid_str).map_err(|_| anyhow!("Invalid TXID format"))?;

    // Create and sign transaction using the transaction module
    let tx = transaction::unlock(txid, vout, compiled, x_only_public_key)?;

    // Print the transaction as hex
    println!("{}", hex::encode(elements::encode::serialize(&tx)));

    Ok(())
}
