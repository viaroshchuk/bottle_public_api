# bottle_public_api
## Deployment
1. Create db
2. Restore db structure from profiles_api.sql. (This works for me: mysql -u *db_user* -p *db_name* < profiles_api.sql)
3. Edit config.py
4. Edit server address in sample_app/app.py (7-9 row)
-----------------------------------------------
gate.py - api server
sample_app/app.py - test application that works with API
graph.py - graphene task

