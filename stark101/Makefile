SIMF_FILE=target/main.out.simf
WIT_FILE=target/proof.wit

build:
	mcpp -P -I src src/main.simf -o $(SIMF_FILE)
	simfony build $(SIMF_FILE) --witness $(WIT_FILE)

run:
	simfony run $(SIMF_FILE) --witness $(WIT_FILE)

test:
	bash ../scripts/unit_tests.sh

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
		--env-file ../.env \
		--account 0 \
		--address tex1pp8lydxfev5w2fxury77z25r222v4llm78xgr3cdh4f5c26sypfeqnytzje \
		--txid 40765d6cc77396989f8f8a4ba59e61558a8ea440b9c6dbb6197d09784af35909

spend-scriptpath:
	cargo run --bin simfony-wallet spend \
		--simf-file $(SIMF_FILE) \
		--env-file ../.env \
		--account 0 \
		--address tex1pp8lydxfev5w2fxury77z25r222v4llm78xgr3cdh4f5c26sypfeqnytzje \
		--txid 40765d6cc77396989f8f8a4ba59e61558a8ea440b9c6dbb6197d09784af35909 \
		--vout 1 \
		--wit-file $(WIT_FILE)
