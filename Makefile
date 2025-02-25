install:
	cargo install --git https://github.com/BlockstreamResearch/simfony simfony

build:
	simc src/main.simf

test:
	cargo test
