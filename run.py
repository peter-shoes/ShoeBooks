# /////////////////////////////////////////////////////////////////
# PETER-SHOES LABS 2019
# ALL CODE IS FROM THE DATA VOID AND CAN ONLY BE RUN ON WINDOWS 95
# NO RIGHTS RESERVED
# HAVE AT IT
# //////////////////////////////////////////////////////////////////

import decimal
import random
from getpass import getpass

import requests
import settings
import datetime
import hashlib
import time


def checksum(activity_id, ts, token):
    md5 = hashlib.md5()
    md5.update('content_resource/{}/activity'.format(activity_id))
    md5.update(ts)
    md5.update(token)
    return md5.hexdigest()


def delay():
    # Delays the program
    min_sleep = float(settings.TIME_INTERVAL) * (1 - (float(settings.PERCENTAGE_VARIANCE) / 100))
    max_sleep = float(settings.TIME_INTERVAL) * (1 + float(settings.PERCENTAGE_VARIANCE) / 100)

    if max_sleep == min_sleep:
        time.sleep(max_sleep)
        return

    actual_sleep = float(decimal.Decimal(random.randrange(int(min_sleep * 100), int(max_sleep * 100))) / 100)
    # print("Sleeping for {} seconds".format(actual_sleep))
    time.sleep(actual_sleep)


def send_post(url, payload, headers=None):
    if headers:
        r = requests.post(url, json=payload, headers=login_data)
        return r.json()
    else:
        r = requests.post(url, json=payload)
        return r.json()


def send_get(url, params):
    r = requests.get(url, params=params)
    return r.json()


def login(username, password):
    SIGNIN_URL = 'https://zyserver.zybooks.com/v1/signin'
    headers = {
	    'Accept': 'application/json, text/javascript, */*; q=0.01',
	    'Accept-Encoding': 'gzip, deflate, br',
	    'Accept-Language': 'en-US,en;q=0.9',
	    'Origin': 'https://learn.zybooks.com',
	    'Referer': 'https://learn.zybooks.com/signin',
	    'Content-Type': 'application/json',
	    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
	    }
    payload = '{"email": "%s", "password": "%s"}' % (username, password)
    ret = requests.post(SIGNIN_URL, data=payload, headers=headers)
    return ret.json()

def get_activities(URL, access_code):
    URL_GET = '%s?auth_token=%s' % (URL, access_code)
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': URL,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
    }
    ret = requests.get(URL_GET, headers=headers)
    resources = ret.json()["section"]["content_resources"]
    for resource in resources:
        print(resource)
        activity_type = resource['activity_type']
        resource_type = resource['type']
        resource_id = resource['id']
        num_parts = resource['parts']

        payload = resource['payload']

        resource_url = 'https://zyserver.zybooks.com/v1/content_resource/{}/activity' \
            .format(resource_id)

        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%dT%H:%M.000")
        cs = checksum(resource_id, timestamp, auth_token)

        answer_payload = {'auth_token': auth_token, 'complete': True, 'timestamp': timestamp,
                          'zybook_code': zybook_code, '__cs__': cs, 'metadata': '{}', 'answer': 1}
        print(answer_payload)
        for i in range(num_parts):
            answer_payload['part'] = i
            response_data = send_post(resource_url, answer_payload)
            if response_data['success'] is True:

                type_str = resource_type
                if type_str == 'custom':
                    type_str = payload['tool']
                print('{} "{}" id {} part {} completed.'
                      .format(activity_type.title(), type_str, resource_id, i + 1))
                delay()
            else:
                print('{} "{}" id {} part {} failed.'
                      .format(activity_type.title(), type_str, resource_id, i + 1))



def main():
    try:
        login_data = login(settings.uname,settings.psswrd)
        print("Login Success")
    except:
        print("Incorrect Username or Password (????????????)")
        sys.exit(0)

    # print(login_data)

    auth_token = login_data['session']['auth_token']
    user_id = login_data['user']['user_id']

    get_classes_url = 'https://zyserver.zybooks.com/v1/user/' + str(user_id) + '/items'
    get_classes_params = {'items': '["zybooks"]', 'auth_token': auth_token}

    get_classes_data = send_get(get_classes_url, get_classes_params)

    for subject in get_classes_data['items']['zybooks']:
        zybook_code = subject['zybook_code']

        class_info_url = 'https://zyserver.zybooks.com/v1/zybooks'
        class_info_params = {'zybooks': '["' + zybook_code + '"]',
                             'auth_token': auth_token}

        class_info_data = send_get(class_info_url, class_info_params)

        zybook = class_info_data['zybooks'][0]

        # print(zybook)

        if (settings.COURSE != zybook_code
                and settings.COURSE != zybook['course']['course_call_number']
                and settings.COURSE != zybook['course']['name']):
            # Go to next zybook
            continue

        for chapter in zybook['chapters']:

            if settings.CHAPTER_NUMBER != chapter["number"]:
                # Go to next chapter
                continue

            for section in chapter['sections']:
                chapter_num = section['canonical_chapter_number']
                section_id = section['canonical_section_id']
                section_num = section['canonical_section_number']

                if str(section_num) not in settings.SECTION_NUMBERS.split(",") \
                        and settings.SECTION_NUMBERS != '*':
                    # Go to next section if it is not in settings
                    continue

                print("\n---Chapter " + str(chapter_num) + " : Section " + str(section_num) + "---\n")

                section_url = 'https://zyserver.zybooks.com/v1/zybook/{}/chapter/{}/section/{}' \
                    .format(zybook_code, chapter_num, section_num)
                section_params = {'auth_token': auth_token}

                section_data = send_get(section_url, section_params)

                get_activities(section_url, login_data["session"]["auth_token"])


if __name__=='__main__':
    main()
