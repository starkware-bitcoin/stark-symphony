install:
	cargo install --path simfony-cli simfony-cli

build:
	mcpp -P src/main.simf -o target/main.out.simf
	simfony build target/main.out.simf --witness target/proof.wit

run:
	simfony run target/main.out.simf --witness target/proof.wit

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
