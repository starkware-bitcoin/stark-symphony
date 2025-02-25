use simfony::{dummy_env, simplicity::BitMachine, Arguments, CompiledProgram};

#[allow(unused)]
const PROGRAM: &str = include_str!("../../src/main.simf");

#[allow(unused)]
fn run_program() -> String {
    let compiled = CompiledProgram::new(PROGRAM, Arguments::default()).expect("Failed to compile program");
    let satisfied = compiled.satisfy(Default::default()).expect("Failed to satisfy program");
    let mut machine = BitMachine::for_program(satisfied.redeem());
    let env = dummy_env::dummy();
    let res = machine.exec(satisfied.redeem(), &env).expect("Failed to execute program");
    res.to_string()
}

#[test]
fn test_program() {
    let _ = run_program();
}
