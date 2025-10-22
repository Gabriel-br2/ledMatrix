import requests
from datetime import datetime

class GitHub:
    def __init__(self,cfg):
        # begin class with data
        self.user = cfg['Git_hub']['user']  
        self.token = cfg['Git_hub']['token']
        self.url_repos = f'https://api.github.com/users/{self.user}/repos'
        self.auth = {'Authorization': f'token {self.token}'}
        self.today = None
        self.dados_repos = []
        self.commits = []
        self.lost_conection = False

    def get_repo(self):
        # get de repositorys name of the account
        try:
            self.dados_repos = []
            response_repos = requests.get(self.url_repos, headers=self.auth,timeout=5)
            if response_repos.status_code == 200:
                self.data_repos = response_repos.json()
        except Exception as e:
            print('Error in git_hub_Module (get_repo): ',e)

    def diferenca_dias(self, data):
        # make the timeline of commits
        try:
            data_formatada = datetime(data[0], data[1], data[2])
            return abs((self.today - data_formatada).days)
        except Exception as e:
            print('Error in git_hub_Module (format day): ',e)

    def get_commits(self):
        # get the commits of a repository
        try:
            self.commits = []
            self.today = datetime.today()

            for repo in self.data_repos:
                url_commits = f"https://api.github.com/repos/{self.user}/{repo['name']}/commits"
                response_commits = requests.get(url_commits, headers=self.auth)
                if response_commits.status_code == 200:
                    dados_commits = response_commits.json()
                    for commit in dados_commits:
                        data = commit['commit']['author']['date']
                        data = list(data.split('T'))
                        data = list(map(int,list(data[0].split('-'))))

                        self.commits.append(data)
            self.commits = sorted(self.commits, key=self.diferenca_dias, reverse=False)
        except Exception as e:
            print("Error in git_hub_Module (Get commits): ",e)