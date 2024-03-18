# Installation

```bash
conda create -n cs40 python=3.10 -y
conda activate cs40
pip install -r requirements.txt
```

# To Deploy
```bash
cdk bootstrap
cdk synth
cdk deploy cs40-dns-stack
cdk deploy --all
```