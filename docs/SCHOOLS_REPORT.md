Relevant commands in schools report to create both schools and injured around schools data (they should run in this order - first schools then injured):

1. Run the following in ANYWAY container:
`python main.py process schools-with-description`

2. Run the following in ANYWAY container with updated start and end dates:

`python main.py process injured-around-schools --start_date 01-06-2015 --end_date 01-06-2025`

3. Later activate jupyter notebook (to run jupyter use `jupyter notebook` command from the main directory).

Run the following notebook to create the result files (both csvs and json files):
Notebook path: `anyway/parsers/schools_2025.ipynb`