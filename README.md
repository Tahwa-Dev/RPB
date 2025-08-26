# 🚀 Telegram Bot Setup Guide (Ubuntu + Python3 + aiogram)

This guide helps you install and run your Telegram bot on an Ubuntu server.  
Each command block is **independent** (you can copy them one by one).

---

## 🔹 Step 1 — Update the server

```sh
sudo apt update && sudo apt upgrade -y
 ```
## 🔹 Step 2 — Install Python and required tools

```sh
sudo apt install python3 -y
```
```sh
sudo apt install python3-venv -y
```
```sh
sudo apt install python3-pip -y
```
## 🔹 Step 3 — Create and activate Virtual Environment

```sh
python3 -m venv venv
```
```sh
source venv/bin/activate
```

## 🔹 Step 4 — Upgrade pip and install libraries

```sh
pip install --upgrade pip
```

```sh
pip install aiogram==2.25.1
```

## 🔹 Step 5 — Install File Py Bot 

```sh
git@github.com:Tahwa-Dev/RPB.git
```
## 🔹 Step 6 — change API TOKEN BOT

```sh
chmod +x update_token.sh
```
## 🔹 Step 7 — RUN/START BOT 

```sh
python3 bot.py
```



