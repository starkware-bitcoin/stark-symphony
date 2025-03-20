# STARK verifier in Simfony language

This is an exploration project with a goal to implement a simple STARK verifier in Simfony language.   
[Simfony](https://github.com/BlockstreamResearch/simfony) is a Rust-like language that compiles to [Simplicity](https://github.com/BlockstreamResearch/simplicity) assembly. The stack is developed by Blockstream, and it is currently deployed in the [Liquid](https://liquidtestnet.com/) sidechain testnet.

One of the key concepts of Simplicity is **Jets**:
- The core language is very concise (nine GADT operators)
- You can implement pretty complex programs using just the core, but it would take kilobytes of code and minutes of execution
- However you can replace common sub-programs with "Jets" — formally proven equivalent implementations in C
- This opens a clear path for introducing new exciting features without softforks, with a follow-up optimization route

STARKs are perfect candidate for this approach!

## Roadmap

- [x] Fibonacci square over toy field PoC
- [ ] Liquid testnet deployment
- [ ] M31 field and its extensions
- [ ] Merkle VCS verifier
- [ ] Polynomial over QM31
- [ ] Circle FRI
- [ ] Single component Stwo verifier

## Dev quickstart

0. Clone this repo
1. Install `simfony` CLI tool with `make install`
2. Run tests with `make test`
3. Generate proof with `make proof`
4. Build STARK verifier program with `make build`
5. Run the program using the generated witness with `make run`

## Simfony CLI

This is a small CLI tool that helps with the development of Simfony programs.

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

## Simfony VSIX

VSCode extension providing syntax highlighting and autocompletion for the Simfony programming language.

Read the [instructions](./simfony-vsix/README.md).
