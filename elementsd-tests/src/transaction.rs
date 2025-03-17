use elements::secp256k1_zkp as secp256k1;
use elements::{
    confidential::{Asset, Nonce, Value},
    hashes::Hash,
    pset::PartiallySignedTransaction,
    sighash::{Prevouts, SighashCache},
    taproot::TapLeafHash,
    Address, AssetId, AssetIssuance, BlockHash, LockTime, OutPoint, SchnorrSighashType, Script,
    Sequence, Transaction, TxIn, TxInWitness, TxOut, TxOutWitness, Txid,
};
use simfony::{CompiledProgram, WitnessValues};

use crate::keys::sign_transaction_p2tr;
use crate::script::{
    create_p2tr_address, create_script, create_taproot_key_path, create_taproot_script_path,
    simplicity_leaf_version,
};

/// Spend a P2TR/key path output
/// Lock a UTXO with a Simplicity script
pub fn lock(
    utxo_txid: Txid,
    utxo_vout: u32,
    utxo: TxOut,
    program: CompiledProgram,
    key_pair: secp256k1::Keypair,
) -> anyhow::Result<Transaction> {
    let (x_only_public_key, _) = key_pair.x_only_public_key();

    let script = create_script(&program)?;
    let lock_spend_info = create_taproot_script_path(script, x_only_public_key)?;

    let address = create_p2tr_address(&lock_spend_info)?;
    let value = utxo.value.explicit().unwrap();
    let fee = 10000;
    let tx = build_transaction(utxo_txid, utxo_vout, address, value - fee, fee);

    let mut sighash_cache = SighashCache::new(&tx);
    let sighash_all = sighash_cache
        .taproot_key_spend_signature_hash(
            0,
            &Prevouts::All(&[utxo]),
            SchnorrSighashType::All,
            liquid_testnet_genesis_hash(),
        )
        .map_err(|e| anyhow::anyhow!("Failed to compute sighash: {}", e))?;

    let utxo_spend_info = create_taproot_key_path(x_only_public_key)?;
    let signature = sign_transaction_p2tr(&sighash_all.to_byte_array(), key_pair, utxo_spend_info)?;

    let final_script_witness = vec![signature.serialize().to_vec()];

    Ok(finalize_transaction(tx, final_script_witness))
}

/// Spend a P2TR/script path output
pub fn unlock(
    utxo_txid: Txid,
    utxo_vout: u32,
    utxo: TxOut,
    program: CompiledProgram,
    witness_values: WitnessValues,
    key_pair: secp256k1::Keypair,
) -> anyhow::Result<Transaction> {
    let (x_only_public_key, _) = key_pair.x_only_public_key();

    let lock_spend_info = create_taproot_key_path(x_only_public_key)?;
    let address = create_p2tr_address(&lock_spend_info)?;
    let value = utxo.value.explicit().unwrap();
    let fee = 10000;
    let tx = build_transaction(utxo_txid, utxo_vout, address, value - fee, fee);

    let script = create_script(&program)?;
    let utxo_spend_info = create_taproot_script_path(script.clone(), x_only_public_key)?;
    let control_block = utxo_spend_info
        .control_block(&(script.clone(), simplicity_leaf_version()))
        .unwrap();

    let mut sighash_cache = SighashCache::new(&tx);
    let sighash_all = sighash_cache
        .taproot_script_spend_signature_hash(
            0,
            &Prevouts::All(&[utxo]),
            TapLeafHash::from_script(&script, simplicity_leaf_version()),
            SchnorrSighashType::All,
            liquid_testnet_genesis_hash(),
        )
        .map_err(|e| anyhow::anyhow!("Failed to compute sighash: {}", e))?;
    let signature = sign_transaction_p2tr(&sighash_all.to_byte_array(), key_pair, utxo_spend_info)?;

    let satisfied_program = program
        .satisfy(witness_values)
        .map_err(|e| anyhow::anyhow!("Failed to satisfy program: {}", e))?;
    let (program_bytes, witness_bytes) = satisfied_program.redeem().encode_to_vec();

    let final_script_witness = vec![
        signature.serialize().to_vec(),
        witness_bytes,
        program_bytes,
        script.into_bytes(),
        control_block.serialize(),
    ];

    Ok(finalize_transaction(tx, final_script_witness))
}

fn build_transaction(
    utxo_txid: Txid,
    utxo_vout: u32,
    address: Address,
    value: u64,
    fee: u64,
) -> Transaction {
    Transaction {
        version: 2,
        lock_time: LockTime::ZERO.into(),
        input: vec![TxIn {
            previous_output: OutPoint {
                txid: utxo_txid,
                vout: utxo_vout,
            },
            is_pegin: false,
            script_sig: Script::new(),
            sequence: Sequence::ZERO,
            asset_issuance: AssetIssuance::null(),
            witness: TxInWitness::empty(),
        }],
        output: vec![
            TxOut {
                value: Value::Explicit(value),
                script_pubkey: address.script_pubkey(),
                asset: Asset::Explicit(tlbtc_asset_id()),
                nonce: Nonce::Null,
                witness: TxOutWitness::default(),
            },
            TxOut::new_fee(fee, tlbtc_asset_id()),
        ],
    }
}

fn finalize_transaction(tx: Transaction, final_script_witness: Vec<Vec<u8>>) -> Transaction {
    let mut partial_tx = PartiallySignedTransaction::from_tx(tx);
    partial_tx.inputs_mut()[0].final_script_witness = Some(final_script_witness);
    partial_tx.extract_tx().unwrap()
}

pub fn tlbtc_asset_id() -> AssetId {
    AssetId::from_slice(&[0; 32]).unwrap()
}

pub fn liquid_testnet_genesis_hash() -> BlockHash {
    BlockHash::all_zeros()
}
