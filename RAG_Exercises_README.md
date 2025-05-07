# 🧑‍💻 RAG Practical Exercises: Chunking, Summarization, and Retrieval Tuning

## Overview

In this set of exercises, you will explore how the way you ingest, chunk, and summarize data affects the performance of a Retrieval-Augmented Generation (RAG) system. You will also learn how retrieval parameters and prompt engineering impact the quality of answers.

---

## 1. **Chunking Strategies**

### **Exercise 1A: One Document per Issue**
- Ingest each Jira issue as a separate document.
- Observe how the RAG system answers project-level questions (e.g., "Who is working in this project?").
- **Questions:**
  - Does the system find all relevant people/components?
  - What happens if the information is spread across many issues?

### **Exercise 1B: All Issues as a Single Document**
- Ingest all issues for a project as a single large document, then chunk it (e.g., by character count or paragraph).
- Observe how the RAG system answers the same questions.
- **Questions:**
  - Is it easier for the system to aggregate information?
  - Are there trade-offs in retrieval accuracy?

---

## 2. **Project Summary Documents**

### **Exercise 2: Aggregated Project Summary**
- After ingesting all issues, programmatically extract all unique assignees, reporters, and components.
- Create a synthetic "project summary" document, e.g.:
  ```
  Project: XYZ
  Components: A, B, C
  People: Alice (reporter), Bob (assignee)
  ```
- Ingest this summary into the vector store with the same `project_id`.
- **Questions:**
  - Does the RAG system now answer project-level questions better?
  - What information is still missing?

---

## 3. **Retrieval Tuning**

### **Exercise 3A: Varying k (Number of Chunks)**
- Change the `k` parameter (number of retrieved chunks) in your retrieval code.
- Try values like 1, 4, 8, 16.
- **Questions:**
  - How does increasing `k` affect the quality of answers?
  - Is there a point of diminishing returns?

### **Exercise 3B: Adjusting Score Threshold**
- Lower the `score_threshold` to allow more diverse chunks to be retrieved.
- **Questions:**
  - Does this help with aggregation questions?
  - Does it introduce more noise?

---

## 4. **Prompt Engineering**

### **Exercise 4: System Prompt for Aggregation**
- Modify your system prompt to include instructions like:
  > "If the answer requires aggregation (e.g., a list of people or components), use all provided context to infer the answer."
- **Questions:**
  - Does this help the LLM provide more complete answers?
  - What are the limitations?

---

## 5. **Data Cleaning**

### **Exercise 5: Clean vs. Noisy Data**
- Compare RAG performance with raw Jira data vs. cleaned/normalized data (e.g., consistent field names, no HTML, etc.).
- **Questions:**
  - How does data quality affect retrieval and answer quality?
  - What cleaning steps are most important?

---

## 6. **Implementation Variants**

- Implement two ingestion scripts:
  - `extract_and_clean_jira_data.py`: Ingests as one document per issue (current approach).
  - `extract_and_clean_jira_data_with_summary.py`: Ingests both per-issue documents and a project summary document, and/or as a single large document for chunking.

---

## 7. **Discussion**

- Which approach works best for project-level vs. issue-level questions?
- How do chunk size, retrieval parameters, and prompt design interact?
- What would you do differently for other types of data (e.g., Confluence pages, test cases)?

---

## **Deliverables**

- Code for both ingestion strategies.
- Example queries and answers for each approach.
- A short write-up on your findings for each exercise.

---

**Tip:**  
Keep your code modular so you can easily switch between ingestion strategies and retrieval settings! 