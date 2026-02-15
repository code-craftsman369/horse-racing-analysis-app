# 🐎 Horse Racing Analysis - Precision Web Dashboard

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

*Transforming raw track data into actionable racing insights through smart automation*

</div>

---

## 🌟 Overview

Horse Racing Analysis is a professional-grade web application designed to solve one of the most complex challenges in racing: **analyzing the correlation between track conditions and performance.**

By automating the collection of moisture and cushion values directly from JRA sites, this tool provides a high-precision, visual environment for data-driven decision making.

---

## ✨ Features

### 📡 **Automated Data Pipeline**

1 - **JRA/Netkeiba Integration**
Automated daily data extraction using Selenium with built-in retry logic for high reliability.

2 - **Live Track Conditions**
Instantly fetches current moisture levels and cushion values directly from official JRA sources.

3 - **One-Click Batch Processing**
Processes all 12 races of the day simultaneously via a simple `settings.txt` configuration.

### 📊 **Advanced Interactive Dashboard**

1 - **Dynamic Visualization**
High-precision (300dpi) correlation charts mapping historical results against current track status.

2 - **Multi-Race Tab View**
[cite_start]Switch between 1R to 12R instantly within a single browser-based interface[cite: 5].

3 - **Deep Horse Analysis**
Search and filter individual horses to visualize their specific track-surface adaptability.

### 🛠️ **Engineer-Friendly Architecture**

1 - **No-Code Operation**
Uses `.bat` files for one-click installation and execution, designed for non-technical users.

2 - **Modular Logic**
Clean separation between the scraping engine (`main_analysis.py`) and the Web UI (`app.py`).

---

## 🛠️ Tech Stack

| Technology | Purpose |
|-----------|---------|
| **Python 3.8+** | Core data processing & logic |
| **Streamlit** | [cite_start]Interactive web dashboard & UI [cite: 5] |
| **Pandas / NumPy** | Large-scale data normalization & correlation |
| **Selenium** | Automated web scraping & data extraction |
| **Matplotlib** | High-fidelity scientific data visualization |

---

## 🎯 Vision & Story

### Why I Built This

As a freelance engineer aiming for the top tier of the global market, I developed this project to demonstrate:

1 - **Data Integrity**
My commitment to providing 100% accurate and reliable automated solutions for complex business needs.

2 - **User Experience**
The ability to transform "messy" raw data into a beautiful, intuitive interface that anyone can use.

3 - **Professional Discipline**
Maintaining the highest standards of code quality and documentation, a hallmark of my 10+ years of professional experience in Japan.

### My Journey

1 - **Goal**: Become a world-class engineer specializing in Blockchain, NFT, and Web3.

2 - **Mission**: Creating products that empower children and bring joy to families through technology.

3 - **Target**: Full-time independent freelancer by 2026.

---

## 🚀 How to Use

### 1 - Installation

1 - Double-click `install.bat` to automatically set up the required Python environment and libraries.

### 2 - Configuration

1 - Open `settings.txt` and set the venue, date, and preferred moisture/cushion modes (auto/manual).

### 3 - Execution

1 - Run `run_analysis.bat` to collect and analyze data.

2 - Run `run_app.bat` to launch your interactive dashboard in your browser.

---

## 🌈 Future Enhancements

- [ ] Real-time odds integration via API.
- [ ] AI-driven performance prediction modeling.
- [ ] Support for international racing venues.
- [ ] Exportable PDF summary reports.

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file.

---

## 👤 Author

**Tatsu S.**

GitHub: [@code-craftsman369](https://github.com/code-craftsman369)  
Official Listing: [Coconala Service Page](https://coconala.com/services/4076648)

---

## 💡 Inspiration

This tool is a testament to the power of **automated intelligence**. It is designed for those who value time and demand precision in their analysis. My goal is to continue building tools that turn "impossible data tasks" into "one-click solutions".