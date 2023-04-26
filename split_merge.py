import sys, os, zipfile, random, shutil

readSize = 1024*1024*25

def split(fromfile, toDir, chunkSize=1024*1024*25): 
    print("Splitting file into chunks of size: ", chunkSize)
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
        fileobj  = open(f"{filename}.zip_fragment", 'wb')
        fileobj.write(chunk)
        fileobj.close()                            # or simply open(  ).write(  )
    input.close(  )
    print("Split into ", partNum, " files")
    assert partNum <= 9999                         # join sort fails if 5 digits
    return partNum

def join(fromDir, toFile):
    output = open(toFile, 'wb')
    parts  = os.listdir(fromDir)
    parts.sort(  )
    for filename in parts:
        filepath = os.path.join(fromDir, filename)
        fileobj  = open(filepath, 'rb')
        while 1:
            fileBytes = fileobj.read(readSize)
            if not fileBytes: break
            output.write(fileBytes)
        fileobj.close(  )
    output.close(  )

def extract(zipFile, toPath):
    zipName = zipFile.split('/')[-1]
    with zipfile.ZipFile(zipFile, 'r') as zip_ref:
        zip_ref.extractall(toPath+"/"+zipName.split('.')[0])

def construct_zip_from_zip(sourcePath, finalPath):
    zipName = sourcePath.split('/')[-1]
    zipPath = sourcePath.replace(zipName, '')
    temp = f"temp-{random.randint(10000, 99999)}"
    os.mkdir(f"{zipPath}/{temp}")
    with zipfile.ZipFile(sourcePath, 'r') as zip_ref:
        zip_ref.extractall(f"{zipPath}/{temp}")
    join(f"{zipPath}/{temp}", finalPath)
    try: shutil.rmtree(f"{zipPath}/{temp}")
    except Exception as e: print("Error deleting temp folder: ", e)

