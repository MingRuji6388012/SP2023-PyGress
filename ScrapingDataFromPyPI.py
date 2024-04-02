# import pandas as pd
# import requests
# from bs4 import BeautifulSoup
# import unicodedata

# def scrape_pypi_info(project_name):
#     """Scrape PyPI project page for description, tags, and stars."""
#     description = "No Description"
#     tags = ["No Tag"]
#     stars = ""
#     url = f"https://pypi.org/project/{project_name}/"
#     print(f"Scraping data from {url}")
#     response = requests.get(url)
#     if response.status_code == 200:
#         soup = BeautifulSoup(response.content, 'html.parser')
#         # Scrape description
#         description_tag = soup.find('div', class_='project-description')
#         if description_tag:
#             description = description_tag.get_text(strip=True)
#             print(f"Description found for {project_name}\n")
#             description = remove_non_unicode(description)
#         # Scrape tags
#         tags_container = soup.find('p', class_='tags')
#         if tags_container:
#             keyword_tags = tags_container.find_all('span', class_='package-keyword')
#             tags = [tag.get_text(strip=True) for tag in keyword_tags]
#             print(f"Tags found for {project_name}: {tags}\n\n\n")
#             tags = [remove_non_unicode(tag) for tag in tags]
#             tags = [tag.strip(',') for tag in tags]
#             tags = [tag for tag in tags if tag]
#         # Scrape stars count
#         stars_tag = soup.find('span', {'data-github-repo-info-target': 'stargazersCount'})
#         if stars_tag:
#             stars_text = stars_tag.text.strip()
#             if stars_text:
#                 stars = int(stars_text)
#                 print(f"Stars found for {project_name}: {stars}")
#             else:
#                 print(f"Stars information not available for {project_name}.")
#                 stars = ""
#         else:
#             print(f"Stars information not available for {project_name}.")
#     return description, tags, stars, url

# def remove_non_unicode(text):
#     return ''.join(char for char in text if unicodedata.category(char)[0] != 'C')

# # Read DataPyPI.csv
# csv_path = 'DataPyPI.csv'
# df = pd.read_csv(csv_path)

# # Add columns for Stars, PyPIURL, and ProjectURL
# df['Stars'] = ""
# df['PyPIURL'] = ""
# df['ProjectURL'] = ""

# # Iterate over each row
# for index, row in df.iterrows():
#     project_name = row['ProjectName']
#     github_url = row['URL']
#     # Get stars, description, and tags of the GitHub repository from PyPI
#     description, tags, stars, pypi_url = scrape_pypi_info(project_name)
#     # Update DataFrame with scraped data
#     df.at[index, 'Description'] = description
#     df.at[index, 'Tags'] = str(tags)  # Convert list to string for CSV
#     df.at[index, 'Stars'] = stars
#     df.at[index, 'PyPIURL'] = pypi_url
#     df.at[index, 'ProjectURL'] = github_url

# # Save the updated DataFrame back to CSV
# df.to_csv('DataPyPI_All.csv', index=False)
# print("Data saved to DataPyPI_All.csv")

# import pandas as pd
# import requests
# from bs4 import BeautifulSoup
# import unicodedata
# from datetime import datetime

# def scrape_libraries_io_info(project_name):
#     """Scrape Libraries.io project page for description, tags, stars, and latest commit."""
#     description = "No Description"
#     tags = ["No Tag"]
#     stars = ""
#     latest_commit = ""

#     url = f"https://libraries.io/pypi/{project_name}"
#     print(f"Scraping data from {url}")
#     response = requests.get(url)
#     if response.status_code == 200:
#         soup = BeautifulSoup(response.content, 'html.parser')

#         # Scrape description
#         description_tag = soup.find('div', class_='col-md-8').find('p')
#         if description_tag:
#             description = description_tag.get_text(strip=True)
#             print(f"Description found for {project_name}: {description_tag}\n")
#             description = remove_non_unicode(description)

#         # Scrape tags
#         keywords_tag = soup.find('dt', string='Keywords')
#         if keywords_tag:
#             tags_container = keywords_tag.find_next_sibling('dd')
#             if tags_container:
#                 keyword_tags = tags_container.find_all('a')
#                 tags = [tag.get_text(strip=True) for tag in keyword_tags]
#                 print(f"Tags found for {project_name}: {tags}\n\n\n")
#                 tags = [remove_non_unicode(tag) for tag in tags]
#                 tags = [tag.strip(',') for tag in tags]
#                 tags = [tag for tag in tags if tag]

#         # Scrape stars count
#         stars_tag = soup.find('dt', string='Stars')
#         if stars_tag:
#             stars_container = stars_tag.find_next_sibling('dd')
#             print(f"stars_container: {stars_container}")
#             if stars_container:
#                 stars = stars_container.find('a').text.strip()
#                 print(f"Stars found for {project_name}: {stars}")

#         # Scrape latest commit
#         latest_commit_tag = soup.find('dt', string='Latest release')
#         if latest_commit_tag:
#             latest_commit_container = latest_commit_tag.find_next_sibling('dd')
#             print(f"latest_commit_container: {latest_commit_container}")
#             if latest_commit_container:
#                 latest_commit = latest_commit_container.find('time')['datetime']
#                 print(f"Latest commit found for {project_name}: {latest_commit}")

#     return description, tags, stars, latest_commit, url

# def remove_non_unicode(text):
#     return ''.join(char for char in text if unicodedata.category(char)[0] != 'C')

# # Read DataPyPI.csv
# csv_path = 'DataPyPI.csv'
# df = pd.read_csv(csv_path)

# # Add columns for Description, Tags, Stars, LatestCommit, and PyPIURL
# df['Description'] = ""
# df['Tags'] = ""
# df['Stars'] = ""
# df['LatestCommit'] = ""
# df['PyPIURL'] = ""

# # Iterate over each row
# for index, row in df.iterrows():
#     project_name = row['ProjectName']

#     # Get description, tags, stars, latest commit, and PyPI URL of the project
#     description, tags, stars, latest_commit, pypi_url = scrape_libraries_io_info(project_name)

#     # Update DataFrame with scraped data
#     df.at[index, 'Description'] = description
#     df.at[index, 'Tags'] = str(tags)  # Convert list to string for CSV
#     df.at[index, 'Stars'] = stars
#     df.at[index, 'LatestCommit'] = latest_commit
#     df.at[index, 'PyPIURL'] = pypi_url

# # Save the updated DataFrame back to CSV
# df.to_csv('DataPyPI_All.csv', index=False)
# print("Data saved to DataPyPI_All.csv")


# Set your GitHub personal access token here
# import pandas as pd
# import requests
# from bs4 import BeautifulSoup
# import github3

# def get_stargazers(github_url, token):
#     """Retrieve stargazers for a GitHub repository."""
#     stargazers = []
#     # Extract owner and repository name from GitHub URL
#     owner, repo = github_url.split('/')[-2:]
#     # Initialize GitHub session with personal access token
#     gh = github3.login(token=token)
#     if gh:
#         try:
#             # Retrieve repository object
#             repo_obj = gh.repository(owner, repo)
#             # Get stargazers for the repository
#             for stargazer in repo_obj.stargazers():
#                 stargazers.append(stargazer.login)
#             return stargazers
#         except github3.exceptions.NotFoundError:
#             print(f"GitHub repository {owner}/{repo} not found.")
#             return []
#         except github3.exceptions.ForbiddenError:
#             print("GitHub API rate limit exceeded. Try again later.")
#             return []
#     else:
#         print("Failed to authenticate with GitHub.")
#         return []

# # Set your GitHub personal access token here
# github_token = "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"

# # Read DataPyPI.csv
# csv_path = 'DataPyPI.csv'
# df = pd.read_csv(csv_path)

# # Add a column for Stargazers
# df['Stargazers'] = ""

# # Iterate over each row
# for index, row in df.iterrows():
#     github_url = row['URL']
#     print(f"Exploring GitHub repository: {github_url}")
#     # Retrieve stargazers for the GitHub repository
#     stargazers = get_stargazers(github_url, github_token)
#     # Update DataFrame with stargazers data
#     df.at[index, 'Stargazers'] = ", ".join(stargazers)
#     print(f"Stars found: {len(stargazers)}")

# # Save the updated DataFrame back to CSV
# df.to_csv('DataPyPI_WithStargazers.csv', index=False)
# print("Data saved to DataPyPI_WithStargazers.csv")

import pandas as pd
import requests
from bs4 import BeautifulSoup
import unicodedata
import github3
import time

def scrape_pypi_info(project_name):
    """Scrape PyPI project page for description, tags, and stars."""
    description = "No Description"
    tags = ["No Tag"]
    url = f"https://pypi.org/project/{project_name}/"
    print(f"Scraping data from {url}")
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        # Scrape description
        description_tag = soup.find('div', class_='project-description')
        if description_tag:
            description = description_tag.get_text(strip=True)
            print(f"Description found for {project_name}")
            description = remove_non_unicode(description)
        # Scrape tags
        tags_container = soup.find('p', class_='tags')
        if tags_container:
            keyword_tags = tags_container.find_all('span', class_='package-keyword')
            tags = [tag.get_text(strip=True) for tag in keyword_tags]
            print(f"Tags found for {project_name}: {tags}")
            tags = [remove_non_unicode(tag) for tag in tags]
            tags = [tag.strip(',') for tag in tags]
            tags = [tag for tag in tags if tag]
    return description, tags, url

def remove_non_unicode(text):
    return ''.join(char for char in text if unicodedata.category(char)[0] != 'C')

def get_stargazers(github_url, token, request_count):
    """Retrieve stargazers for a GitHub repository."""
    stargazers = []
    # Extract owner and repository name from GitHub URL
    owner, repo = github_url.split('/')[-2:]
    # Initialize GitHub session with personal access token
    gh = github3.login(token=token)
    if gh:
        try:
            # Retrieve repository object
            repo_obj = gh.repository(owner, repo)
            request_count += 1
            print(f"request_count: {request_count}")
            # Get stargazers for the repository
            if request_count % 900 == 0:
                print("Pausing for 10 mins to prevent exceeding rate limit...")
                time.sleep(600)  # Sleep for 10 mins
            for stargazer in repo_obj.stargazers():
                stargazers.append(stargazer.login)
            return stargazers, request_count
        except github3.exceptions.NotFoundError:
            print(f"GitHub repository {owner}/{repo} not found.")
            return [], request_count
        except github3.exceptions.ForbiddenError:
            print("GitHub API rate limit exceeded. Try again later.")
            return [], request_count
        except github3.exceptions.UnavailableForLegalReasons:
            print(f"GitHub repository {owner}/{repo} unavailable due to DMCA takedown notice.")
            return [], request_count
    else:
        print("Failed to authenticate with GitHub.")
        return [], request_count

# Set your GitHub personal access token here
github_token = ""

# Read DataPyPI.csv
csv_path = 'DataPyPI.csv'
df = pd.read_csv(csv_path)

# Add columns for Description, Tags, PyPIURL, ProjectURL, and Stargazersฆฆ
df['Description'] = ""
df['Tags'] = ""
df['PyPIURL'] = ""
df['ProjectURL'] = ""
df['Stargazers'] = ""

# Initialize request count
request_count = 0

# Iterate over each row
for index, row in df.iterrows():
    project_name = row['ProjectName']
    github_url = row['URL']
    # Get description, tags, and PyPI URL from PyPI
    description, tags, pypi_url = scrape_pypi_info(project_name)
    # Update DataFrame with PyPI scraped data
    df.at[index, 'Description'] = description
    df.at[index, 'Tags'] = str(tags)  # Convert list to string for CSV
    df.at[index, 'PyPIURL'] = pypi_url
    df.at[index, 'ProjectURL'] = github_url

    # Retrieve stargazers for the GitHub repository
    stargazers, request_count = get_stargazers(github_url, github_token, request_count)
    # Update DataFrame with GitHub stargazers data
    df.at[index, 'Stargazers'] = ", ".join(stargazers)
    print(f"Stars found: {len(stargazers)}\n")

# Save the updated DataFrame back to CSV
df.to_csv('DataPyPI_All.csv', index=False)
print("Data saved to DataPyPI_All.csv")
