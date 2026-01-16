# ROBDD Builder
A Python-based tool for building, analyzing, and visualizing **Reduced Ordered Binary Decision Diagrams (ROBDDs)** from Boolean formulas. This project provides a complete pipeline for parsing Boolean expressions, constructing optimal binary decision diagrams, and generating visual representations.

---

## Features

**Boolean Formula Parsing**
- Supports standard Boolean operators: AND (`&`), OR (`|`), NOT (`!`), XOR (`^`), Implication (`->`), Bi-implication (`<->`)
- Uses a Pratt parser for correct operator precedence and associativity
- Converts formulas to PySMT expressions for robust handling

**ROBDD Construction**
- Implements Shannon expansion recursively
- Applies reduction and isomorphism rules automatically
- Supports custom variable ordering (alphabetical by default)

**Visual Output**
- Generates high-quality PNG visualizations
- Color-coded nodes: Red edges for 0-branches, Blue edges for 1-branches
- Terminal nodes clearly marked (0 = False, 1 = True)
- Automatic fallback to online GraphvizOnline if local Graphviz is unavailable

**CLI Interface**
- Command-line arguments for formulas, output filenames, and variable ordering
- Detailed console output for debugging and verification

---

## Project Structure

```
BDD/
├── BDD.py                    # Main ROBDD engine and visualization
├── parser.py                 # Boolean formula parser (Pratt parser)
├── requirements.txt          # Python package dependencies
├── README.md                 # This file
└── robdd_output/             # Output directory for generated visualizations
```


## Installation

### Prerequisites

- **Python 3.7+** installed on your system
- **pip** (Python package installer)
- *(Optional but recommended)* **Graphviz** for local PNG rendering

### Step 1: Clone or Download the Project

```bash
cd path/to/BDD
```

### Step 2: Install Python Dependencies

Install the required packages using pip:

```bash
pip install -r requirements.txt
```

This installs:
- **pysmt**: Symbolic math library for Boolean logic manipulation
- **graphviz**: Python interface to Graphviz for diagram rendering

### Step 3: (Optional) Install Graphviz System Package

For local PNG rendering, install Graphviz:

**On Windows:**
```bash
# Using Chocolatey
choco install graphviz

# Or download from https://graphviz.org/download/
```

**On macOS:**
```bash
brew install graphviz
```

**On Linux (Ubuntu/Debian):**
```bash
sudo apt-get install graphviz
```

If Graphviz is not installed, the tool will automatically open the diagram in **GraphvizOnline** (web-based) instead.

---

## Usage

### Basic Usage

Run the tool from the command line:

```bash
python BDD.py "<formula>"
```

### Command-Line Arguments

```
usage: BDD.py [-h] [-o OUTPUT] [--ordering ORDERING] formula

positional arguments:
  formula                  Boolean formula string (e.g., '(a & !c) | (b ^ d)')

optional arguments:
  -h, --help              Show help message and exit
  -o, --output OUTPUT     Output filename without extension (default: 'robdd_output')
  --ordering ORDERING     Comma-separated variable ordering (default: alphabetical)
```

### Operator Reference

| Operator | Symbol | Example | Meaning |
|----------|--------|---------|---------|
| AND | `&` | `a & b` | Both a and b are true |
| OR | `\|` | `a \| b` | Either a or b (or both) is true |
| NOT | `!` | `!a` | a is false |
| XOR | `^` | `a ^ b` | Either a or b is true (but not both) |
| Implication | `->` | `a -> b` | If a then b |
| Bi-implication | `<->` | `a <-> b` | a and b have the same truth value |


#### Example 

```bash
python BDD.py "(a & !c) | (b ^ d)" --ordering "a,b,c,d"
```

**Output:**
```
Formula String: (a & !c) | (b ^ d)
Parsed PySMT: Or(And(a, Not(c)), Xor(b, d))
Variable Ordering (user-defined): ['a', 'b', 'c', 'd']
ROBDD Root ID: 12
ROBDD Image saved locally to: robdd_output.png
```
---

#### Visualization

The `save_image()` function generates a graph visualization:

**Graph Representation:**
- **Nodes**: Circles labeled with variable names (except terminals)
- **Terminals**: Boxes (0 = red, 1 = green)
- **Edges**: 
  - Dashed red line = 0-branch (variable = false)
  - Solid blue line = 1-branch (variable = true)

---
