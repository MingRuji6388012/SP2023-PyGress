import requests
import json
import time

ndex_base_url = 'http://services.bigmech.ndexbio.org'

def send_request(url_suffix, params):
    res = requests.post(ndex_base_url + url_suffix, data=json.dumps(params))
    res_json = get_result(res)
    return res_json

def get_result(res):
    status = res.status_code
    if status == 200:
        return res.text
    task_id = res.json()['task_id']
    print 'NDEx services task submitted...' % task_id
    time_used = 0
    try:
        while status != 200:
            res = requests.get(ndex_base_url + '/task/' + task_id)
            status = res.status_code
            if status != 200:
                time.sleep(5)
                time_used += 5
    except KeyError:
        next
        return None
    print 'NDEx services task complete.' % task_id
    return res.text
