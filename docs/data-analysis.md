# Data Analysis Guide

## 📊 Overview

This guide covers the dataset used in the DoH Exfiltration Detection Platform, including traffic analysis, and pattern detection. It provides insights into how data is collected, analyzed, and utilized for machine learning model training and validation.

## 🔍 Data Collection and Sources

### Dataset Information

The platform utilizes the **CIRA-CIC-DoHBrw-2020** dataset for machine learning training and validation:

**Dataset Details:**
- **Source**: https://www.unb.ca/cic/datasets/dohbrw-2020.html
- **Full Name**: CIRA-CIC-DoHBrw-2020 Dataset
- **Description**: Comprehensive dataset containing benign and malicious DoH traffic flows
- **Format**: CSV files with network flow features
- **Usage**: Training ML models for DoH traffic classification
- **Location**: Place CSV files in the `datasets/` directory

**Dataset Features:**
- Network flow statistics (duration, bytes sent/received)
- Packet-level features (length statistics, timing patterns)
- Protocol-specific features for DoH traffic analysis
- Labeled data for supervised learning (benign/malicious)

## 📈 Flow Analysis with DoHLyzer

DoHLyzer is the core traffic analysis engine that captures and analyzes network flows:

The version of DoHLyzer used in this platform is a fork of the original DoHLyzer, that has been modified for this project. It is used to gather flow data similar to the ones used in the CIRA-CIC-DoHBrw-2020 dataset, enabling detailed analysis of DoH traffic patterns on the same models used for training.

This comprehensive data analysis framework provides deep insights into DoH exfiltration attempts, enabling both real-time detection and thorough forensic analysis of security incidents.
