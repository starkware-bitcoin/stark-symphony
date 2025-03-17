use elements::secp256k1_zkp as secp256k1;
use elements::taproot::{TapTweakHash, TaprootSpendInfo};

/// Sign a P2TR/key path transaction
pub fn sign_transaction_p2tr(
    sighash_all: &[u8],
    key_pair: secp256k1::Keypair,
    spend_info: TaprootSpendInfo,
) -> anyhow::Result<secp256k1::schnorr::Signature> {
    let secp = secp256k1::Secp256k1::new();

    let tweak =
        TapTweakHash::from_key_and_tweak(spend_info.internal_key(), spend_info.merkle_root());
    let msg = secp256k1::Message::from_digest_slice(sighash_all)
        .map_err(|e| anyhow::anyhow!("Failed to create message: {}", e))?;
    let tweaked_key_pair = key_pair
        .add_xonly_tweak(&secp, &tweak.to_scalar())
        .map_err(|e| anyhow::anyhow!("Failed to tweak key pair: {}", e))?;

    Ok(secp.sign_schnorr(&msg, &tweaked_key_pair))
}

/// Derive a keypair from a mnemonic
pub fn derive_keypair_from_mnemonic(mnemonic_str: &str) -> anyhow::Result<secp256k1::Keypair> {
    use anyhow::anyhow;
    use bip39::Mnemonic;
    use elements::bitcoin::bip32::{DerivationPath, ExtendedPrivKey};
    use elements::bitcoin::secp256k1::Secp256k1;
    use std::str::FromStr;

    // Parse mnemonic
    let mnemonic =
        Mnemonic::parse_normalized(mnemonic_str).map_err(|e| anyhow!("Invalid mnemonic: {}", e))?;

    // Generate seed from mnemonic
    let seed = mnemonic.to_seed("");

    // Derive master key
    let secp = Secp256k1::new();
    let master_key = ExtendedPrivKey::new_master(elements::bitcoin::Network::Bitcoin, &seed)
        .map_err(|e| anyhow!("Failed to derive master key: {}", e))?;

    // Derive child key (using m/84'/0'/0'/0/0 for example)
    let path = DerivationPath::from_str("m/84'/0'/0'/0/0")
        .map_err(|e| anyhow!("Invalid derivation path: {}", e))?;
    let child_key = master_key
        .derive_priv(&secp, &path)
        .map_err(|e| anyhow!("Failed to derive child key: {}", e))?;

    // Convert to secp256k1 keypair
    let secret_key_bytes = child_key.private_key.secret_bytes();
    let keypair = secp256k1::Keypair::from_seckey_slice(secp256k1::SECP256K1, &secret_key_bytes)
        .map_err(|e| anyhow!("Failed to create keypair: {}", e))?;

    Ok(keypair)
}
