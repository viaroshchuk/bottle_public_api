import getpass
import urllib.request
import urllib.error
import urllib.parse
import json


def register():
    print('[Registration]')
    login = input('Login: ')
    password = getpass.getpass('Password: ')
    name = input('Your full name: ')
    try:
        response = urllib.request.urlopen('http://localhost:8080/v1/register?login={}&password={}&name={}'
                                          .format(login, password, name)).read()

        dict_response = json.loads(response.decode())
        print('Registration completed!\nYour login:', dict_response['login'])
    except urllib.error.HTTPError:
        print('Bad HTTP response :(')


def auth():
    print('[Logging in]')
    login = input('Login: ')
    password = getpass.getpass('Password: ')
    try:
        response = urllib.request.urlopen('http://localhost:8080/v1/auth?login={}&password={}'
                                          .format(login, password)).read()
        dict_response = json.loads(response.decode())
        print("You've successfully logged in!")
        return dict_response['api_key']
    except urllib.error.HTTPError:
        print('Bad HTTP response :(')
        return login_or_register()


def login_or_register():
    command = input('To start working you have to login or register (l/r): ')
    if command.lower() == 'l' or command.lower() == 'login':
        return auth()
    elif command.lower() == 'r' or command.lower() == 'register':
        register()
        return login_or_register()
    else:
        return login_or_register()


def get_profile_data(api_key):
    profile_id = input('Enter profile id (leave empty to get your profile): ')
    try:
        response = urllib.request.urlopen('http://localhost:8080/v1/get_profile_data?api_key={}&profile_id={}'
                                          .format(api_key, profile_id)).read()
        dict_response = json.loads(response.decode())
        print("[Profile data]")
        for key in dict_response['data']:
            print('\t{}:\t\t\t{}'.format(key, dict_response['data'][key]))
    except urllib.error.HTTPError:
        print('Bad HTTP response :(')


def change_name(api_key):
    new_name = input("Enter new name: ")
    try:
        response = urllib.request.urlopen('http://localhost:8080/v1/change_profile_name?api_key=' + api_key + '&new_name=' +
                               urllib.parse.quote(new_name)).read()
        print("Your name is changed now!")
    except urllib.error.HTTPError:
        print('Bad HTTP response :(')


def upload_photo(api_key):
    option = input("Do you want to upload from [w]eb, or from [c]omputer?")
    if option == 'c':
        file_path = input('Input path to your file: ')
        req = urllib.request.Request("http://localhost:8080/v2/upload_profile_image?api_key=" + api_key)
        with open(file_path, 'rb') as file:
            req.data = file.read()
        urllib.request.urlopen(req)
        print('Your profile image is updated now!')
    elif option == 'w':
        file_url = input("Input image url: ")
        try:
            urllib.request.urlopen('http://localhost:8080/v1/upload_profile_image?api_key={}&file_url={}'
                                   .format(api_key, file_url)).read()
            print("Your profile image is updated now!")
        except urllib.error.HTTPError:
            print('Bad HTTP response :(')
    else:
        print('Invalid option...')


print('This is test of ineraction with bottle_public_api.')
api_key = login_or_register()
print('You can try one of these commands:',
      '[c]hange name',
      '[g]et profile data (yours or others)',
      '[u]pload photo to your profile (from website)',
      sep='\n\t')
while True:
    command = input('Type the key to choose command (c/g/u) or (q) to quit: ').lower()
    if command == 'c':
        change_name(api_key)
    elif command == 'g':
        get_profile_data(api_key)
    elif command == 'u':
        upload_photo(api_key)
    elif command == 'q':
        exit(0)
    else:
        print('Unknown command')

