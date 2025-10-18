# 🇺🇦 README.uk.md — Український переклад офіційного README

> Це переклад офіційного файлу `README.md` репозиторію [`gensyn-ai/rl-swarm`](https://github.com/gensyn-ai/rl-swarm), призначений для україномовної спільноти. Оригінальний текст англійською мовою див. у корені репозиторію.

---

## 🧠 RL-Swarm

RL-Swarm — це проєкт від Gensyn для розподіленого тренування моделей підкріплювального навчання (Reinforcement Learning) у відкритому, децентралізованому середовищі. Він надає можливість запуску та участі у глобальному кластері RL, підключаючи вузли з різних систем.

---

## ⚙️ Встановлення та запуск

Найпростіший спосіб почати — запустити ноду локально або на VPS:

```bash
cd ~
rm -rf rl-swarm
git clone https://github.com/gensyn-ai/rl-swarm.git
cd rl-swarm
python3 -m venv venv
source venv/bin/activate
sudo apt update
sudo apt install -y python3 python3-pip
pip install pycosat
tmux new -s swarm
./run_rl_swarm.sh
```

---

## 🖥️ Вимоги до системи

* **Python 3.10+**
* **Ubuntu 22.04+ або WSL2** (Windows Subsystem for Linux)
* **Рекомендовано:** мінімум 16 ГБ RAM або комбінація 8 ГБ RAM + 16 ГБ SWAP

---

## 🐝 Як це працює

RL-Swarm дозволяє розподіленим машинам тренувати агентів RL у спільному середовищі, за допомогою механізмів спільного навчання (peer-to-peer RL).

* Вузол запускається локально
* Підключається до централізованого координаційного вузла
* Приймає завдання, виконує епізоди RL та повертає результати

---

## 🧾 Документація

* Основна документація англійською: `docs/`
* Гайд з налаштування WSL та SWAP: [docs/stable\_node\_guide.md](./docs/stable_node_guide.md)

---

## 🤝 Участь та внесок

* Форкніть репозиторій
* Створіть нову гілку
* Додайте свої зміни
* Створіть Pull Request з поясненням змін

У разі запитань звертайтеся до каналу Discord: [https://discord.gg/gensyn](https://discord.gg/gensyn)

---

## 🧠 Про Gensyn

> Gensyn створює децентралізований протокол для масштабованого навчання ML (Machine Learning), де апаратні ресурси та алгоритми поєднуються в єдину екосистему.

Офіційний сайт: [https://www.gensyn.ai/](https://www.gensyn.ai/)
