from flask import Flask, request, render_template, Response
import pandas as pd
import turicreate as tc
import pickle
import random
import sys

reload(sys)
sys.setdefaultencoding('utf8')
sf_hikes = tc.SFrame('Data/all_hikes_with_hike_name.csv')
hikes = list(sf_hikes['hike_name'])
sf_ratings = tc.SFrame('Data/all_ratings_matrix.csv')
hike_side_data = tc.SFrame('Data/all_hikes_with_hike_id.csv')
with open('Data/all_hike_ids.pkl') as f:
	hike_ids = pickle.load(f)

with open('Data/all_user_ids.pkl') as f:
	user_ids = pickle.load(f)

content_model = tc.load_model('web_app/hike_content_recommender')
popular_count_model = tc.load_model('web_app/hike_popularity_count_recommender')
popular_stars_model = tc.load_model('web_app/hike_popularity_stars_recommender')
rf_model = tc.load_model('web_app/rank_factorization_recommender')


app = Flask(__name__)


def list_hikes(sf_hikes):
	hikes = []
	for h in sf_hikes['hike_name']:
		hikes.append(h)
	return hikes

def get_info(hike):
	data = sf_hikes[sf_hikes['hike_name']==hike]
	return data

def get_hike_info(recs):
	hike_info = []
	for rec in recs:
		hike = rec['hike_id']
		info = sf_hikes[sf_hikes['hike_id']==hike]
		hike_info.append(info)
	return hike_info

def top_five(recs):
    hike_info = []
    for rec in recs:
        info = sf_hikes[sf_hikes['hike_id']==rec]
        hike_info.append(info)
    return hike_info
  

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/username', methods=['GET', 'POST'])
def username():
	names = user_ids.keys()
	return render_template('username.html', names=names)

@app.route('/choose-hike', methods=['GET', 'POST'])
def enter_hike():
	hikes = list_hikes(sf_hikes)
	return render_template('choose-hike.html', hikes=hikes)

@app.route('/personal-recs', methods=['GET', 'POST'])
def enter_username():
	username = request.form.get('username')
	try:
		user_id = user_ids[username]
	except:
		return render_template('error.html')	
	if username == '':
		return render_template('error.html')
	else:
		recs = rf_model.recommend(users = [user_id], k=5)
		print(recs)
		hike_data = get_hike_info(recs)
		return render_template('personal-recs.html', hike_data=hike_data)

@app.route('/make-recommendations', methods=['POST', 'GET'])
def get_recommendations():
	hike = request.form.get('hike-name')
	if hike == '':
		return render_template('error.html')
	else:
		recs = content_model.recommend_from_interactions(observed_items=[hike], k=10)
		hike_data = []
		for rec in recs:
			name = rec['hike_name']
			info = get_info(name)
			info['score'] = "{:.1%}".format(rec['score'])
			hike_data.append(info)
		your_hike = get_info(hike)
		return render_template('make-recommendations.html', your_hike=your_hike, hike_data=hike_data)

@app.route('/most-reviewed', methods=['POST', 'GET'])
def get_popular():
    recs = []
    rec = popular_count_model.recommend(k=10)
    for h_id in rec[0:10]:
        hike = h_id['hike_id']
        recs.append(hike)
    best_hikes = top_five(recs)
    return render_template('most-reviewed.html', best_hikes=best_hikes)

@app.route('/highest-rated', methods=['POST', 'GET'])
def get_highest():
    recs = []
    rec = popular_stars_model.recommend(k=10)
    for h_id in rec[0:10]:
        hike = h_id['hike_id']
        recs.append(hike)   
    best_hikes = top_five(recs)
    return render_template('highest-rated.html', best_hikes=best_hikes)

@app.route('/power-rated', methods=['POST', 'GET'])
def get_power():
	recs = []
	power_ratings = sf_hikes.sort('power_rating', ascending=False)
	for h_id in power_ratings[0:10]:
		hike = h_id['hike_id']
		recs.append(hike)
	best_hikes = top_five(recs)	
	return render_template('power-ratings.html', best_hikes=best_hikes)


app.run()
