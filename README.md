# PPFLOW — Dataset Understanding & Diagnostics Engine

## Overview

**PPFLOW** is a modular data analysis and preprocessing system designed to automatically:

* Detect dataset type (tabular, image, etc.)
* Infer dataset structure and format
* Profile dataset characteristics
* Diagnose data quality issues
* Suggest and apply fixes interactively or automatically

The goal is to provide a **plug-and-play pipeline** that helps users quickly understand and clean their datasets before using them in machine learning workflows.

---

## Features Implemented

### 1. Dataset Detection (`scan_data`)

Automatically identifies:

* **Container type**

  * Tabular (CSV, JSON, etc.)
  * Image datasets

* **Structural form**

  * Tabular:

    * Long / Wide / Nested
  * Image:

    * Flat
    * Hierarchical (class folders)
    * With splits (`train/val/test`)

---

### 2. Tabular Dataset Profiling

Extracts:

* Statistical properties:

  * Skewness
  * Kurtosis

* Data quality indicators:

  * Type mismatches
  * Encoding detection

* Time-series detection (robust parsing + monotonicity)

---

### 3. Image Dataset Profiling

Supports:

* Class-based datasets
* Split-based datasets (`train/test/val`)

Extracts:

* Class distribution
* Image resolutions
* Color modes (RGB, grayscale, etc.)
* Corrupt image detection

Includes both:

* **Per-split profiling**
* **Global aggregation**

---

### 4. Diagnostics System

A modular issue detection system for both tabular and image data.

---

## Tabular Diagnostics

Detects:

* Duplicate rows
* Missing values
* Mixed data types
* Constant columns
* Skewed distributions
* NLP/text columns
* Outliers (Z-score based)
* Non-normalized numeric data

Each issue includes:

* Description
* Severity level
* Suggested fix
* Automatic fix implementation

---

## Image Diagnostics

Detects:

* Corrupt images
* Duplicate images
* Mixed image resolutions
* Mixed color modes
* Class imbalance

Handles:

* Flat datasets
* Class folders
* `train/test/val` structures

---

### 5. Fixing System

Two modes:

#### Interactive Mode

```bash
ppflow diagnose --fix
```

* Prompts user for each fix (`y/n`)
* Applies fixes step-by-step

#### Automatic Mode

```bash
ppflow diagnose --fixall
```

* Applies all fixes without prompting

#### Diagnostics Only

```bash
ppflow diagnose
```

* Displays issues only
* No modifications

---

## Project Structure (Simplified)

```
ppflow/
│
├── cli/
│   └── main.py                # CLI entry point
│
├── datahandling/
│   ├── tabular.py            # Tabular detection & profiling
│   ├── image.py              # Image detection & profiling
│   ├── diagnostics/
│   │   ├── runner.py         # Main diagnostics pipeline
│   │   ├── tabular.py        # Tabular issues & fixes
│   │   └── images.py         # Image issues & fixes
│   └── models.py             # DatasetIdentity abstraction
```

---

## How to Use

### 1. Place Your Dataset

Put your dataset inside:

```
data/
```

Supported:

* CSV files
* Image folders

---

### 2. Run Scan (optional if integrated)

The system internally scans the dataset using:

```python
dataset = scan_data()
```

---

### 3. Run Diagnostics

#### Only analyze

```bash
ppflow diagnose
```

#### Interactive fixing

```bash
ppflow diagnose --fix
```

#### Automatic fixing

```bash
ppflow diagnose --fixall
```

---

### 4. Review Output

* Issues are displayed in a structured, colored format
* Fixed dataset appears in:

```
data_fixed/
```

---

## Design Principles

* **Modular**: Each detector is independent and extensible
* **Non-destructive**: Original data is never modified
* **Extensible**: New dataset types and diagnostics can be added easily
* **User-controlled**: Interactive fixes allow human-in-the-loop decisions

