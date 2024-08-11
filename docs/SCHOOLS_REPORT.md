Relevant commands in schools report to create both schools and injured around schools data (they should run in this order - first schools then injured):

1. Run the following in ANYWAY container:
`python main.py process schools-with-description-2020`

2. Run the following in ANYWAY container with updated start and end dates:

`python main.py process injured-around-schools-2023 --start_date 01-06-2014 --end_date 01-06-2024`

3. Later activate jupyter notebook (to run jupyter use `jupyter notebook` command from the main directory).

Run the following notebook to create the result files (both csvs and json files):
Notebook path: `anyway/parsers/schools_2024.ipynb`

4. Add the 3 jsons to git:
- static/data/schools/injured_around_schools_api.json
- static/data/schools/injured_around_schools_months_graphs_data_api.json
- static/data/schools/injured_around_schools_sex_graphs_data_api.json