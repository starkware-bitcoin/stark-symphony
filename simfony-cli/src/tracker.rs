use itertools::{Either, Itertools};

use simfony::debug::DebugSymbols;
use simfony::jet::{source_type, target_type};
use simfony::str::AliasName;
use simfony::types::AliasedType;
use simfony::value::StructuralValue;
use simfony::{ResolvedType, Value};

use simplicity::bit_machine::ExecTracker;
use simplicity::ffi::ffi::UWORD;
use simplicity::jet::type_name::TypeName;
use simplicity::jet::{Elements, Jet};
use simplicity::{
    BitIter, BitIterCloseError, Cmr, EarlyEndOfStreamError, Value as SimValue, ValueRef,
};

pub struct Tracker<'a> {
    pub debug_symbols: &'a DebugSymbols,
}

#[derive(Debug)]
pub enum TrackerError {
    UnexpectedAlias(AliasName),
    EndOfBitStream,
    UnexpectedEndOfBitStream(BitIterCloseError),
    ReconstructError,
    UnexpectedValue(SimValue),
}

impl From<EarlyEndOfStreamError> for TrackerError {
    fn from(_: EarlyEndOfStreamError) -> Self {
        Self::EndOfBitStream
    }
}

impl From<BitIterCloseError> for TrackerError {
    fn from(error: BitIterCloseError) -> Self {
        Self::UnexpectedEndOfBitStream(error)
    }
}

impl<'a> ExecTracker<Elements> for Tracker<'a> {
    fn track_left(&mut self, _: simplicity::Ihr) {}

    fn track_right(&mut self, _: simplicity::Ihr) {}

    fn track_jet_call(
        &mut self,
        jet: &Elements,
        input_buffer: &[UWORD],
        output_buffer: &[UWORD],
        _: bool,
    ) {
        let args = parse_args(jet, input_buffer).expect("parse args");
        let result = parse_result(jet, output_buffer).expect("parse res");
        println!(
            "{:?}({}) = {}",
            jet,
            args.iter().map(ToString::to_string).join(", "),
            result
        );
    }

    fn track_dbg_call(&mut self, cmr: &Cmr, value: simplicity::Value) {
        if let Some(tracked_call) = self.debug_symbols.get(cmr) {
            match tracked_call.map_value(
                &StructuralValue::from(value),
            ) {
                Some(Either::Right(debug_value)) => {
                    println!(
                        "\x1b[1;33mDBG: {} = {}\x1b[0m",
                        debug_value.text(),
                        debug_value.value()
                    );
                }
                _ => {}
            }
        }
    }
}

/// Coverts an array of words into a bit iterator.
/// Bits are reversed.
fn words_into_bit_iter(words: &[UWORD]) -> BitIter<std::vec::IntoIter<u8>> {
    let bytes_per_word = std::mem::size_of::<UWORD>();
    let mut bytes = Vec::with_capacity(words.len() * bytes_per_word);
    for word in words.iter().rev() {
        for i in 0..bytes_per_word {
            let byte: u8 = ((word >> ((bytes_per_word - i - 1) * 8)) & 0xFF) as u8;
            bytes.push(byte);
        }
    }
    BitIter::from(bytes.into_iter())
}

/// Converts an aliased type to a resolved type.
fn resolve_type(aliased_type: &AliasedType) -> Result<ResolvedType, TrackerError> {
    let get_alias = |_: &AliasName| -> Option<ResolvedType> { None };
    aliased_type
        .resolve(get_alias)
        .map_err(TrackerError::UnexpectedAlias)
}

/// Traverses a product and collects the arguments.
fn collect_args(
    node: ValueRef,
    num_args: usize,
    args: &mut Vec<SimValue>,
) -> Result<(), TrackerError> {
    assert!(num_args > 0);
    if num_args == 1 {
        args.push(node.to_value());
        Ok(())
    } else {
        if let Some((left, right)) = node.as_product() {
            args.push(left.to_value());
            collect_args(right, num_args - 1, args)
        } else {
            Err(TrackerError::UnexpectedValue(node.to_value()))
        }
    }
}

/// Parses a SimValue from an array of words.
fn parse_sim_value(words: &[UWORD], type_name: TypeName) -> Result<SimValue, TrackerError> {
    let sim_type = type_name.to_final();
    let mut bit_iter = words_into_bit_iter(words);
    let sim_value = SimValue::from_padded_bits(&mut bit_iter, &sim_type)?;
    // TODO(m-kus): this call fails
    //bit_iter.close()?;
    Ok(sim_value)
}

/// Parses a Simfony value from a Simplicity value.
fn parse_simf_value(
    sim_value: SimValue,
    aliased_type: &AliasedType,
) -> Result<Value, TrackerError> {
    let resolved_type = resolve_type(aliased_type)?;
    let value = Value::reconstruct(&sim_value.into(), &resolved_type)
        .ok_or(TrackerError::ReconstructError)?;
    Ok(value)
}

/// Parses the arguments of a jet call.
fn parse_args(jet: &Elements, words: &[UWORD]) -> Result<Vec<Value>, TrackerError> {
    let simf_types = source_type(*jet);
    if simf_types.len() == 0 {
        return Ok(vec![]);
    }

    let sim_value = parse_sim_value(words, jet.source_ty())?;

    let mut args = Vec::with_capacity(simf_types.len());
    collect_args(sim_value.as_ref(), simf_types.len(), &mut args)?;

    args.into_iter()
        .zip(simf_types.iter())
        .map(|(arg, ty)| parse_simf_value(arg, ty))
        .collect()
}

/// Parses the result of a jet call.
fn parse_result(jet: &Elements, words: &[UWORD]) -> Result<Value, TrackerError> {
    let simf_type = target_type(*jet);
    let sim_value = parse_sim_value(words, jet.target_ty())?;
    parse_simf_value(sim_value, &simf_type)
}
