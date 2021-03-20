# -*- coding: utf-8 -*-

"""
	Created by:	Shaheen Syed
	Date: 		July 2018

	Step 1 – Search for target tweets
	-------------------

	The tweets of interest are referred to as target tweets. That is, tweets for which we want to infer a sentiment class. This script uses the Twitter API to collect tweets 
	that match a specific search query. Note that tweets are only available within the search API if not older than 7 days. To create a dataset, execute once every 7 
	days, either manually or by using something like a cronjob. The collected target tweets will be saved on disk. It will furthermore be used to only retrieve the delta 
	of new tweets since the last time this script was run.

	Creates files in the folder files/target_tweets

	Before running, set the twitter key and secret, see https://developer.twitter.com/en/docs/basics/authentication/guides/access-tokens.html

	How to run?
	python 1_search_target_tweets.py
"""

# packages and modules
import json
from helper_functions import *
from twitter import Twitter
from datetime import datetime
from config import API_KEY, API_SECRET

"""
	Internal Helper Functions
"""


def get_last_tweet_id(folder):
    """
            Read the tweets that are collected before and obtain the last tweet ID. This tweet ID is then used to collect more tweets that were created after the last one we obtained
    """

    logging.info('Called function: {} '.format(sys._getframe().f_code.co_name))

    # read the files in the folder and sort them
    F = sorted(read_directory(folder))

    # check if files are present
    if len(F) > 0:

        # obtain the last created file
        f = F[-1]

        # read tweets in file
        tweets = read_plain_text(f, read_lines=True)

        # empty list to store tweet IDs in
        tweet_ids = []

        # loop trough each tweet
        for tweet in tweets:
            # convert string to json
            tweet = json.loads(tweet)
            # get tweet ID
            tweet_id = tweet['id']
            # save all IDs into a list
            tweet_ids.append(tweet_id)

        # obtain the latest ID
        latest_id = max(tweet_ids)

        logging.debug('Latest tweet ID: {}'.format(latest_id))
        return latest_id
    else:

        logging.debug('No tweets found, returning None as latest ID')
        return None


def search_tweets_from_API(save_name, save_location, query, last_tweet_id, tweets_per_query=100, max_tweets=10000000, max_id=-1):
    """
            Search for tweets

            Parameters
            ----------
            save_name: string
                    Name of the file to save the tweets to
            save_location: os.path
                    location to save the tweets to
            query: string
                    search query
            last_tweet_id: int
                    latest tweet ID that we collected previously (can also be None if collecting tweets for the first time)
            max_tweets : int (optional)
                    large number to make sure we collect all the available tweets
            tweets_per_query : int (optional)
                    the maximum number of tweets that can be returned by the API.
            max_id : int long (optional)
                    to make sure we exhaust the search
    """

    logging.info('Called function: {} '.format(sys._getframe().f_code.co_name))

    # create connection to twitter API
    twitter = Twitter(key=API_KEY, secret=API_SECRET)

    # connect to Twitter API
    twitter.connect_to_API()

    # create full file name
    file_name = os.path.join(save_location, save_name)

    # keep track of the number of tweets
    num_tweets = 0

    # create empty file
    with open(file_name, 'w') as f:

        while num_tweets < max_tweets:
            try:
                if (max_id <= 0):
                    if (not last_tweet_id):

                        new_tweets = twitter.search_tweets(
                            q=query, count=tweets_per_query, tweet_mode='extended')

                    else:

                        new_tweets = twitter.search_tweets(
                            q=query, count=tweets_per_query, since_id=last_tweet_id, tweet_mode='extended')

                else:

                    if (not last_tweet_id):

                        new_tweets = twitter.search_tweets(
                            q=query, count=tweets_per_query, max_id=str(max_id - 1), tweet_mode='extended')

                    else:

                        new_tweets = twitter.search_tweets(q=query, count=tweets_per_query, max_id=str(
                            max_id - 1), since_id=last_tweet_id, tweet_mode='extended')

                # update counter
                num_tweets += len(new_tweets)

                # check if no tweets could be obtained
                if num_tweets == 0:

                    logging.debug('No tweets found, no files created, exit...')

                    # close file
                    f.close()
                    # remove file (if we don't remove it here, we might use it to find the latest ID, but since its empty, it will give an error)
                    os.remove(file_name)

                    break

                # break if no more tweets can be retrieved
                if not new_tweets:
                    logging.debug('No more tweets found, exiting...')
                    break

                # append tweets to file
                for tweet in new_tweets:
                    f.write(json.dumps(tweet._json) + '\n')

                logging.debug(
                    'Downloaded number of tweets: {}'.format(num_tweets))

                # set the max ID
                max_id = new_tweets[-1].id

            except e:

                logging.error('[{}] : {}'.format(
                    sys._getframe().f_code.co_name, e))
                # close file
                f.close()
                # remove file (if we don't remove it here, we might use it to find the latest ID, but since its empty, it will give an error)
                os.remove(file_name)

                break


"""
	Script starts here
"""

if __name__ == "__main__":

    # create logging to console
    set_logger()

    logging.info('Start: {} '.format(__file__))

    # define modes of research and their search query
    modes_of_research = {	'interdisciplinary': 'interdisciplinary OR #interdisciplinary OR interdisciplinarity OR #interdisciplinarity',
                          'multidisciplinary': 'multidisciplinary OR #multidisciplinary OR multidisciplinarity OR #multidisciplinarity',
                          'transdisciplinary': 'transdisciplinary OR #transdisciplinary OR transdisciplinarity OR #transdisciplinarity'}

    # location to store the target tweets
    save_location = os.path.join('files', 'target_tweets')

    # create folders if not exist
    [create_directory(os.path.join(save_location, k))
     for k in modes_of_research.keys()]

    # collect tweets for each mode of research by using the defined search query
    for mode, query in modes_of_research.iteritems():

        # verbose
        logging.info('Processing mode of research: {}'.format(mode))
        logging.info('Processing query: {}'.format(query))

        # get the last tweet ID (if we have searched for tweets before)
        last_tweet_id = get_last_tweet_id(os.path.join(save_location, mode))

        # create a save name for the tweets
        save_name = '{}-{:%Y%m%d%H%M%S}.txt'.format(mode, datetime.now())

        # search for tweets and save to disk
        search_tweets_from_API(save_name=save_name, save_location=os.path.join(
            save_location, mode), query=query, last_tweet_id=last_tweet_id)

        logging.info('Finished collecting {} tweets\n'.format(mode))
