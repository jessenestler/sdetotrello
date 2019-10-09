## Task Managing Feature Classes

Databases&mdash;especially those of the geospatial variety&mdash;can get out of hand quickly. When there is a need to evaluate the schema of (potentially) thousands of layers, the task management associated with keeping track of those schema evaluations can feel like a project unto itself. Cue `sdetotrello`, an Extract-Transform-Load (ETL) pipeline that takes feature classes from an SDE database connection or file geodatabase and loads them as cards into Trello, a popular task management app.

### Installation and Use

#### Assumptions

This package assumes that the user:

- Is familiar with conda environments
- Has a Trello account and can obtain API key and tokens by [logging in and visiting this website](https://trello.com/app-key).

#### Set Up

Clone this repo to your preferred location using Git (or download through the [repo website](https://github.com/jessenestler/sdetotrello)):

```bash
cd your/preferred/project/location
git clone "https://github.com/jessenestler/facilityid"
```
Then, create a conda environment:

```bash
conda create --name sdetotrello_env python=3.7
```

Now, still `cd`'d into your preferred project location, run the bash script to store your API key and token in your conda environment variables. The script will prompt you to copy both the key and token provided to you by Trello in the website linked above. This is a one-time run, the app should work indefinitely after this. 

```bash
bash store_api_secret_in_env.sh
```
