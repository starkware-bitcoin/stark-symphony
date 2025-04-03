SIMF_FILE=target/main.out.simf
WIT_FILE=target/proof.wit

install:
	cargo install --path simfony-cli simfony-cli

build:
	mcpp -P -I src src/main.simf -o $(SIMF_FILE)
	simfony build $(SIMF_FILE) --witness $(WIT_FILE)

run:
	simfony run $(SIMF_FILE) --witness $(WIT_FILE)

test:
	bash scripts/unit_tests.sh

vsix:
	cd simfony-vsix && vsce package

proof:
	cd scripts && python -m fibsquare
	python ./scripts/generate_simf.py target/proof.json > target/proof.simf
	python ./scripts/generate_wit.py target/proof.json > target/proof.wit

test-prover:
	cd scripts && PYTHONPATH=. pytest -s fibsquare

address-0:
	cargo run --bin simfony-wallet address --simf-file $(SIMF_FILE) --account 0

address-1:
	cargo run --bin simfony-wallet address --simf-file $(SIMF_FILE) --account 1

spend-keypath:
	cargo run --bin simfony-wallet spend \
		--simf-file $(SIMF_FILE) \
		--account 0 \
		--address tex1ps2y3ut204geww4fklgnh07xe2pu3wqjrns9gsxra9pjflpjlkfysfsn389 \
		--txid af506fb383f4e70c9ccf56a59779792fed19601e8fd175af5d49fa3d14bf7645

spend-scriptpath:
	cargo run --bin simfony-wallet spend \
		--simf-file $(SIMF_FILE) \
		--account 0 \
		--address tex1ps2y3ut204geww4fklgnh07xe2pu3wqjrns9gsxra9pjflpjlkfysfsn389 \
		--txid af506fb383f4e70c9ccf56a59779792fed19601e8fd175af5d49fa3d14bf7645 \
		--vout 0 \
		--wit-file $(WIT_FILE)
