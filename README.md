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

## DB Model TODO

1. Join, foreign key,
2. tags for job
3. Task table, register task with project, task field for job.
3. Job Status to seperate table: status_id, string, running_on.
4. Depends on seperate table?

## Next steps

1. define a consistent datamodel in and out (eg. task_name etc)
2. be consitent with checks and return cose
3.
