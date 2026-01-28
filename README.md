# 🛡️ A Context-Aware Self-Healing Security Framework for WBAN Against Sybil Attacks

---

## 🌐 Overview

Wireless Body Area Networks (WBANs) are a vital component of the **Internet of Medical Things (IoMT)**, enabling continuous patient monitoring using wearable and implanted medical sensors. These networks handle **life-critical and sensitive medical data** while operating under strict constraints such as low power, limited computation, and open wireless communication channels.

Due to these limitations, WBANs are highly vulnerable to security threats that can directly impact patient safety and the reliability of medical decisions.

---

## ⚠️ Problem Statement

One of the most critical security threats in WBAN environments is the **Sybil Attack**, where a single malicious node creates multiple fake identities.

🔴 This can result in:
- Injection of false medical data  
- Network disruption and routing manipulation  
- Secondary attacks such as DoS  
- Compromised patient safety  

Most existing security solutions are **too heavy**, **energy-intensive**, or **not adaptive** enough for resource-constrained WBAN systems.

---

## 🎯 Project Objectives

This project aims to design a **lightweight, adaptive, and autonomous security framework** that can:

- 🔍 Accurately detect Sybil attacks  
- ⚡ Operate efficiently in low-power WBAN environments  
- 🔁 Recover automatically without manual intervention  
- 🩺 Preserve the integrity and reliability of medical data  

---

## 🧠 Proposed Solution

We propose a **Context-Aware Self-Healing Security Framework** tailored for IoMT-based WBANs.

🔐 **Core Idea:**  
Combine **cryptographic identity verification** with **context-aware machine learning** techniques to detect Sybil attacks while minimizing false positives, energy consumption, and network latency.

---

## 🏗️ System Architecture

The framework follows a **three-layer architecture**:

### 🩺 WBAN Layer
- Wearable and implanted medical sensors  
- Secure identity tokens  
- Lightweight cryptographic mechanisms  

### 🌫️ Fog Layer
- Network behavior monitoring  
- Context-aware ML-based Sybil detection  
- Cryptographic verification  
- Self-healing decision engine  

### ☁️ Cloud Layer
- Secure data storage  
- Audit logs and long-term analysis  
- Heavy ML model training  

---

## 🔄 Self-Healing Mechanism

Once a Sybil node is detected, the system **autonomously recovers** by:

- 🚫 Isolating suspicious nodes  
- 🔑 Revoking compromised security keys  
- 📉 Dynamically adjusting detection thresholds  
- 🛑 Activating fail-safe modes when necessary  

This ensures uninterrupted operation and maintains trust in medical data.

---

## 🚀 Expected Outcomes

✔️ Lightweight Sybil attack detection for WBAN  
✔️ Reduced false positives using contextual awareness  
✔️ Autonomous recovery with minimal energy overhead  
✔️ Improved patient safety and data trustworthiness  
✔️ A simulated Sybil attack dataset for WBAN research  

---

## 💡 Why This Project Matters

Modern healthcare systems demand **high reliability, security, and resilience**.  
This project addresses a critical research gap by delivering a **practical, adaptive, and deployable security solution** for next-generation smart healthcare environments.

---

## 👨‍💻 Project Information

**Final Year Research Project**  
Department of Engineering  
University of Peradeniya  

**Research Area:**  
IoMT · WBAN · Cyber Security · Machine Learning · Self-Healing Systems

---

## 📜 License

This project is developed for academic and research purposes.

---
