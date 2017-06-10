## Introduction

This document describes the contents of the file [lms.zip](https://drive.google.com/file/d/0B4yX8HDe1VaTdWdPMXV5c2gycW8/view?usp=sharing), which is used in the ANYWAY project in the [Public Knowledge Workshop](http://www.hasadna.org.il). The file was acquired from the Israeli Central Bureau of Statistics (הלשכה המרכזית לסטטיסטיקה, למ”ס), for the purposes of the ANYWAY project.
It contains information about traffic accidents from 2005-2014, including location, time, vehicles and individuals involved, and more.
See the data on a map on http://oway.org.il/

## Directory structure
The zipped archive contains two directories, `Accidents Type 1` and `Accidents Type 3`, each containing files of a different format. The subdirectories under these directories each correspond to one year (the first four digits in the directory name). Inside each subdirectory there are various files, each with the subdirectory name as a prefix. Here are the description of the files (listed without the prefix):

* **AccAverages.{pdf,xls}**: averages of all numeric columns in `AccData.csv`, for data validation.
* **AccCodebook.{pdf,xls}**: description of each column in `AccData.csv`, and its possible values.
* **AccData.{csv,sas7bdat}**: actual data about accidents. Use the `.csv` file.
* **DicStreets.{csv,sas7bdat}**: mapping from street ID to street name, including city code.
* **Dictionary.{csv,sas7bdat}**: textual description for all categorical values in `AccData.csv`, `InvData.csv` and `VehData.csv`.
* **IntersectNonUrban.{csv,sas7bdat}**: name of every non-urban intersection, the numbers of the intersecting roads, and the kilometer on the first road (counting from its start). Each intersection appears twice, once with each road first.
* **IntersectUrban.{csv,sas7bdat}**: for every urban intersection, the city it is in and the codes of the intersecting streets.
* **Introduction.pdf**: definitions and background about the various values.
* **InvAverages.{pdf,xls}**: averages of all numeric columns in `InvData.csv`, for data validation.
* **InvCodebook.{pdf,xls}**: description of each column in `InvData.csv`, and its possible values.
* **InvData.{csv,sas7bdat}**: data about individuals involved in accidents. Linked to `AccData.csv` by the `pk_teuna_fikt` column, and to `VehData.csv` by the `mispar_rehev_fikt` column. Use the `.csv` file.
* **Methodology.pdf**: information about the data collection and reliability.
* **ReadMe.pdf**: general information about the data, including a description of the legacy PUF system originally developed to process the data, and a listing of the data files similar to this one.
* **VehAverages.{pdf,xls}**: averages of all numeric columns in `VehData.csv`, for data validation.
* **VehCodebook.{pdf,xls}**: description of each column in `VehData.csv`, and its possible values.
* **VehData.{csv,sas7bdat}**: data about vehicles involved in accidents. Linked to `AccData.csv` by the `pk_teuna_fikt` column, and to `InvData.csv` by the `mispar_rehev_fikt` column. Use the `.csv` file.

Note: in Type 1 directories from 2007 and older, the data files are tab-separated `.txt` files rather than `.csv` files, and the name after the prefix starts with a small letter rather than a capital letter.

## Reading the files
The files should be read with Hebrew encoding (`cp1255`).
You can see an example [here](../process.py).

## Known issues
Some accidents (from 2005) don’t have x and y coordinates.

