import os, random, shutil
from github import Github, ContentFile, Commit
from dotenv import load_dotenv
from tkinter.filedialog import askopenfilename
from github.GithubException import GithubException
from requests.exceptions import SSLError
from time import sleep

from print_colour import prRed, prGreen, prPurple, prYellow
from split_merge import split

load_dotenv()

token = os.environ.get("GITHUB_TOKEN")

GITHUB_REPO = "McSaveFiles"

def create_branch(repo, branch_name, branch_reference="master"):
    """Creates a branch from a reference branch in a Github repository"""
    sb = repo.get_branch(branch_reference)
    print(f"Creating branch \033[95m{branch_name}\033[00m")
    try:
        repo.create_git_ref(ref='refs/heads/' + branch_name, sha=sb.commit.sha)
    except GithubException as e:
        print("\033[91mBranch already exists\033[00m, skipping creation")

def upload_file(repo, file_path, branch):
    """Uploads a file to a Github repository"""
    name = file_path.split('\\')[-1]

    log_text = f"Uploading {name} to {branch}"

    with open(file_path, 'rb') as file:
        content = file.read()

    

    while True:
        try:
            print(f"{log_text} 📶", end="\r")
            repo.create_file(f"{name}", f"Uploaded {name}", content, branch=branch)
            print(f"{log_text} ✅               ")
            break
        except SSLError as e:
            print(f"{log_text} ❌ {e}           ")

def upload_directory(directory, branch=None):

    if not os.path.exists(directory):
        prRed(f"Directory {directory} does not exist")
        raise Exception(f"Directory {directory} does not exist")

    g = Github(token)
    repo = g.get_user().get_repo(GITHUB_REPO)
    i = 0
    if branch == None: branch = directory.split('/')[-1]

    prGreen(f"Uploading {branch} to Github")

    create_branch(repo, branch, branch_reference="empty")

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            upload_file(repo, file_path, branch)

            i += 1
    prGreen(f"Uploaded Folder {branch}")
    print(f"Link to GitHub Repo:")
    link = f"https://github.com/{g.get_user().name}/{GITHUB_REPO}/tree/{branch}"
    prYellow(link)
    return {
        "link": link,
    }

def upload_zip(zip_path, branch=None):
    zipName = zip_path.split("/")[-1]
    zipPath = zip_path.replace("/"+zipName, '')
    zipName = zipName.replace(".zip", '')
    temp = f"temp-{random.randint(10000, 99999)}"

    if branch == None: branch = zipName

    path = os.path.join(zipPath, temp)
    os.mkdir(path)
    path = os.path.join(path, zipName)
    os.mkdir(path)
    split(zip_path, path)
    upload_directory(path, branch)
    
    sleep(5)

    try: shutil.rmtree(os.path.join(zipPath, temp))
    except Exception as e: print("Error deleting temp folder: ", e)



#upload_zip(askopenfilename())