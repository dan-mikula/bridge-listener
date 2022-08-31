# Bridge Listener
Listens on events published by <a href="https://github.com/duckster/bridge-contracts">Bridge Contracts</a>.<br />
Disclaimer: Do not use in production.

### Installation
cd into project directory, create virtual environement, activate it and run:
```
pip install -r requirments.txt
```

### Usage
Rename `.envexample` to `.env` and set up your private keys and keys for infura/alchemy (or whatever provider you use).<br /><br />
Rename `config-example.yaml` to `config.yaml` and add the addresses of your tokens and bridge contracts on the respective networks.<br /><br />
Run the listener with:
```
python src/listener/
```

### Todo
- Tests
- Refactor code
- Add gas strategies
- Add transaction validator
- Add multitoken functionality