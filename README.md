# WhatsNext

## Install

```python
pip install -e /path/to/this/repo/ --config-settings editable_mode=strict

pip install -e . --config-settings editable_mode=strict

```

## Dev

start postgresql server

```
For compilers to find postgresql@16 you may need to set:
  export LDFLAGS="-L/opt/homebrew/opt/postgresql@16/lib"
  export CPPFLAGS="-I/opt/homebrew/opt/postgresql@16/include"
```

```
brew services start postgresql@16
```

update schemas etc

```
psql postgres
```

```
cat /opt/homebrew/var/log/postgres.log
```

##  TODO

* protected Routes
* Env Variables in Tutorial
* SQL joins
* SQL foreign keys
* Disable SQLA create Engine
* CORS
