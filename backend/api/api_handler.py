from flask_restful import Resource, reqparse
import requests
import json
import numpy
import pandas

class api_handler(Resource):

  def get(self):
    return "HELLO WORLD"

  def post(self):
    print(self)
    parser = reqparse.RequestParser()
    parser.add_argument('locationType', type=str)
    parser.add_argument('numLocations', type=int)
    parser.add_argument('city', type=str)

    args = parser.parse_args()
    location = args['locationType']
    num_locations = args['numLocations']
    city = args['city']

    if location:
      message = calculate(location, num_locations, city)
    else:
      message = "No Msg"
    
    return message

def calculate(location_type, num_locations, city):
  api_key= "PLACEHOLDER"
  headers = {'Authorization': 'Bearer %s' % api_key}
  url='https://api.yelp.com/v3/businesses/search'
  params = {'term':location_type,'location':city}
  req=requests.get(url, params=params, headers=headers)
  req=json.loads(req.text)
  results_list = runKMeans(num_locations, req)
  search_query = location_type
  message = {"searchQuery": search_query, "resultsList": results_list}
  return message

def runKMeans(num_locations, req):
  total_locations = 20
  names = []
  addresses = []
  ratings = []
  urls = []
  coordinates = []
  images = []
  ids = []
  
  for i in range(0, total_locations) :
    name = req["businesses"][i]["name"]
    names.append(name)
    address = req["businesses"][i]["location"]["display_address"]
    addresses.append(address)
    rating = req["businesses"][i]["rating"]
    ratings.append(rating)
    url = req["businesses"][i]["url"]
    urls.append(url)
    coordinate = req["businesses"][i]["coordinates"]
    coordinates.append(coordinate)
    image = req["businesses"][i]["image_url"]
    images.append(image)
    id = req["businesses"][i]["id"]
    ids.append(id)

  from sklearn.cluster import KMeans

  sanitized_df = pandas.DataFrame(coordinates, columns=["longitude", "latitude"])
  location_data = sanitized_df.copy()
  location_data.insert(0, 'name', names)
  location_data.insert(1, 'address', addresses)
  location_data.insert(2, 'rating', ratings)
  location_data.insert(3, 'url', urls)
  location_data.insert(4, 'image', images)
  location_data.insert(5, 'id', ids)

  kmeans = KMeans(
    init="random",
    n_clusters=round(total_locations / num_locations),
    n_init=10,
    max_iter=300,
    random_state=42
  )
  kmeans.fit(sanitized_df)

  labels = kmeans.labels_
  centroids = kmeans.cluster_centers_
  location_data["cluster"] = labels
  centroid_df = pandas.DataFrame(centroids, columns=["cx", "cy"])
  centroid_df["cluster"] = range(0, len(centroid_df))
  location_data = location_data.merge(centroid_df, left_on='cluster', right_on='cluster')
  location_data["distance"] = numpy.sqrt(numpy.square(location_data["cx"] - location_data["longitude"]) + numpy.square(location_data["cy"] - location_data["latitude"]))
  location_data["avg_distances"] = location_data.groupby("cluster")["distance"].transform("mean")
  location_data = location_data.sort_values("avg_distances")

  place = 1
  best_cluster = location_data["cluster"][place]
  threshold = num_locations
  num_in_group = 1
  while threshold > num_in_group:
    if best_cluster == location_data["cluster"][place + 1]:
      num_in_group = num_in_group + 1
    else:
      place = 1
      best_cluster = best_cluster + 1
      num_in_group = 1
    place = place + 1
  best_result = location_data[location_data["cluster"] == best_cluster]
  best_result = best_result.loc[:,["name", "address", "rating", "url", "image", "id"]]
  best_result.set_index("id", drop=True, inplace=True)
  final_result = best_result.to_dict(orient="index")
  return final_result