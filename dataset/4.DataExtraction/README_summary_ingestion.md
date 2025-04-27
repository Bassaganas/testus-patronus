# Comparing Jira Ingestion Strategies: Per-Issue vs. Project Summary

## Overview

This directory contains two scripts for ingesting and cleaning Jira data:

- **`extract_and_clean_jira_data.py`**: Ingests each Jira issue as a separate document (per-issue ingestion).
- **`extract_and_clean_jira_data_with_summary.py`**: Ingests each Jira issue as a separate document **and** generates a synthetic project summary document (per-issue + summary ingestion).

These scripts are designed to help you explore how different ingestion strategies affect the performance of Retrieval-Augmented Generation (RAG) systems.

---

## Scripts

### 1. `extract_and_clean_jira_data.py`
- **What it does:**
  - Cleans and saves each Jira issue as a separate document.
  - No project-level summary is created.
- **Use case:**
  - Baseline for RAG systems that only use granular, issue-level context.

### 2. `extract_and_clean_jira_data_with_summary.py`
- **What it does:**
  - Cleans and saves each Jira issue as a separate document (same as above).
  - Additionally, generates a synthetic project summary document for each project, containing:
    - A summary (concatenated summaries/descriptions of all issues)
    - A list of unique contributors (assignees and reporters)
    - A list of unique components
  - Saves the summary as a separate JSON file.
- **Use case:**
  - Enhanced RAG systems that benefit from project-level aggregation and context.

---

## How to Use

1. **Run the baseline script:**
   ```bash
   python extract_and_clean_jira_data.py
   ```
   - This will output per-issue cleaned JSON files.

2. **Run the summary script:**
   ```bash
   python extract_and_clean_jira_data_with_summary.py
   ```
   - This will output per-issue cleaned JSON files **and** a project summary JSON file for each project.

3. **Ingest the outputs into your RAG/vector store pipeline.**

4. **Compare RAG answers to project-level questions** (e.g., "Who is working in this project?" , "What are the main components of this project?") between the two approaches.

---

## Learning Objectives

- Understand the impact of chunking and document granularity on retrieval and answer quality.
- See how project-level aggregation (contributors, components, summaries) can improve RAG answers to high-level questions.
- Experiment with retrieval parameters (k, score threshold) and prompt engineering to further improve results.
- Appreciate the importance of data cleaning and structuring for downstream AI applications.

---

## Discussion

- Which approach works best for project-level vs. issue-level questions?
- How does the presence of a summary document affect retrieval and answer quality?
- What are the trade-offs between fine-grained and aggregated context?

---

**Tip:** Try modifying the summary generation logic (e.g., use an LLM for summarization) and see how it affects your RAG system! 