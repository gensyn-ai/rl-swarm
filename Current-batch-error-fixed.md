If you're facing 'current_batch' error, follow the commands below:

Step-1:
```bash
pkill -f "SCREEN.*gensyn"
```
Step-2:
```bash
screen -S gensyn
```
Step-3:
```bash
cd rl-swarm
```
Step-4:
```bash
curl -o hivemind_exp/configs/mac/grpo-qwen-2.5-0.5b-deepseek-r1.yaml https://raw.githubusercontent.com/karandedhaa/rl-swarm/main/hivemind_exp/configs/mac/grpo-qwen-2.5-0.5b-deepseek-r1.yaml
```
Step-5:
```bash
rm -rf .venv
python3 -m venv .venv && . .venv/bin/activate && ./run_rl_swarm.sh
```
