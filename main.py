import requests
import datetime
import os
import json
from flask import Flask

# Open the JSON file
with open('config.json', 'r') as f:
  data = json.load(f)
headers = {
    'Authorization': f'Token {os.environ["REPLICATE_KEY"]}',
}


def check_and_cancel_job(prediction_id, start_time, model, data):
  current_time = datetime.datetime.utcnow()
  elapsed_time = (current_time - start_time).total_seconds()
  should_cancel = (model in data
                   and elapsed_time > data[model]) or (elapsed_time
                                                       > data['default'])
  if should_cancel:
    cancel_url = f"https://api.replicate.com/v1/predictions/{prediction_id}/cancel"

    cancel_response = requests.post(cancel_url, headers=headers)
    if cancel_response.status_code == 200:
      print("Job canceled successfully.")
    else:
      print(
          f"Failed to cancel the job. for {prediction_id}, resp: {cancel_response.status_code}"
      )


def main():

  response = requests.get('https://api.replicate.com/v1/predictions',
                          headers=headers)

  if response.status_code == 200:
    dataresponse = response.json()
    for prediction in dataresponse['results']:
      try:
        start_time = datetime.datetime.strptime(prediction['started_at'],
                                                '%Y-%m-%dT%H:%M:%S.%fZ')
        if (prediction['status'] not in ['succeeded', 'canceled']):
          print(prediction['status'])
          check_and_cancel_job(prediction['id'], start_time,
                               prediction['model'], data)
      except TypeError:
        print("No started_at field found in the prediction.")
  else:
    print("Failed to fetch predictions.", response)


app = Flask(__name__)


@app.route('/run', methods=['POST'])
def echo():
  main()
  return 'Main executed successfully', 200


app.run(host='0.0.0.0', port=8080)

# from shell run: (easier than whole nother repl to hit it)
# curl -XPOST localhost:8080/run
