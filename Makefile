build:
	cargo run --bin simfony-cli build src/simple_fib.simf

test:
	cargo run --bin simfony-cli run src/simple_fib.simf
