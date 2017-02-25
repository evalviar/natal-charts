from flask import Flask, request, jsonify
from datetime import datetime, timezone
from models import *
import geocoder
import os

app = Flask(__name__)
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')

@app.route('/')
def index():
  return "Hello"

@app.route('/geocode', methods=['POST'])
def geocode():
  query = request.form.get('q')
  if not query:
    return jsonify({'error': "Invalid input: query"})
  g = geocoder.google(query, key=GOOGLE_API_KEY)
  if not g or g.status != 'OK':
    return jsonify({'error': "Unable to find location"})
  tz = geocoder.google([g.lat, g.lng], method="timezone", key=GOOGLE_API_KEY)

  # E.g. -18000 --> -05:00 // 12600 --> +3:30
  tz_offset_negative = tz.rawOffset < 0
  tz_offset_hours = int(abs(tz.rawOffset)/60//60)
  tz_offset_minutes = int((abs(tz.rawOffset)/60/60 - tz_offset_hours) * 60)

  return jsonify({
    'query': query,
    'location': g.address,
    'geo': [g.lat, g.lng],
    'utc_offset': '{}{:02d}:{:02d}'.format("-" if tz_offset_negative else "+",
        tz_offset_hours, tz_offset_minutes)
  })


@app.route('/chart', methods=['POST'])
def chart():
  name = request.form.get('name')
  if not name:
    return jsonify({'error': "Invalid input: name"})
  
  birth_year = request.form.get('date_year', -1, type=int)
  birth_month = request.form.get('date_month', -1, type=int)
  birth_day = request.form.get('date_day', -1, type=int)
  birth_hour = request.form.get('date_hour', -1, type=int)

  for el in [birth_year, birth_month, birth_day, birth_hour]:
    if el == -1:
      return jsonify({'error': "Invalid input: birthdate"})

  birth_lon = request.form.get('location_lon', 0.0, type=float)
  birth_lat = request.form.get('location_lat', 0.0, type=float)

  if birth_lon == 0.0 or birth_lat == 0.0:
    return jsonify({'error': "Invalid input: birth geo"})

  birth_utc_offset = request.form.get('location_utc_offset', '+00:00')
  
  birthdate = datetime(birth_year, birth_month, birth_day, birth_hour, 0, 0, tzinfo=timezone.utc)
  person = Person(name, birthdate, birth_lon, birth_lat, birth_utc_offset)
  chart = NatalChart(person)

  return jsonify(chart.to_dict())


if __name__ == '__main__':
    app.run(port=os.environ.get('PORT', 8080))