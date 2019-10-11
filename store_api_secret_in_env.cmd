@ECHO OFF
SET /p env_name="What would you like to call your environment? "
ECHO Attempting to create a clone from the default ArcGIS Pro conda distribution
SET /p env_name="What would you like to call your environment? "

conda create --clone arcgispro-py3 --name %env_name% 2>&1 |find "CondaEnvironmentNotFoundError" && (
    ECHO Attempting to create a completely new environment
    conda create --name %env_name%
) || (
  echo successfully created %env_name%
)

REM Step 1: Activate the conda environment
activate %env_name%
SET %CONDA_PREFIX%

REM Step 2: Create new folders in to %CONDA_PREFIX% directory
mkdir %CONDA_PREFIX%\etc\conda\activate.d
mkdir %CONDA_PREFIX%\etc\conda\deactivate.d

REM Step 3: Prompt the user to enter their key and token values
SETLOCAL
SET /p key="What is your API key? "
SET /p token="What is your API key? "
ENDLOCAL

REM Step 4: Store those values to environment variables upon startup
SET activate=%CONDA_PREFIX%/etc/conda/activate.d/env_vars.cmd

REM Step 5: Unset those values when the env is deactivated
SET deactivate=%CONDA_PREFIX%/etc/conda/deactivate.d/env_vars.cmd