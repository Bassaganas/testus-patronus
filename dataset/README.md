## Summary of Artefacts

Jira is an issue tracking system that supports software companies (among other types of companies) with managing their projects, community, and processes. This dataset is a collection of public Jira repositories downloaded from the internet using the Jira API V2. We collected data from 16 pubic Jira repositories containing 1822 projects and 2.7 million issues. Included in this data are historical records of 32 million changes, 9 million comments, and 1 million issue links that connect the issues in complex ways. This artefact repository contains the data as a MongoDB dump, the scripts used to download the data, the scripts used to interpret the data, and qualitative work conducted to make the data more approachable.

## Author Information

Lloyd Montgomery - lloyd.montgomery@uni-hamburg.de
Clara Lüders - clara.marie.lueders@uni-hamburg.de
Prof. Dr. Walid Maalej - walid.maalej@uni-hamburg.de

All authors are affiliated with the University of Hamburg in Hamburg, Germany.

## Description of Artefacts

The artefact is split into four different folders.

0. **DataDefinition**: This folder houses the definition of data such as the repos themselves, and additional meta information downloaded using the provided scripts.
   - May2021: A folder containing the same downloaded data found below, but in May2021 instead of Jan2022. We upload this previous meta-information because two Jiras, MariaDB and Mindville, are no longer available online and therefore the most up-to-date meta-information included outside this folder does not contain those sources.
   - jira_data_sources.json: The list of public Jira repos with URLs and additional information.
   - jira_field_information.json: Information about the fields describing each issue, organised by Jira repo.
   -  jira_issuetype_information.json: Information about the types of issues, as described by each Jira.
   - jira_issue_linktype_mapping.json: Results of manual qualitative labelling conducted by the authors to support use of this data from the perspective of link types.
   - jira_issuetype_thematic_analysis.json: Results of a Thematic Analysis process conducted by the authors to support use of this data from the perspective of issue types.
1. **DataDownload**
   - README.md: Instructions how to run DownloadData.ipynb.
   - requirements-manual.txt: List of Python packages required.
   - DownloadData.ipynb: Script to download various types of data and meta-data.
2. **OverviewAnalysis**
   - README.md: Instructions how to run OverviewAnalysis.ipynb.
   - requirements-manual.txt: List of Python packages required.
   - OverviewAnalysis.ipynb: Script to analyse the data at a high level.
3. **DataDump**
   - README.md: Instructions how to import and export the MongoDB data.
   - mongodump-JiraRepos.archive: MongoDB archive file, compressed. Expanded, this data is ~60GB inside MongoDB.


## System Requirements

- MongoDB must be installed in order to import and use the dataset.
- The Python scripts require Python, and a number of Python packages. For each folder listed above, a different README and requirements-manual file are included. Follow those instructions to get the code running on your machine.

## Installation Instructions

Installation instructions are included in each sub-folder.

## Licenses

The code is licensed under MIT. The license is included in this repository and further information can be found here:https://opensource.org/licenses/MIT

The data is licensed under CC BY 4.0. The license is included in this repository and further information can be found here: https://creativecommons.org/licenses/by/4.0/

## Additional

Command used to ZIP the folder: `zip -r ThePublicJiraDataset.zip ./ThePublicJiraDataset -x ".*" -x "__MACOSX"`