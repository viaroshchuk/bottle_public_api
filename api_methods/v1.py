from bottle import request, response
from mysql_query import exec_sql
import hashlib
import datetime
import urllib.request
import imghdr
import os
import json
""" 
    v1 API Methods:
        v1_register(): takes login, password, name and creates new user in db.
        v1_auth(): takes login and password. Generates api_key, write it into db and returns it to caller.
                    api_key is used as mandatory param for all next methods.
        v1_change_profile_name(): takes api_key and new_name. Profile_name in db changes to new_name.
        v1_get_profile_data(): takes api_key and profile_id(optional). This methods allows you to fetch data 
                            about any user by id, if id is not mentioned, it returns data from your profile.
        v1_upload_profile_image(): takes api_key and file_url. Downloads image from url on server, save it's path 
                                    in db. Also deletes old image from server.
        [PLANNED]v1_logout(): deletes api_key.
                            
"""
# TODO: placeholders in sql queries
# TODO: sql injection security


# http://config.server_host:config.server_port/v1/register?login=..&password=..&name=..
# TODO: name validation
def v1_register():
    """ Add new user into profiles table
    3 GET params (all srt):
        login
        password => password (sha256 in db)
        name
    Returns:
        200 = login
        400 = Missing params/Login taken
        500 = ???
    """
    if 'login' not in request.query or 'password' not in request.query or 'name' not in request.query:
        response.status = 400
        return json.dumps({'status': '400', 'error': 'Missing GET params, 3 needed (login, password, name).'})
    # TODO: params validation
    login = request.query.login

    select_query = "SELECT id FROM profiles WHERE login='{}'".format(login)

    if exec_sql(select_query)[0] == 0:  # In case such login not found
        # password in db is sha256 hash
        pass_sha256 = hashlib.sha256(request.query.password.encode()).hexdigest()
        insert_query = "INSERT INTO profiles (login, password, profile_name) VALUES ('{0}', '{1}', '{2}')".\
            format(login, pass_sha256, request.query.name)
        if exec_sql(insert_query)[0] == 1:
            return json.dumps({'status': '200', 'login': login})
        else:
            response.status = 500
            return json.dumps({'status': '500', 'error': 'Too much affected rows, during insertion of new user.'})
    else:  # In case login already exists in db
        response.status = 400
        return json.dumps({'status': '400', 'error': 'Login is already taken.'})


# http://config.server_host:config.server_port/v1/auth?login=..&password=..
def v1_auth():
    """ Generate new api key, register it in db and give to client
    2 GET params (both str):
        login
        password
    Returns JSON:
        200 = api_key + api_key in HTTP-header "Authentication"
        400 = Missing params/Wrong auth data
        500 = Duplicate profiles/Error during insertion api_key
    """
    if 'login' not in request.query or 'password' not in request.query:
        response.status = 400
        return json.dumps({'status': '400', 'error': 'Missing GET params, 2 needed (login, password).'})

    login = request.query.login
    password = request.query.password

    db_pass_tuple = exec_sql("SELECT password FROM profiles WHERE login='" + login + "'")
    db_pass_count = db_pass_tuple[0]
    db_pass = db_pass_tuple[1][0]["password"]

    if db_pass_count == 0:  # Case 'not found'
        response.status = 400
        return json.dumps({'status': '400', 'error': 'Wrong login or password given.'})
    elif db_pass_count > 1:  # Case 'duplicates' (anomaly)
        response.status = 500
        return json.dumps({'status': '500', 'error': 'Found few profiles with given login.'})
    elif db_pass_count == 1:  # Case 'OK, found account with given login'
        if db_pass == hashlib.sha256(password.encode()).hexdigest():  # If passwords match
            # Generate api_key and then write it into db
            api_key = hashlib.sha256((str(datetime.datetime.now()) + login).encode()).hexdigest()
            insert_query = exec_sql("UPDATE profiles SET api_key='" + api_key + "' WHERE login = '" + login + "'")

            if insert_query[0] == 1:
                response.add_header("Authentication", api_key)
                return json.dumps({'status': '200', 'api_key': api_key})
            else:
                response.status = 500
                return json.dumps({'status': '500', 'error': 'Something went wrong during insertion api_key into db.'})
        else:  # Case 'wrong password'
            response.status = 400
            return json.dumps({'status': '400', 'error': 'Wrong login or password given.'})


# http://config.server_host:config.server_port/v1/change_name?api_key=..&new_name=..
# TODO: (maybe) add new param - password
# TODO: api_key validation (length)
def v1_change_profile_name():
    """ Change profile_name for authenticated client
    2 GET params:
        api_key
        new_name
    Returns:
        200 = profile_name(new_name)
        400 = Missing new_name/Invalid name
        401 = Missing api_key or it's wrong
        500 = Duplicate profiles/Troubles with update query
    """
    if 'api_key' not in request.query:
        response.status = 401
        return json.dumps({'status': '401', 'error': 'This method requires authentication.'})

    if 'new_name' not in request.query:
        response.status = 400
        json.dumps({'status': '400', 'error': 'Missing new_name param.'})

    if len(request.query.new_name) < 3:
        response.status = 400
        json.dumps({'status': '400', 'error': 'Name must consist at least 3 chars.'})

    if all(x.isalpha() or x.isspace() for x in request.query.new_name):
        response.status = 400
        json.dumps({'status': '400', 'error': 'Name must consist only of letters.'})

    db_profile_info = exec_sql("SELECT * FROM profiles WHERE api_key='" + request.query.api_key + "'")
    if db_profile_info[0] == 1:  # Case 'api_key is okay'
        update_query = exec_sql("UPDATE profiles SET profile_name='" + request.query.new_name + "' WHERE api_key='" + request.query.api_key + "'")
        if update_query[0] == 1:
            return json.dumps({'status': '200', 'profile_name': request.query.new_name})
        else:
            response.status = 500
            return json.dumps({'status': '500', 'error': 'Something went wrong during updating profile_name in db.'})

    elif db_profile_info[0] == 0:  # Case 'api key is wrong'
        response.status = 401
        return json.dumps({'status': '401', 'error': 'Wrong api_key.'})
    else:  # Case 'duplicates'
        response.status = 500
        return json.dumps({'status': '500', 'error': 'Found few profiles with given api_key.'})


# http://config.server_host:config.server_port/v1/get_profile_data?api_key=..&profile_id=..
# if profile_id empty - returns current users profile data
# TODO: (maybe) cause error if id is not given
# TODO: (maybe) fetch data by some other field, not id
def v1_get_profile_data():
    """ Fetch data about user profile by given id. If id is not given - fetch own data
        Data: profile_name, photo_file_url, date_of_registration
    2 GET params:
        api_key
        profile_id - optional
    Returns:
        200 = Own or found by id data
        400 = Given id, but profile not found
        401 = Missing or wrong api_key
        500 = Duplicate profiles
    """

    if 'api_key' not in request.query:
        response.status = 401
        return json.dumps({'status': '401', 'error': 'This method requires authentication.'})

    db_profile_info = exec_sql("SELECT * FROM profiles WHERE api_key='" + request.query.api_key + "'")

    if db_profile_info[0] == 1:  # Case 'api_key is ok'
        if 'profile_id' not in request.query or request.query.profile_id.strip() == '':
            # Case 'profile_id is not given' - fetch own data
            profile_data = db_profile_info[1][0]
            json_report = json.dumps({
                'status': '200',
                'data': {
                    'profile_name': profile_data['profile_name'],
                    'profile_photo_url': profile_data['profile_photo_url'],
                    'date_of_registration': str(profile_data['date_of_registration'])
                }
            })
            return json_report
        else:  # Case 'profile_id is given'
            db_profile_info = exec_sql("SELECT * FROM profiles WHERE id=" + request.query.profile_id)
            if db_profile_info[0] == 1:  # Case 'profile with given id found'
                profile_data = db_profile_info[1][0]
                json_report = json.dumps({
                    'status': '200',
                    'data': {
                        'profile_name': profile_data['profile_name'],
                        'profile_photo_url': profile_data['profile_photo_url'],
                        'date_of_registration': str(profile_data['date_of_registration'])
                    }
                })
                return json_report
            elif db_profile_info[0] == 0:  # Case 'id is wrong'
                response.status = 400
                return json.dumps({'status': '400', 'error': 'Profile with given id not found.'})
            else:
                response.status = 500
                return json.dumps({'status': '500', 'error': 'Found few profiles with given profile_id.'})
    elif db_profile_info[0] == 0:
        response.status = 401
        return json.dumps({'status': '401', 'error': 'Wrong api_key.'})
    else:
        response.status = 500
        return json.dumps({'status': '500', 'error': 'Found few profiles with given api_key.'})


# http://config.server_host:config.server_port/v1/upload_avatar?api_key=..&file_url=..
# TODO: Add possibility to upload image from PC
def v1_upload_profile_image():
    """ Download image from given URL and mark it as profile photo, delete old image
    2 GET params:
        api_key
        file_url
    Returns:
        200 = deleted old image, new image is on server and updated path to file in db
        400 = Missing file_url/Wrong file type
        401 = Missing api_key or it's wrong
        500 = Duplicate profiles/Error while download/Error while updating db
    """

    if 'api_key' not in request.query:
        response.status = 401
        return json.dumps({'status': '401', 'error': 'This method requires authentication.'})

    if 'file_url' not in request.query:
        response.status = 400
        return json.dumps({'status': '400', 'error': 'Missing file_url param.'})

    db_profile_info = exec_sql("SELECT * FROM profiles WHERE api_key='" + request.query.api_key + "'")

    if db_profile_info[0] == 1:  # Case 'api_key is ok'
        # Make old file backuo(if exists) to delete it later
        old_file_path = db_profile_info[1][0]['profile_photo_url']
        if old_file_path:
            os.rename(old_file_path, old_file_path + '.backup')

        # Restore image from backup in case of error
        def restore_img():
            if old_file_path:
                os.rename(old_file_path + '.backup', old_file_path)

        # Suitable for storage name for image and path to directory with images
        file_name = str(db_profile_info[1][0]["id"]) + "_avatar"
        file_path = "content"
        # Correct path to future file
        download_image_path = os.path.join(file_path, file_name)
        try:
            # Download
            urllib.request.urlretrieve(request.query.file_url, download_image_path)
            # Detect file type
            file_ext = str(imghdr.what(download_image_path))
            if file_ext == 'None':
                restore_img()
                response.status = 400
                return json.dumps({'status': '400', 'error': 'Looks like given file is not image'})
            file_full_path = str(os.path.join(file_path, file_name + "." + file_ext))
            # Give file extension corresponding to it's type
            os.rename(download_image_path, os.path.join(file_path, file_name + "." + file_ext))
            # Record new path to image into db
            update_query = exec_sql(
                "UPDATE profiles SET profile_photo_url='{0}' WHERE api_key='{1}'"
                .format(file_full_path, request.query.api_key)
            )
            print(file_full_path, old_file_path, sep='\n')
            if update_query[0] == 1 or file_full_path == old_file_path:
                # As new image successfully downloaded and it's path recorded in db, old one can be deleted
                os.remove(old_file_path + '.backup')
                return json.dumps({'status': '200'})
            else:
                restore_img()
                response.status = 500
                return json.dumps({'status': '500', 'error': 'Some error while updating image path in db.'})
        except:
            restore_img()
            response.status = 500
            return json.dumps({'status': '500', 'error': 'Error during downloading file.'})
    elif db_profile_info[0] == 0:  # Case 'Wrong api_key'
        response.status = 401
        return json.dumps({'status': '401', 'error': 'Wrong api_key.'})
    else:  # Case 'Duplicate profiles'
        response.status = 500
        return json.dumps({'status': '500', 'error': 'Found few profiles with given api_key.'})
