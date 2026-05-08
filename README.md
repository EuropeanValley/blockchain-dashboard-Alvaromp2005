[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/N3kLi3ZO)
[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=23734417&assignment_repo_type=AssignmentRepo)
# Blockchain Dashboard Project

CryptoChain Analyzer Dashboard is a Streamlit app for exploring Bitcoin mining data.
It connects to public Bitcoin APIs and organizes the work into the four required modules plus three optional extensions:
Proof of Work monitor, block header analyzer, difficulty history, anomaly detector, Merkle proof verifier, security score and second AI predictor.

## Student Information

| Field | Value |
|---|---|
| Student Name | Alvaro |
| GitHub Username | Alvaromp2005 |
| Project Title | CryptoChain Analyzer Dashboard |
| Chosen AI Approach | Anomaly detector for abnormal block inter-arrival times |

## Module Tracking

Use one of these values: `Not started`, `In progress`, `Done`

| Module | What it should include | Status |
|---|---|---|
| M1 | Proof of Work Monitor | Done |
| M2 | Block Header Analyzer | Done |
| M3 | Difficulty History | Done |
| M4 | AI Component | Done |
| M5 | Merkle Proof Verifier | Done |
| M6 | Security Score | Done |
| M7 | Second AI Approach | Done |

## Current Progress

Write 3 to 5 short lines about what you have already done.

- Built a Streamlit dashboard with four tabs, one for each required module.
- Connected the app to Blockchain.com and Blockstream to fetch latest blocks, raw headers and recent block history.
- Added Proof of Work calculations: compact bits to target, estimated difficulty, hash rate and target threshold.
- Added local double SHA-256 verification of the real 80-byte Bitcoin block header.
- Added an AI-style anomaly detector trained on recent inter-block times with evaluation metrics.
- Added optional modules M5-M7: Merkle proof verification, 51% attack cost/risk estimate and difficulty prediction.
- Added screenshots for every module under the `images/` folder and included the final report in `report/`.

## Next Step

Write the next small step you will do before the next class.

- Review the final dashboard, commit the completed work and push it to the GitHub Classroom repository.

## Main Problem or Blocker

Write here if you are stuck with something.

- No current blocker. The live API needs internet access when the dashboard is used.

## How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL shown by Streamlit, normally `http://localhost:8501`.

The final report is included in `report/final_report.pdf`.

## Screenshots

Screenshots are stored by module:

- M1: `images/m1/`
- M2: `images/m2/`
- M3: `images/m3/`
- M4: `images/m4/`
- M5: `images/m5/`
- M6: `images/m6/`
- M7: `images/M7/`


## Module Summary

### M1 - Proof of Work Monitor

Fetches the latest Bitcoin block and displays:

- block height
- block hash
- nonce
- number of transactions
- block time
- compact bits value
- estimated difficulty
- calculated target
- whether the hash is below the target
- visual leading-zero threshold in the 256-bit SHA-256 space
- distribution of time between recent blocks
- estimated network hash rate

### M2 - Block Header Analyzer

Accepts a Bitcoin block hash, or uses the latest block, and shows the six fields of the 80-byte header:

- version
- previous block hash
- Merkle root
- timestamp
- bits
- nonce

It computes `SHA256(SHA256(header))` locally with Python `hashlib`, compares it with the API hash, counts leading zero bits and checks the proof-of-work target.

### M3 - Difficulty History

Loads completed 2016-block adjustment periods, plots difficulty at each adjustment event and summarizes:

- latest difficulty
- percentage change
- average block time per period
- ratio between actual period duration and the 600-second target

### M4 - AI Component

Uses a statistical anomaly detector. It does not need an external AI API key.

The model:

- trains on recent Bitcoin inter-arrival times
- uses an exponential distribution as the expected mining baseline
- flags intervals in the extreme tails as anomalous
- reports fitted mean, MAE against the 600-second target, anomaly rate and log-likelihood

### M5 - Merkle Proof Verifier

Loads the txids from a selected Bitcoin block and verifies that one transaction belongs to the block:

- builds the Merkle proof branch manually
- duplicates odd nodes according to Bitcoin's tree rule
- recomputes every parent hash with double SHA-256
- compares the final computed root with the Merkle root stored in the block header

### M6 - Security Score

Estimates Bitcoin security from live network data and user assumptions:

- estimated network hash rate
- attacker hash rate required for a selected attacker share
- energy cost per hour
- approximate hardware cost
- double-spend success probability versus confirmation depth using Nakamoto's formula

### M7 - Second AI Approach

Implements a second AI method: a transparent difficulty predictor.

- trains a linear regression model on recent difficulty adjustment periods
- predicts the next difficulty value
- evaluates predictions with walk-forward MAE and MAPE

## Project Structure

```text
template-blockchain-dashboard/
|-- README.md
|-- requirements.txt
|-- .gitignore
|-- app.py
|-- report/
|   `-- final_report.pdf
|-- images/
|   |-- m1/
|   |-- m2/
|   |-- m3/
|   |-- m4/
|   |-- m5/
|   |-- m6/
|   `-- M7/
|-- api/
|   `-- blockchain_client.py
`-- modules/
    |-- m1_pow_monitor.py
    |-- m2_block_header.py
    |-- m3_difficulty_history.py
    |-- m4_ai_component.py
    |-- m5_merkle_proof.py
    |-- m6_security_score.py
    `-- m7_second_ai.py
```
