#!/bin/bash

# Step 1: create a conda env if not already created

# Step 2: activate the conda directory

# Step 3: create new folders in the $CONDA_PREFIX directory

#mkdir -p $CONDA_PREFIX/etc/conda/activate.d
#mkdir -p $CONDA_PREFIX/etc/conda/deactivate.d
#touch $CONDA_PREFIX/etc/conda/activate.d/env_vars.sh
#touch $CONDA_PREFIX/etc/conda/deactivate.d/env_vars.sh

# Step 4: prompt the user to enter their key and token values

# Step 5: store those values to environment variables upon startup

read -p "What is your API key?" key
read -p "What is your API token?" token

echo "#!/bin/bash
" >> /Users/jessenestler/Projects/sdetotrello/test.sh
echo "export KEY='$key'" >> /Users/jessenestler/Projects/sdetotrello/test.sh
echo "export TOKEN='$token'" >> /Users/jessenestler/Projects/sdetotrello/test.sh

# Step 6: unset those values when the env is deactivated

echo "#!/bin/bash
" >> /Users/jessenestler/Projects/sdetotrello/test.sh
echo "unset KEY" >> /Users/jessenestler/Projects/sdetotrello/test.sh
echo "unset TOKEN" >> /Users/jessenestler/Projects/sdetotrello/test.sh