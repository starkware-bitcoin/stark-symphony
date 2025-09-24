SIMF_FILE=../target/main.out.simf
WIT_FILE=../target/proof.wit

test:
	bash ../scripts/unit_tests.sh --debug

proof-simf:
	python3 scripts/generate_simf.py tests/data/proof.json > ../target/proof.simf

proof-wit:
	python3 scripts/generate_wit.py tests/data/proof.json > $(WIT_FILE)

build:
	mcpp -P -I src src/main.simf -o $(SIMF_FILE)
	simfony build $(SIMF_FILE) --witness $(WIT_FILE)

run:
	simfony run $(SIMF_FILE) --witness $(WIT_FILE)
