# STARK verifier in Simfony language

## Simfony CLI

Install the CLI tool:

```bash
cargo install --git https://github.com/m-kus/simfony-stark-verifier simfony-cli
```

## Build and run

```bash
simfony build src/simple_fib.simf --witness src/simple_fib.wit --output-path src/simple_fib.bin
simfony run src/simple_fib.simf --witness src/simple_fib.wit --param src/simple_fib.param
```

