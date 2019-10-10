#!/usr/bin/env bash

# Before running this script, activate the conda environment
# where this information will be stored
export CONDA_PREFIX

# Step 1: create new folders in the $CONDA_PREFIX directory
mkdir -p ${CONDA_PREFIX}/etc/conda/activate.d
mkdir -p ${CONDA_PREFIX}/etc/conda/deactivate.d

# Step 2: prompt the user to enter their key and token values
read -p "What is your API key? " key
read -p "What is your API token? " token

# Step 3: store those values to environment variables upon startup
ACTIVATE=${CONDA_PREFIX}/etc/conda/activate.d/env_vars.sh
echo "#!/usr/bin/env bash
" >> ${ACTIVATE}
echo "export KEY='$key'" >> ${ACTIVATE}
echo "export TOKEN='$token'" >> ${ACTIVATE}

# Step 4: unset those values when the env is deactivated
DEACTIVATE=${CONDA_PREFIX}/etc/conda/deactivate.d/env_vars.sh
echo "#!/usr/bin/env bash
" >> ${DEACTIVATE}
echo "unset KEY" >> ${DEACTIVATE}
echo "unset TOKEN" >> ${DEACTIVATE}