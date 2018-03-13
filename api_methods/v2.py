from bottle import request, response
from mysql_query import exec_sql
import json
import imghdr
import os


def v2_upload_profile_image():
    """ Upload image from clients device and mark it as profile photo, delete old image
        1 GET param:
            api_key
        Returns:
            200 = deleted old image, new image is on server and updated path to file in db
            400 = Wrong file type
            401 = Missing api_key or it's wrong
            500 = Duplicate profiles/Error while upload/Error while updating db
        """
    if 'api_key' not in request.query:
        response.status = 401
        return json.dumps({'status': '401', 'error': 'This method requires authentication.'})

    db_profile_info = exec_sql("SELECT * FROM profiles WHERE api_key='{}'".format(request.query.api_key))
    if db_profile_info[0] == 1:  # Case 'api_key is ok'
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

        if request.body:
            try:
                with open(download_image_path, 'wb') as file:
                    file.write(request.body.getvalue())
                file.close()
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
        else:
            restore_img()
            response.status = 400
            return json.dumps({'status': '400', 'error': 'Empty file.'})
    elif db_profile_info[0] == 0:  # Case 'Wrong api_key'
        response.status = 401
        return json.dumps({'status': '401', 'error': 'Wrong api_key.'})
    else:  # Case 'Duplicate profiles'
        response.status = 500
        return json.dumps({'status': '500', 'error': 'Found few profiles with given api_key.'})


