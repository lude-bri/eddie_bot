import ptapi42
from datetime import date
import time
from pprint import pprint

def api_call_users(api, cursus_id, campus_id, pool_year, pool_month):
	url = 'users'
	params = {
		'cursus_id': cursus_id,
		'campus_id': campus_id,
		"filter": {
			'pool_year': pool_year,
			'pool_month': pool_month, 
		}
	}
	users = api.get(url=url, params=params)

	return users
	
def api_call_log(api, id, begin_date, end_date):
	url = f'users/{id}/locations_stats'
	params = {
		'begin_at' : begin_date,
		'end_at' : end_date,
	}
	response_log = api.get(url=url, params=params)
	return response_log

def api_call_scale(api, begin_date, end_date, user_id):
	url = 'scale_teams'
	params = {
		'range': {
			'updated_at': f"{begin_date}, {end_date}",
		},
		'user_id' : user_id,
	}
	response_scale = api.get(url=url, params=params)
	return response_scale

def api_call_exam(api, project_id, user_id):
	url = 'projects_users'
	params = {
		'project_id' : project_id,
		"filter": {
			'user_id': user_id,
		}
	}
	response_exam = api.get(url=url, params=params)
	return response_exam

def main():
	api = ptapi42.Api42(requests_per_second=2, log_lvl='DEBUG')
	cursus_id = 9
	campus_id = 58
	pool_year = 2025
	pool_month = 'january'
	counter = 0
	gave_ups = []
	response_users = api_call_users(api, cursus_id, campus_id, pool_year, pool_month)
	if response_users: # Piscine Users
		for i in response_users:
			if counter >= 5:
				break
			time.sleep(1)
			# print(f"Fetching logs for user {i['login']} -> id: {i['id']}")
			# print("\n")
			#logtime = api_call_log(api, i["id"], date(2025, 1, 20), date(2025, 1 , 24))
			logtime = api_call_log(api, i["id"], '2025-01-20', '2025-01-24')
			if not logtime:
				scale = api_call_scale(api, '2025-01-20', '2025-01-24', i["id"])
				exam = api_call_exam(api, 1301, i["id"])
				if not scale :
					gave_ups.append((i["login"], "exam: " + str(bool(exam))))
			print("\n")
			counter = counter + 1
	for value in gave_ups:
		print(f"{value[0]} -> {value[1]}")

if __name__ == '__main__':
	main()
