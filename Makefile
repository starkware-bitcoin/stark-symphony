install:
	cargo install --path simfony-cli simfony-cli

vsix:
	cd simfony-vsix && vsce package

test:
	cd stark101 && $(MAKE) test
	cd stwo-verifier && $(MAKE) test
