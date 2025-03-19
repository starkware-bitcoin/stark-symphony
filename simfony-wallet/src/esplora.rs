use elements::{encode, OutPoint, Transaction, TxOut};

/// Fetch UTXO given the txid and vout
pub fn fetch_utxo(outpoint: OutPoint) -> anyhow::Result<TxOut> {
    let url = format!(
        "https://blockstream.info/liquidtestnet/api/tx/{}/hex",
        outpoint.txid.to_string()
    );
    let tx_hex = reqwest::blocking::get(&url)?.text()?;
    extract_utxo(&tx_hex, outpoint.vout as usize)
}

/// Broadcast a transaction to the network
/// Returns the txid of the broadcasted transaction
#[allow(dead_code)]
pub fn broadcast_tx(tx: Transaction) -> anyhow::Result<String> {
    let client = reqwest::blocking::Client::new();
    let txid = client
        .post("https://blockstream.info/liquidtestnet/api/tx")
        .body(encode::serialize_hex(&tx))
        .send()?
        .text()?;
    Ok(txid)
}

/// Extract UTXO from a raw transaction given its index
fn extract_utxo(tx_hex: &str, vout: usize) -> anyhow::Result<TxOut> {
    let tx_bytes = hex::decode(tx_hex.trim())?;
    let transaction: Transaction = encode::deserialize(&tx_bytes)?;
    if vout >= transaction.output.len() {
        return Err(anyhow::anyhow!("Invalid vout index: {}", vout));
    }
    Ok(transaction.output[vout].clone())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_confidential_utxo() {
        let tx_hex = include_str!(
            "../tests/data/7916e3f48a07db0ffa0b680c9ff8188c70cea47ccba9b2e6bb7f89cd9bd057ee.hex"
        );
        let txout = extract_utxo(tx_hex, 0).expect("Failed to extract UTXO");

        let blinding_key = secp256k1::SecretKey::from_slice(
            hex::decode("0973e78f7334ef19907b7071bb5168fa086f08419e58c95906e994ec0392a1f1")
                .unwrap()
                .as_slice(),
        )
        .expect("Failed to parse blinding key");

        let secp = secp256k1::Secp256k1::new();
        let secrets = txout
            .unblind(&secp, blinding_key)
            .expect("Failed to unblind");
        assert_eq!(secrets.value, 50000);
    }
}
