# Email Processing
    -> Fetches email from gmail, pushes to postgres table and performs actions based on rules 


# 🛠️ Installation

-> Authenticate and Enable Gmail API. 

-> Create a venv, and install libraries from requirements.txt
    >python -m venv venv_test
    >source venv/bin/activate
    >pip install -r requirements.txt

-> Repo uses Posgres, make sure to install and run posgres (adding sample steps using brew)
    > brew install postgresql
    > CREATE ROLE postgres WITH LOGIN <user_name> PASSWORD '<yourpassword>';
    > brew services start postgresql
    > brew services stop postgresql  (To stop Services)
