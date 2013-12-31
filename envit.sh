source venv/bin/activate
# AVOID!!! CLEARDB_DATABASE_URL=mysql://b224c5f58888c8:b33706db@us-cdbr-east-04.cleardb.com/heroku_90761df1db0de24?reconnect=true
# prod CLEARDB_DATABASE_URL=mysql://b224c5f58888c8:b33706db@us-cdbr-east-04.cleardb.com/heroku_90761df1db0de24
# sagi staging CLEARDB_DATABASE_URL=mysql://b8cf289d37bbb7:270d159a@eu-cdbr-west-01.cleardb.com/heroku_4e1f2a316647805d
# local CLEARDB_DATABASE_URL=sqlite:///local.db
CLEARDB_DATABASE_URL=mysql://b224c5f58888c8:b33706db@us-cdbr-east-04.cleardb.com/heroku_90761df1db0de24
export CLEARDB_DATABASE_URL
