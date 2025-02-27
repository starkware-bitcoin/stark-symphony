install:
	cargo install --path simfony-cli simfony-cli

build:
	mcpp -P src/main.simf -o target/main.out.simf
	simfony build target/main.out.simf

test:
	mcpp -P src/tests.simf -o target/tests.out.simf
	simfony run target/tests.out.simf
