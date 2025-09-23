install:
	cargo install --path simfony-cli simfony-cli

test:
	cd stark101 && $(MAKE) test
	cd stwo-verifier && $(MAKE) test
