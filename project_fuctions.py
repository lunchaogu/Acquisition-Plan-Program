from openai import OpenAI
import requests
import pandas as pd

def generate_query(category, area):
    unique_items = []
    for item in area:
        if item != '' and item not in unique_items:
            unique_items.append(item)
    unique_items.reverse()
    result = ' '.join(unique_items)
    return(f'{category}, {result}')
#--------------------------------------------------------------------------------------------------------
def get_POI(API_KEY, category, area, pagetoken, url):
    query = generate_query(category, area)
    print(query)
    params = {
        'query': query,
        'key': API_KEY,
        'pagetoken' : pagetoken,
        #'type' : "amusement_park",
        }
    result = requests.get(url, params=params)
    #Convert data into json type first and dataframe then
    result_js = result.json()
    result_df = pd.json_normalize(result_js['results'])
    #Check if there is next page and send the token to params
    if 'next_page_token' in result_js:
        page_token = result_js['next_page_token']
    else:
        page_token = None
    return(result_df, page_token)
#--------------------------------------------------------------------------------------------------------
def cleanup(dataframe, rating_threshold, country):
    dataframe = dataframe.drop_duplicates(subset=['place_id'])
    dataframe = dataframe.drop_duplicates(subset=['formatted_address','name'])
    dataframe = dataframe[dataframe['formatted_address'].str.contains(country)]
    dataframe['country'] = dataframe['plus_code.compound_code'].str.extract(r'((?<=\s)[a-zA-Z]+$)')
    place_info = dataframe['plus_code.compound_code'].str.replace(r'((,)[\sa-zA-Z]+$)', '', regex=True)
    dataframe['state'] = place_info.str.extract(r'((?<=\s)[a-zA-Z]+$)')
    place_info = place_info.str.replace(r'((,)[\sa-zA-Z]+$)', '', regex=True)
    dataframe['city'] = place_info.str.extract(r'((?=\s).+)')
    dataframe = dataframe[['state','city','name','formatted_address', 'place_id', 'rating', 'user_ratings_total', 'types', 'plus_code.compound_code']]
    dataframe = dataframe[dataframe['user_ratings_total'] >= rating_threshold].reset_index(drop=True)
    return(dataframe) 
#---------------------------------------------------------------------------------------------------------
def get_completion(prompt, OpenAI_key, model = 'gpt-3.5-turbo'):
    client = OpenAI(
        api_key=OpenAI_key
        )
    response = client.chat.completions.create(
        messages = [
            {'role': 'user','content': prompt}],
        model=model,
        timeout=20,
        temperature=0, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message.content

