install:
	cargo install --path simfony-cli simfony-cli

build:
	simfony build src/field_ops.simf

test:
	simfony run src/field_ops.simf
