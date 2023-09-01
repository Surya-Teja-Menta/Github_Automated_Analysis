import requests
import os, re,gc
import openai
import nbformat as nbf
import cachetools
import shutil

openai.api_key = "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"

# Initialize cache
cache = cachetools.LRUCache(maxsize=1000)

ext = ['.c', '.cpp', '.cs', '.css', '.go', '.html', 'Dockerfile', '.htm', '.java', '.js', '.kt', '.m', '.php', '.php3',
       '.php4', '.php5', '.pl', '.pm', '.py', '.r', '.rb', '.rs', '.scala', '.scm', '.sql', '.swift', '.vb', '.xml', '.yaml']

def fetch_repositories(username):
    print('fetch_repositories')
    try:
        """
        Fetches the repositories of a GitHub user.

        Args:
            username: The username of the GitHub user.

        Returns:
            A list of repositories or None if the request fails.
        """
        url = "https://api.github.com/users/{}/repos".format(username)
        response = requests.get(url)
        if response.status_code == 200:
            repositories = response.json()
            return repositories
        else:
            return None
    except Exception as e:
        print(e)

def download_repository(repository):
    try:
        """
        Downloads a repository from GitHub.

        Args:
            repository: The repository information.

        Returns:
            The path to the downloaded repository.
        """
        name = repository["name"]
        url = repository["clone_url"]
        os.system("git clone {}".format(url))
        repository_path = os.path.join(os.getcwd(), name)

        for root, directories, files in os.walk(repository_path):
            for filename in files:
                filepath = os.path.join(root, filename)
                extension = os.path.splitext(filename)[1]
                if extension not in ext and extension != '.ipynb':
                    os.remove(filepath)
        return repository_path
    except Exception as e:
        print(e)


def preprocess_code(code):
    try:
        """
        Preprocesses the code by removing comments and unnecessary whitespace.

        Args:
            code: The code to be preprocessed.

        Returns:
            The preprocessed code.
        """
        code = re.sub(r"\/\/.*?$", "", code, flags=re.MULTILINE)
        code = re.sub(r"\/\*.*?\*\/", "", code, flags=re.DOTALL)
        code = re.sub(r"(['\"]{3})(.*?)\1", '', code, flags=re.DOTALL)
        code = re.sub(r"#+\s?(.*)", "", code)
        code = re.sub(r'\s+', ' ', code)
        code = re.sub(r"<!--(.*?)-->", "", code)
        code = re.sub(r"\/\*\*.*?\*\/", "", code, flags=re.DOTALL)
        comments = re.compile(r"//.*?$|/\*.*?\*/|<!--.*?-->|#.*?$", re.MULTILINE)
        code = comments.sub("", code)
        code = code.strip()
        return code
    except Exception as e:
        print(e)
    

def identify_coding_files(repository):
    try:
        """
        Identifies coding files and Jupyter notebooks in a repository.

        Args:
            repository: The path to the repository.

        Returns:
            Two lists: coding_files and notebooks.
        """
        coding_files, notebooks = [], []
        for root, directories, files in os.walk(repository):
            for filename in files:
                filepath = os.path.join(root, filename)
                if os.path.isfile(filepath):
                    extension = os.path.splitext(filename)[1]
                    if extension in ext:
                        coding_files.append(filepath)
                    if extension == '.ipynb':
                        notebooks.append(filepath)
        return coding_files, notebooks
    except Exception as e:
        print(e)

def get_code_from_notebook(notebook_filepath):
    try:
        """
        Extracts code from a Jupyter notebook.

        Args:
            notebook_filepath: The path to the Jupyter notebook file.

        Returns:
            The extracted code as a string.
        """
        notebook = nbf.read(notebook_filepath, as_version=4)
        code = []
        for cell in notebook.cells:
            if cell.cell_type == "code":
                code.append(cell.source)
        return ' '.join(code)
    except Exception as e:
        print(e)


def download_and_preprocess(repository):
    try:
        """
        Downloads a repository, preprocesses the code, and returns the preprocessed code.

        Args:
            repository: The repository information.

        Returns:
            The preprocessed code.
        """
        repository_path = download_repository(repository)
        coding_files, notebooks = identify_coding_files(repository_path)
        notebook_codes = []
        for notebook in notebooks:
            notebook_codes.append(get_code_from_notebook(notebook))

        file_codes = []
        for filepath in coding_files:
            try:
                with open(filepath, "r") as f:
                    code = f.read()
                    file_codes.append(code)
            except UnicodeDecodeError as e:
                print("File corrupted")

        codes = notebook_codes + file_codes
        merged_code = ' '.join(codes)
        preprocessed_code = preprocess_code(merged_code)
        return preprocessed_code
    except Exception as e:
        print(e)
   

def get_merged_codes(repository_codes):
    try:
        """
        Merges the codes from different repositories into a single list.

        Args:
            repository_codes: List of preprocessed codes.

        Returns:
            The merged list of codes.
        """
        mc = []
        for code in repository_codes:
            set_matplotlib_close = []
            for i in code:
                smc = ''.join(code)
            mc.append(smc)
        return mc
    except Exception as e:
        print(e)
    


def split_string_into_list(string, words_per_string):
    print("Max Length:",words_per_string)
    words = string.split()  # Split the string into individual words
    num_strings = len(words) // words_per_string  # Calculate the number of strings needed
    string_list = []
    
    for i in range(num_strings):
        start_index = i * words_per_string
        end_index = (i + 1) * words_per_string
        string_list.append(" ".join(words[start_index:end_index]))
    print('Number of Lists:',len(string_list))
    # Add any remaining words to the last string
    if len(words) % words_per_string != 0:
        string_list.append(" ".join(words[num_strings * words_per_string:]))
    
    return string_list
def get_repo_metrics(code_texts,max_code_length = 2040):

  code_texts = split_string_into_list(code_texts,max_code_length)
  output_list = []
  for i,code_text in enumerate(code_texts):
    prompt = """Analyse Code and measure performance and complexity\n
    provide the output as
    list of all Programming Languages that are used in the code: score of associated coding level of each Programming Language out of 10,
    Time Complexity: score out of 10
    Space Complexity: score out of 10
    Overall Technical Complexity: score out of 10
    Rule: 0 means bad and 10 means good
    Provide the output in only Json Format and don't provide any else
    Code = 
      
    """

    input_text = prompt + code_text

    # Truncate code snippet to fit within the context limit
    truncated_code = input_text[:max_code_length]
    messages = [{'role':'user','content':input_text}]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages = messages,
        temperature = 0.7
    )

    output = response.choices[0].message['content']
    output_list.append(output)
    # print(output)
   
  return output_list



def run(username = "webcodify"):
    print('run')
    repositories = fetch_repositories(username)
    repository_codes = []
    for repository in repositories:
        repository_code = cache.get(repository["name"])
        if repository_code is None:
            repository_code = download_and_preprocess(repository)
            cache[repository["name"]] = repository_code
        repository_codes.append(repository_code)


    repository_codes = get_merged_codes(repository_codes)

    repository_codes = [preprocess_code(code) for code in repository_codes]

    repository_codes = get_chunks(repository_codes)


    repositories = fetch_repositories('webcodify')
    QM=[]
    for i,code in enumerate(repository_codes):
        if code != '': 
            QM.append(get_repo_metrics(code))
        else:
            QM.append(0)
    print([rep['name'] for rep in repositories])
    complex_repository = repositories[QM.index(max(QM))]['name']
    complexity_score = (max(QM)/20)*100
    gc.collect()
    for rep in repositories:
        shutil.rmtree(rep['name'])
    return f"Complex Repo is {complex_repository} and its score {complexity_score}"


