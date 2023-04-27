import os, random, shutil, requests, zipfile, sys, webbrowser
from github import Github, ContentFile, Commit
from dotenv import load_dotenv
from tkinter.filedialog import askopenfilename
from github.GithubException import GithubException
from requests.exceptions import SSLError
from time import sleep

from print_colour import prRed, prGreen, prPurple, prYellow, print_ansi_colour as prANSI

load_dotenv()
os.system("")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

GITHUB_REPO = "McSaveFiles"

def split(fromfile, toDir, chunkSize=1024*1024*25): 
    """Splits a file into fragments of a specified size (recombined by `join`)"""
    print(f"Splitting file into chunks of size: {int(round(chunkSize/1024))}kb ~{int(round(chunkSize/1024/1024))}mb")
    fileExtension = fromfile.split('.')[-1]
    if not os.path.exists(toDir):                  # caller handles errors
        os.mkdir(toDir)                            # make dir, read/write parts
    else:
        for fname in os.listdir(toDir):            # delete any existing files
            os.remove(os.path.join(toDir, fname)) 
    partNum = 0
    input = open(fromfile, 'rb')                   # use binary mode on Windows
    i = 0

    while 1:                                       # eof=empty string from read
        i += 1
        chunk = input.read(chunkSize)              # get next part <= chunkSize
        if not chunk: break
        partNum  = partNum+1
        filename = os.path.join(toDir, ('part%04d' % partNum))
        fileobj  = open(f"{filename}.{fileExtension}_fragment", 'wb')
        fileobj.write(chunk)
        fileobj.close()                            # or simply open(  ).write(  )
    input.close(  )
    print("Split into ", partNum, " files")
    assert partNum <= 9999                         # join sort fails if 5 digits
    return partNum

def join(fromDir, toFile):
    """Assembles a file from its fragments (created by `split`)"""
    print(f"Joining file fragments. {len(os.listdir(fromDir))} fragments found")

    output = open(toFile, 'wb')

    fromDir = fromDir + "\\" + os.listdir(fromDir)[0]

    parts  = os.listdir(f"{fromDir}")
    parts.sort()
    for filename in parts:
        filepath = os.path.join(fromDir, filename)
        fileobj  = open(filepath, 'rb')
        while 1:
            fileBytes = fileobj.read(1024*1024*25)
            if not fileBytes: break
            output.write(fileBytes)
        fileobj.close()
    output.close()

def extract(zipFile, toPath):
    """Extracts a zip file to a specified path"""
    zipName = zipFile.split('\\')[-1]
    with zipfile.ZipFile(zipFile, 'r') as zip_ref:
        zip_ref.extractall(toPath+"\\"+zipName.split('.')[0])

def construct_zip_from_part_zip(sourcePath, finalPath, deleteOriginal=True):
    """Constructs a zip file from its fragments (created by `split`). Must be in a zip file"""
    zipName = sourcePath.split('\\')[-1]
    zipPath = sourcePath.replace(zipName, '')
    temp = f"temp-{random.randint(10000, 99999)}"
    os.mkdir(f"{zipPath}/{temp}")
    print("Extracting zip fragments")

    with zipfile.ZipFile(sourcePath, 'r') as zip_ref:
        zip_ref.extractall(f"{zipPath}\\{temp}")

    
    print("Joining zip fragments")
    join(f"{zipPath}\\{temp}", finalPath)
    print("Zip fragments joined")

    print("Cleaning Up")
    try: shutil.rmtree(f"{zipPath}\\{temp}")
    except Exception as e: print("Error deleting temp folder: ", e)

    if deleteOriginal:
        try: os.remove(sourcePath)
        except Exception as e: print("Error deleting original zip: ", e)  

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
    """Uploads a directory to a Github repository (creates a new branch with the name of the directory)"""
    if not os.path.exists(directory):
        prRed(f"Directory {directory} does not exist")
        raise Exception(f"Directory {directory} does not exist")

    g = Github(GITHUB_TOKEN)
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
    """Uploads a zip file to a Github repository (creates a new branch with the name of the zip file)"""
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

def download_zip(GITHUB_REPO, branch, zip_path, autoDownload=True):
    """Downloads a zip file from a Github repository
    
    autoDownload: If True, the file will be downloaded automatically. If False, the file will be opened in the browser, and the user will have to download it manually"""
    headers = {
        "Authorization" : f'{GITHUB_TOKEN} ghp_r5***',
        "Accept": '*.*',

    }

    g = Github(GITHUB_TOKEN)
    OWNER = g.get_user().name
    EXT = "zip"

    url = f'https://api.github.com/repos/{OWNER}/{GITHUB_REPO}/{EXT}ball/{branch}'
    

    if autoDownload:
        print(f"Requesting download for {branch} from {GITHUB_REPO}")
        
        for i in range(5):
            r = requests.get(url, headers=headers, stream=True)
            if r.headers.get("Content-Length") is not None: break
            print(f"Retrying... {i+1}/5", end="\r")

        if r.status_code == 200:
            print(f"Request successful, downloading file {branch}.{EXT}")
            with open(f'{zip_path}\\{branch}-download.{EXT}', 'wb') as f:
                total_length = r.headers.get('Content-Length')

                if total_length is None: # no content length header
                    prRed("No content length header. File size will be unknown.")
                    downloaded_kb = 0
                    for data in r.iter_content(chunk_size=4096): # 4096 bytes
                        downloaded_kb += int(round(len(data)/1024))
                        f.write(data)
                        prANSI(f"  {downloaded_kb} kb dowloaded (~{int(round(downloaded_kb/1024))} mb)", 222, end="\r")

                else:
                    dl = 0
                    downloaded_kb = 0
                    total_length = int(total_length)
                    total_length_kb = int(round(total_length / 1024))
                    for data in r.iter_content(chunk_size=4096): # 4096 bytes
                        downloaded_kb += int(round(len(data)/1024))
                        dl += len(data)
                        f.write(data)
                        done = int(50 * dl / total_length) 
                        prANSI(f"  [{'=' * done}{' ' * (50-done)}] {downloaded_kb} kb /{total_length_kb} kb (~{int(round(total_length_kb/1024))} mb)", 222, end="\r")
            prGreen(f"Downloaded {branch} from {GITHUB_REPO} ({downloaded_kb} kb)                                         ")
        else:
            print(r.text)   
            prRed("Error downloading file")
    else:
        prPurple(f"Opening {url} in browser")
        webbrowser.open(url)

def download_and_recombine_branch(branch, final_path):
    """Downloads a branch from a Github repository, and recombines the zip file"""
    download_zip(GITHUB_REPO, branch, final_path)
    construct_zip_from_part_zip(f"{final_path}\\{branch}-download.zip", f"{final_path}\\{branch}.zip") # TODO: Fix path
    prGreen(f"Downloaded and recombined branch {branch}.")
    print("File path:")
    prYellow(f"{final_path}\\{branch}.zip")
    return (f"{final_path}\\{branch}.zip")

download_and_recombine_branch("CreateAstral_SAVE", r"C:\Users\joehb\Documents\Coding\Personal-Python\PyGithub\downloads")