#################################
##### Name: Jiahong Xu      #####
##### Uniqname: jiahongx    #####
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key
import time
import sqlite3 

################### code for accessing API and crawling and cache  ##################
OMDb_BASE_URL = "http://www.omdbapi.com/?apikey=ff9eafcd"
IMDb_URL = "http://www.imdb.com"
CACHE_FILE_NAME = "cache.jason"

def load_cache():
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache

def save_cache(cache):
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

CACHE_DICT = load_cache()

def make_url_request_using_cache(url, cache):
    if (url in cache.keys()): # the url is our unique key
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        time.sleep(1)
        response = requests.get(url)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]

class MovieInfo:
    def __init__(self, id = None, title = None, genre = None, ratings = None, director = None, actors = None, url = None, json = None):
        if json:
            self.id = json['imdbID']
            self.title = json['Title']
            self.genre = json['Genre']
            self.url = IMDb_URL+"/title/"+self.id
            if json['imdbRating'] == 'N/A':
                self.ratings = -1
            else:
                self.ratings = float(json['imdbRating'])
            self.director = json['Director'].split(',')[0]

            all_actors = json['Actors'].split(',')
            if len(all_actors)<=2:
                self.actors = ','.join(all_actors)
            else: 
                self.actors = ','.join(all_actors[0:2]) # a list, contains at most two names
        else:
            self.id = id
            self.title = title
            self.genre = genre
            self.ratings = ratings
            self.director = director
            self.actors = actors
            self.url = url
    def info(self):
        '''Print the ratings, director and the two main actors of the movie
        '''
        print('['+self.title+']'+' ('+self.ratings+')')
        print('Director: ' + self.director)
        print('Actors: ' + ','.join(self.actors))

class DirectorInfo:
    def __init__(self, name = None, url = None, related_movie_titles = []):
        self.name = name
        self.url  = url
        self.related_movie_titles = related_movie_titles


def get_movie_info_from_omdb(movie_title):
    '''Make a MovieInfo instance from the OMDb
    
    Parameters
    ----------
    movie_title: string
        The name of the movie to be searched in OMDb
    
    Returns
    -------
    instance
        a MovieInfo instance or None if the movie is not found in OMDb
    '''
    movie_title = movie_title.replace(" ","+")
    url = OMDb_BASE_URL + "&t=" + movie_title 
    json_str = make_url_request_using_cache(url, CACHE_DICT)
    dict_info = json.loads(json_str)
    if 'Error' in dict_info:
        return None
    else:
        movie = MovieInfo(json = dict_info)
        return movie

def get_director_url(movie):
    '''get the url of the director from a MovieInfo instance

    Parameters
    ----------
    movie: instance 
        an instance of MovieInfo
    
    Returns
    -------
    director_url: string
        a url of the director
    '''
    url = movie.url
    response_text = make_url_request_using_cache(url, CACHE_DICT)
    soup = BeautifulSoup(response_text, 'html.parser')
    people_div_list = soup.find_all('div', class_='credit_summary_item')
    for people_div in people_div_list:
        job = people_div.find('h4')
        if job.text == 'Director:' or job.text == 'Directors:':
            director_url = IMDb_URL + people_div.find('a')['href']
            return director_url

def get_director_instance(movie):
    '''Make a DirectorInfo instance from a url of the director

    Parameters
    ----------
    movie: instance
        an instance of MovieInfo
    
    Returns
    -------
    director: instance
        an instance of DirectorInfo
    '''
    director_url = get_director_url(movie)
    response_text = make_url_request_using_cache(director_url, CACHE_DICT)
    soup = BeautifulSoup(response_text, 'html.parser')
    name = soup.find('h1', class_ = 'header').find('span', class_ = 'itemprop').text
    related_movies = []
    director_info_list = soup.find_all('div', id=lambda x: x and x.startswith('director-'))
    for director_info in director_info_list:
        movie_title = director_info.find('b').find('a').text.lower()
        related_movies.append(movie_title)

    director = DirectorInfo(name = name, url = director_url, related_movie_titles=related_movies)
    return director
#########################################################################################



############ code for database processing ###############################################

def create_tables():
    conn = sqlite3.connect(r"C:\Users\Lenovo\Desktop\SI507\final_project\MovieRecommend.sqlite")
    cur = conn.cursor()
    create_movie_table = '''
        CREATE TABLE IF NOT EXISTS "Movies" (
            "Id"      INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            "Title"   TEXT NOT NULL,
            "imbdID"  TEXT NOT NULL,
            "Genre"   TEXT NOT NULL,
            "Ratings"  REAL NOT NULL,
            "Directors"  TEXT NOT NULL,
            "Actors"  TEXT NOT NULL,
            UNIQUE ("Title")
        );
    '''
    create_director_table = '''
            CREATE TABLE IF NOT EXISTS "Directors" (
            "Id"      INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            "Name"   TEXT NOT NULL,
            "URL"  TEXT NOT NULL,
            UNIQUE ("Name")
        );
    '''
    cur.execute(create_movie_table)
    cur.execute(create_director_table)
    conn.commit()

def insertItems_movie_table(Movie):
    '''insert a row in the "Movies" table

    Parameters
    ----------
    Movie: instance
        an instance of MovieInfo
    '''
    conn = sqlite3.connect(r"C:\Users\Lenovo\Desktop\SI507\final_project\MovieRecommend.sqlite")
    cur = conn.cursor()
    insert_movie = '''
        INSERT OR IGNORE INTO Movies
        VALUES (NULL, ?,?,?,?,?,?)
    '''
    movie_info = (Movie.title, Movie.id, Movie.genre, Movie.ratings, Movie.director, Movie.actors)
    cur.execute(insert_movie, movie_info)
    conn.commit()

def insertItems_director_table(Director):
    '''insert a row in the "Directors" table

    Parameters
    ----------
    Director: instance
        an instance of DirectorInfo
    '''
    conn = sqlite3.connect(r"C:\Users\Lenovo\Desktop\SI507\final_project\MovieRecommend.sqlite")
    cur = conn.cursor()
    insert_director = '''
        INSERT OR IGNORE INTO Directors
        VALUES (NULL, ?,?)
    '''
    director_info = [Director.name, Director.url]
    cur.execute(insert_director, director_info)
    conn.commit()
#############################################################################################


############################### main function ###############################################
def main():
    # create the sql called MovieRecommend
    create_tables()
    #######################################################################################
    #### input a movie name, get the url and the director infor of the movie on IMDb,  ####
    #### scrape the movie page for the page of the director,                           ####
    #### scrape the director page for other movies directed by the director,           ####
    #### save the info of the related movies and the director in MovieRecommend.sqlite ####
    #######################################################################################
    while True:
        movie_title = input("input the title of a movie, or \"exit\" to exit:").lower().strip()
        if movie_title=="exit":
            break

        else:
            input_movie = get_movie_info_from_omdb(movie_title)
            if not input_movie:
                print("The movie is not found.")

            else:
                insertItems_movie_table(input_movie)
                director = get_director_instance(input_movie)
                insertItems_director_table(director)

                for directed_movie_title in director.related_movie_titles:
                    if directed_movie_title is not movie_title:
                        directed_movie = get_movie_info_from_omdb(directed_movie_title)
                        if directed_movie is not None: 
                            insertItems_movie_table(directed_movie)


if __name__ == "__main__":
    main()


    
