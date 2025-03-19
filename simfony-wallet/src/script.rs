use std::path::Path;

use anyhow::anyhow;
use elements::secp256k1_zkp as secp256k1;
use elements::{
    taproot::{LeafVersion, TaprootBuilder, TaprootSpendInfo},
    Address, AddressParams, Script,
};
use simfony::{Arguments, CompiledProgram, WitnessValues};

/// Load Simfony program from .simf file and compile it to a Simplicity program
pub fn load_program(path: &Path) -> anyhow::Result<CompiledProgram> {
    let src = std::fs::read_to_string(path)?;
    let compiled = simfony::CompiledProgram::new(src, Arguments::default())
        .map_err(|e| anyhow!("Failed to compile Simfony program: {}", e))?;
    Ok(compiled)
}

/// Create a Bitcoin script from a compiled Simplicity program
pub fn create_script(program: &CompiledProgram) -> anyhow::Result<Script> {
    let script = Script::from(program.commit().cmr().as_ref().to_vec());
    Ok(script)
}

/// Generate a (non-confidential) P2TR address from a Simfony program and a key pair
pub fn create_p2tr_address(
    program: CompiledProgram,
    key_pair: secp256k1::Keypair,
) -> anyhow::Result<Address> {
    let (x_only_public_key, _) = key_pair.x_only_public_key();

    let script = create_script(&program)?;
    let spend_info = taproot_spending_info(script, x_only_public_key)?;

    let address = Address::p2tr(
        secp256k1::SECP256K1,
        spend_info.internal_key(),
        spend_info.merkle_root(),
        None, // TODO: use different blinding pubkey
        &AddressParams::LIQUID_TESTNET,
    );
    Ok(address)
}

/// Taproot leaf version for Simplicity (Simfony) programs
pub fn simplicity_leaf_version() -> LeafVersion {
    LeafVersion::from_u8(0xbe).expect("constant leaf version")
}

/// Parse a .wit file into a WitnessValues struct
pub fn parse_witness(path: &Path) -> anyhow::Result<WitnessValues> {
    let witness_bytes = std::fs::read(path)?;
    let witness = serde_json::from_slice(&witness_bytes)
        .map_err(|e| anyhow!("Failed to parse witness: {}", e))?;
    Ok(witness)
}

/// Create a TaprootSpendInfo struct for a given Simfony program and public key
pub fn taproot_spending_info(
    script: Script,
    public_key: secp256k1::XOnlyPublicKey,
) -> anyhow::Result<TaprootSpendInfo> {
    let builder = TaprootBuilder::new();
    let version = simplicity_leaf_version();

    let builder = builder
        .add_leaf_with_ver(0, script, version)
        .map_err(|e| anyhow!("Failed to add leaf to taproot builder: {}", e))?;

    let spend_info = builder
        .finalize(&secp256k1::SECP256K1, public_key)
        .map_err(|e| anyhow!("Failed to finalize taproot builder: {}", e))?;
    Ok(spend_info)
}
