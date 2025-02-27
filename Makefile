install:
	cargo install --path simfony-cli simfony-cli

build:
	simfony build src/field.simf
	simfony build src/channel.simf

test:
	simfony run src/field.simf
	simfony run src/channel.simf
