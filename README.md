# bottle_public_api
## Deployment
1. Create db
2. Restore db structure from profiles_api.sql. (This works for me: mysql -u root -p api_dep < profiles_api.sql)
2. Edit config.py
3. Edit server address in sample_app/app.py (7-9 row)
-----------------------------------------------

