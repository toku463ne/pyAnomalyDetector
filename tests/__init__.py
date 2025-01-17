import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ['SECRET_PATH'] = os.path.join('tests', 'test_secret.yml')