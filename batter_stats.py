# Import needed dependencies
import requests
import pandas as pd
import numpy as np
import scipy.stats as stats
from datetime import date
from bs4 import BeautifulSoup, Comment

# Set current date so we can scrape previous five seasons
today = date.today()

# pull just year from today's date, subtract one from it to get last year
current_year = today.strftime("%Y")
last_year = int(current_year) - 1

# Create list of years for previous 5 seasons
last_five_years = []
for i in range(1,6):
    last_five_years.append(int(current_year) - i)

# Create a list to help create a dataframe from batter statistics data
batter_stats = []

# Create a function to create a dataframe from Baseball Reference tables
for year in last_five_years:
    
    # input URL and use BeautifulSoup to parse through the page
    url = f'https://www.baseball-reference.com/leagues/majors/{year}-standard-batting.shtml'
    soup = BeautifulSoup(requests.get(url).content, 'html.parser')

    # Grab the table element that has batter statistics
    table = BeautifulSoup(soup.select_one('#all_players_standard_batting').find_next(text=lambda x: isinstance(x, Comment)), 'html.parser')


    # Grab data from table and put it into the list created above
    for tr in table.select('tr:has(td)'):
        tds = [td.get_text(strip=True) for td in tr.select('td')]
        tds.append(year)
        batter_stats.append(tds)

# Create dataframe for batter statistics
batter_stats_df = pd.DataFrame(batter_stats)

# Create an empty list to store dataframe header information
header_list = []

# Grab the table header information to use as column headers in our dataframe
for tr in table.select('tr:has(th)'):
    ths = [th.get_text(strip=True) for th in tr.select('th')]
    header_list.append(ths)

# For loop returns a list of lists, and we only need the first list 
df_headers = header_list[0]

# Remove the first item from our headers list, it is the index header that we do not need
df_headers.remove('Rk')
df_headers.append("Year")

# Set column headers equal to our list
batter_stats_df.columns = df_headers

# Change types of columns to numeric for columns with number values
batter_stats_df[['Age', 'R','HR','RBI','SB','BA','PA','OPS','OPS+']] = batter_stats_df[['Age', 'R','HR','RBI','SB','BA','PA','OPS','OPS+']].apply(pd.to_numeric)

# Drop any players with 0 plate appearances to remove null values and change PA type to integer
batter_stats_df.dropna(subset=['PA'], axis = 0 , inplace= True)

# Remove any players with fewer than 100 plate appearances
filtered_batter_stats_df = batter_stats_df[batter_stats_df['PA'] >= 100]

# Select the columns we want for our batter analysis
final_batter_stats_df = filtered_batter_stats_df[['Year','Name','Age','R','HR','RBI','SB','BA','PA','OPS','OPS+','Pos\xa0Summary']]

# Determining Z scores for stats used in fantasy baseball
R_zscores = stats.zscore(final_batter_stats_df['R'])
HR_zscores = stats.zscore(final_batter_stats_df['HR'])
RBI_zscores = stats.zscore(final_batter_stats_df['RBI'])
SB_zscores = stats.zscore(final_batter_stats_df['SB'])/5
BA_zscores = stats.zscore(final_batter_stats_df['BA'])

# Create a DataFrame with Z scores
compare_players_df = pd.DataFrame({
    'Z_R': R_zscores,
    'Z_HR': HR_zscores,
    'Z-RBI': RBI_zscores,
    'Z_SB': SB_zscores,
    'Z_BA': BA_zscores,})

# Create aggregate Z Score columns to merge back into stats DataFrame
compare_players_df['average_z'] = compare_players_df.mean(axis=1)
compare_players_df['std_z'] = compare_players_df.std(axis=1)
compare_players_df['avg_confidence'] = (compare_players_df['average_z'] - compare_players_df['std_z'])
compare_players_df['position'] = final_batter_stats_df['Pos\xa0Summary']
final_compare_players_df = compare_players_df.sort_values(by=['avg_confidence'], ascending=False)

# Add average Z scores and confidence scores to player stats DataFrame
final_batter_stats_df['Average Z'] = ''
final_batter_stats_df['Z Confidence'] = ''
final_batter_stats_df['Average Z'] = final_compare_players_df['average_z']
final_batter_stats_df['Z Confidence'] = final_compare_players_df['avg_confidence']
sorted_final_batter_stats_df = final_batter_stats_df.sort_values(by=['Z Confidence'], ascending=False)

# Remove special characters from names Baseball Reference has
sorted_final_batter_stats_df['Name'] = sorted_final_batter_stats_df['Name'].str.extract('([^\*|#]*)')

# Sort values in an order easy to look through
sorted_final_batter_stats_df = sorted_final_batter_stats_df.sort_values(['Name','Year'], ascending=[True, False])

sorted_final_batter_stats_df.to_csv("/Users/michaelbinger/Documents/Projects/Fantasy-Baseball-Analysis/batter_stats.csv")

