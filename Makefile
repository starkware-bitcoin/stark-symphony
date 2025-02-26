install:
	cargo install --path simfony-cli simfony-cli

build:
	simfony build src/simple_fib.simf

test:
	simfony run src/simple_fib.simf
