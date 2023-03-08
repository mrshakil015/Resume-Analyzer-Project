<details>
  <summary><b>Python Flask Virtual Environment Create</b></summary>
  
  Flask is a web framework that provides libraries to build lightweight web applications in python.</br>
</br><b>Install Virtual Environment:</b>
  - virtualenv is considered as the virtual python environment builder which is used to create the multiple python virtual environment side by side. 
  - At first open <code>Visual Studio Code</code> then use following command to install virtual environment:
  
    - <code>pip install virtualenv</code>
  - Once it is installed, we can create the new virtual environment into a folder as given below.
    - <code>python -m venv env</code>
  - To activate the corresponding environment, use the following command on the Windows operating system.
    - <code>.\env\Scripts\activate</code>
  - If your <code>pip</code> is not upgraded then upgrade the <code>pip</code>:
    - <code>python -m pip install --upgrade pip</code>
  - Now install the flask by using the following command:
    - <code>pip install flask</code>
  - After installation now create a first Flask application. Create this application outside the <code>env</code> folder.Like- <code>app.py</code>, you can use any types of name. Write the following lines of code to check the application.
  ```python
from flask import Flask
app = Flask (__name__)

@app.route("/")
def home():
    return "Hello world"
if __name__ == "__main__":
    app.run(debug=True) 
  ```
  - For run this code <code>Select Interpreter</code> press <code>Ctrl+Shipt+P</code>. Then select <code>env</code> interpreter. Like this type- <code>Python 3.10.10('env':venv).\env\Script\python.exe</code>
  - Let's run this python code using this command:
    - <code>python -m flask run</code>
  - To show this output on web browser <code>ctrl+click</code> the following lines in your terminal: <code>Running on http://127.0.0.1:5000</code>
  

</detail>
