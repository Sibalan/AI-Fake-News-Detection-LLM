import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')

from app import create_app
from models import db
from models.user import User

app = create_app()
app.config.update(TESTING=True, SECRET_KEY='test-secret')
client = app.test_client()

with app.app_context():
    db.drop_all()
    db.create_all()
    admin = User(username='admin', email='admin@test.com', full_name='Admin', is_admin=True, is_active=True)
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()

resp = client.post('/contact', data={'name': 'Jane', 'email': 'jane@example.com', 'message': 'Hello from test'}, follow_redirects=True)
print('contact_status', resp.status_code)
print('contact_body_contains_message', 'Message sent' in resp.get_data(as_text=True))

with client.session_transaction() as sess:
    sess['user_id'] = 1
    sess['is_admin'] = True
    sess['username'] = 'admin'
    sess['email'] = 'admin@test.com'
    sess['full_name'] = 'Admin'

api_resp = client.get('/api/admin/contact-messages')
print('admin_api_status', api_resp.status_code)
print('admin_api_total_unread', api_resp.get_json().get('total_unread'))
print('admin_api_messages_len', len(api_resp.get_json().get('messages', [])))
