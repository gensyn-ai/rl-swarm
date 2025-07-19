# scripts

## setup_gensyn.sh

Однорядковий інсталер, який:

1. Оновлює систему та ставить `python3.10`, `git`, `screen`.  
2. Клонує репозиторій **gensyn-ai/rl-swarm** у `~/rl-swarm`.  
3. Створює Python-venv, встановлює залежності, патчить `protobuf==3.20.3`.  
4. Запускає воркер у фоні (`screen -dmS gensyn ./run_rl_swarm.sh`).

```bash
curl -sSL https://raw.githubusercontent.com/VasilenkoViktor/rl-swarm/main/scripts/setup_gensyn.sh | bash
```

> ⚠️ Скрипт призначений для Ubuntu 22.04 / Debian 12 і тестований у WSL 2 та на VPS (Contabo, DigitalOcean).  
> > Файл `swarm.pem` після запуску зберігається у `~/.gensyn/` — не забудьте зробити резервну копію, якщо плануєте переносити вузол.
