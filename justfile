import 'infra/justfile'

[group('test')]
[doc('''Run integration tests. --no-infra: NO infra start & set up | --no-clean: NO infra cleanup.''')]
test *FLAGS:
    #!/bin/bash
    set -e
    
    NO_INFRA=false
    NO_CLEAN=false

    echo "Parsing flags: {{FLAGS}}"
    if [[ "{{FLAGS}}" == *"--no-infra"* ]]; then
        NO_INFRA=true
        echo "Infra setup will be skipped (remove --no-infra to enable)."
    fi
    if [[ "{{FLAGS}}" == *"--no-clean"* ]]; then
        NO_CLEAN=true
        echo "Infra cleanup will be skipped (remove --no-clean to enable)."
    fi

    if [ "$NO_INFRA" = false ]; then
        echo "Starting & setting up infra..." && \
            just clean start build-plugin setup  && \
            echo "Done starting & setting up infra."
    fi

    echo "Retrieving DSS connection info..."
    # Retrieve api key from .env.dss file generated during setup.
    DKU_DSS_URL="http://localhost:10000"
    DKU_API_KEY=$(grep '^DKU_API_KEY=' ./infra/.env.dss | awk -F= '{print $2}')

    echo "Creating and activating virtual environment..."
    cd ./tests

    # Setting up virtual environment
    if [ ! -d "./venv" ]; then
        python3 -m venv ./venv
    fi
    source ./venv/bin/activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt

    # Preparing tests output folder
    OUTPUT_FOLDER=./tests-results/{{DSS_VERSION}}
    if [ -d "$OUTPUT_FOLDER" ]; then
        rm -rf "$OUTPUT_FOLDER"
    fi
    mkdir -p "$OUTPUT_FOLDER"

    echo "Starting tests run..."

    DKU_DSS_URL=$DKU_DSS_URL DKU_API_KEY=$DKU_API_KEY DSS_USERNAME=reader DSS_PASSWORD=reader TMPDIR=/tmp/ \
        LIMITED_CONTAINER_NAME=dss MEM_LIMITER=percentage MEM_LIMITER_PERCENTAGE_THRESHOLD=80 \
        behavex --output-folder="$OUTPUT_FOLDER" --show-progress-bar --stop \
        | sed $'s/^/\033[1;34m/;s/$/\033[0m/'

    echo "Finished testing, check outputs at $(pwd)/$OUTPUT_FOLDER."

    if [ "$NO_CLEAN" = false ]; then
        cd ../.. && just clean
    fi