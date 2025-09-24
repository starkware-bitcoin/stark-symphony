# STARK verifier in SimplicityHL

This is an exploration project with a goal to implement a simple STARK verifier in SimplicityHL language.   
[SimplicityHL](https://github.com/BlockstreamResearch/simfony) is a Rust-like language that compiles to [Simplicity](https://github.com/BlockstreamResearch/simplicity) assembly. The stack is developed by Blockstream, and it is currently deployed in the [Liquid](https://liquidtestnet.com/) sidechain testnet.

One of the key concepts of Simplicity is **Jets**:
- The core language is very concise (nine GADT operators)
- You can implement pretty complex programs using just the core, but it would take kilobytes of code and minutes of execution
- However you can replace common sub-programs with "Jets" — formally proven equivalent implementations in C
- This opens a clear path for introducing new exciting features without softforks, with a follow-up optimization route

STARKs are perfect candidate for this approach!

## Dev quickstart

0. Clone this repo
1. Install `simfony` CLI tool with `make install`
2. Run tests with `make test`

### STARK 101
1. Go to stark101 folder
2. Generate proof with `make proof`
3. Build STARK verifier program with `make build`
4. Run the program using the generated witness with `make run`

### Stwo verifier
1. Go to stwo-verifier folder
2. Run tests with `make test`
3. Generate witness with `make proof-wit`
4. Build the program using `make build`

## Simfony CLI

This is a small CLI tool that helps with the development of SimplicityHL programs.

Install `simfony` binary:

```bash
cargo install --git https://github.com/keep-starknet-strange/stark-symphony simfony-cli
```

Build a Simfony program:

```bash
simfony build src/simple_fib.simf --witness src/simple_fib.wit --output-path src/simple_fib.bin
```

Run a Simfony program:

```bash
simfony run src/simple_fib.simf --witness src/simple_fib.wit --param src/simple_fib.param
```
