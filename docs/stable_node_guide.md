# Stable Setup of RL-Swarm Node on WSL (Ubuntu) with RAM Limit & SWAP

Цей гайд допоможе стабільно запустити ноду RL-Swarm локально через WSL2 + Ubuntu 22.04, використовуючи обмеження RAM та додаткову SWAP-пам'ять.

---

## ✅ Середовище

- ОС: Windows 10 / 11
- WSL2 (Windows Subsystem for Linux)
- Ubuntu 22.04 (встановлено з Microsoft Store)
- Обмеження RAM + SWAP
- Інсталяція виключно через офіційні команди

---

## 🧰 Підготовка: RAM та SWAP (налаштування в Windows)

1. Відкрий файл `C:\Users\ТВОЄ_ІМ'Я\.wslconfig` (створи, якщо його немає)
2. Встав наступне:

[wsl2]
memory=6GB
processors=4
swap=16GB
localhostForwarding=true

3. Збережи файл
4. Перезапусти WSL:
```powershell
wsl --shutdown

🐧 Встановлення Ubuntu 22.04 через WSL
- Відкрий Microsoft Store
- Знайди та встанови Ubuntu 22.04 LTS
- Запусти "Ubuntu" з меню Пуск
- Створи користувача та пароль (одноразово)

🚀 Встановлення RL-Swarm (тільки офіційні команди):
cd ~
rm -rf rl-swarm
git clone https://github.com/gensyn-ai/rl-swarm.git
cd rl-swarm
python3 -m venv venv
sudo apt update
sudo apt install -y python3 python3-pip
pip install pycosat
tmux new -s swarm
./run_rl_swarm.sh

🟡 Вихід із tmux не зупиняє ноду:
Ctrl + B, потім D
Повернутись: tmux attach -t swarm

📦 Альтернатива: Створення SWAP вручну в Ubuntu (якщо потрібно)
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
Щоб зробити постійним:
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
Перевірити:
free -h

🧪 Перевірка
Відкрий htop → перевір RAM/SWAP
Впевнись, що порт 3000 відкритий (через tmux)
За потреби — зроби SSH-тунель з Windows (локальний перегляд)

🔍 Підсумки
VPS (Time4VPS) — спостерігались проблеми після декількох годин.
Локальний запуск у WSL із RAM 6 ГБ + SWAP 16 ГБ — стабільна робота >24 годин.
Всі команди відповідають офіційній документації.

🗨️ Зв'язок
Знайшли покращення? Пишіть у Discord або створіть новий Pull Request 🙌
Contributed by: Viktorino 🇺🇦
