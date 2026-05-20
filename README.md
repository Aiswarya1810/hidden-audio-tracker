Hidden Audio Tracker 🔐

A Django-based cybersecurity web application that securely hides encrypted audio files inside images using steganography techniques.

Users can:
- Create accounts and log in
- Send hidden audio messages
- Encrypt audio using passwords
- Extract and unlock audio securely
- Use inbox and outbox messaging

---

## 🚀 Features

- Audio encryption using Fernet
- Image steganography (LSB)
- Secure messaging system
- Inbox and Outbox
- Password-protected extraction
- User authentication
- Profile management

---

## 🛠️ Technologies Used

### Backend
Python
Django

### Frontend
HTML
CSS
JavaScript

### Libraries
Pillow (Image processing)
Cryptography (Fernet encryption)

### Database
SQLite3

## ⚙️ Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd hidden_audio_tracker
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Environment

#### Mac/Linux
```bash
source venv/bin/activate
```

#### Windows
```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install django pillow cryptography
```

### 5. Run Server

```bash
python manage.py migrate
python manage.py runserver
```

---

## 🌐 Open Application

```bash
http://127.0.0.1:8000
```

---

## 🔐 How It Works

1. Sender uploads image and audio  
2. Audio is encrypted using a password  
3. Encrypted audio is hidden inside image  
4. Receiver opens message  
5. Receiver enters password to unlock audio  

---

## 👨‍💻 Author

Aiswarya  
