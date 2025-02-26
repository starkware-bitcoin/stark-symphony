# STARK verifier in Simfony language

## Simfony CLI

Install the CLI tool:

```bash
cargo install --git https://github.com/m-kus/simfony-stark-verifier simfony-cli
```

## Build and run

```bash
simfony-cli build src/simple_fib.simf --witness src/simple_fib.wit --output-path src/simple_fib.bin
simfony-cli run src/simple_fib.simf --witness src/simple_fib.wit --param src/simple_fib.param
```

