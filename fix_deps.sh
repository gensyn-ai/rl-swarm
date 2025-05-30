#!/bin/bash
pip uninstall -y trl transformers protobuf hivemind vllm unsloth unsloth_zoo
pip install protobuf==3.20.3
pip install transformers==4.31.0
pip install trl==0.7.4
pip install hivemind@git+https://github.com/learning-at-home/hivemind@1.11.11
pip install vllm==0.7.3
