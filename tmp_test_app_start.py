import os
from pathlib import Path
root = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(root))
os.environ['SCHEDULER_ENABLED'] = 'false'
from backend.app import create_app
app = create_app()
client = app.test_client()
with app.app_context():
    resp = client.get('/admin-panel')
    print('admin-panel', resp.status_code)
    resp2 = client.post('/api/assistant/chat', json={'message': 'Chief minister of Tamil Nadu is C.Joseph Vijay'})
    print('assistant status', resp2.status_code)
    print(resp2.get_json())
