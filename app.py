from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_swagger_ui import get_swaggerui_blueprint
from datetime import datetime
import os

app = Flask(__name__)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///incubator.db')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
db = SQLAlchemy(app)


class User(db.Model):
    UserID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100))
    PhoneNumber = db.Column(db.String(15))
    usages = db.relationship('Usage', backref='user', lazy=True)


class Usage(db.Model):
    UsageID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('user.UserID'), nullable=False)
    UsageDetails = db.Column(db.String(255))
    IncubatorType = db.Column(db.String(50))
    StartTime = db.Column(db.DateTime)
    EndTime = db.Column(db.DateTime)
    Comment = db.Column(db.String(255))
    Status = db.Column(db.String(50))


# Ensure the database tables are created within the application context
with app.app_context():
    db.create_all()


@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{
        'UserID': user.UserID,
        'Name': user.Name,
        'PhoneNumber': user.PhoneNumber,
        'Usages': [{
            'UsageID': usage.UsageID,
            'UsageDetails': usage.UsageDetails,
            'IncubatorType': usage.IncubatorType,
            'StartTime': usage.StartTime,
            'EndTime': usage.EndTime,
            'Comment': usage.Comment,
            'Status': usage.Status
        } for usage in user.usages]
    } for user in users])


@app.route('/users', methods=['POST'])
def add_user():
    data = request.get_json()
    new_user = User(UserID=data['UserID'], Name=data['Name'], PhoneNumber=data['PhoneNumber'])
    db.session.add(new_user)
    for usage in data['Usages']:
        new_usage = Usage(
            UsageID=usage['UsageID'],
            UserID=data['UserID'],
            UsageDetails=usage['UsageDetails'],
            IncubatorType=usage['IncubatorType'],
            StartTime=datetime.strptime(usage['StartTime'], '%Y-%m-%d %H:%M') if usage['StartTime'] else None,
            EndTime=datetime.strptime(usage['EndTime'], '%Y-%m-%d %H:%M') if usage['EndTime'] else None,
            Comment=usage['Comment'],
            Status=usage['Status']
        )
        db.session.add(new_usage)
    db.session.commit()
    return jsonify({'message': 'User and usages added successfully'}), 201


@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    user = User.query.get_or_404(user_id)
    user.Name = data.get('Name', user.Name)
    user.PhoneNumber = data.get('PhoneNumber', user.PhoneNumber)
    db.session.commit()
    return jsonify({'message': 'User updated successfully'})


@app.route('/usages/<int:usage_id>', methods=['PUT'])
def update_usage(usage_id):
    data = request.get_json()
    usage = Usage.query.get_or_404(usage_id)
    usage.UsageDetails = data.get('UsageDetails', usage.UsageDetails)
    usage.IncubatorType = data.get('IncubatorType', usage.IncubatorType)
    usage.StartTime = datetime.strptime(data['StartTime'], '%Y-%m-%d %H:%M') if data.get(
        'StartTime') else usage.StartTime
    usage.EndTime = datetime.strptime(data['EndTime'], '%Y-%m-%d %H:%M') if data.get('EndTime') else usage.EndTime
    usage.Comment = data.get('Comment', usage.Comment)
    usage.Status = data.get('Status', usage.Status)
    db.session.commit()
    return jsonify({'message': 'Usage updated successfully'})


@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    for usage in user.usages:
        db.session.delete(usage)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User and usages deleted successfully'})


@app.route('/usages/<int:usage_id>', methods=['DELETE'])
def delete_usage(usage_id):
    usage = Usage.query.get_or_404(usage_id)
    db.session.delete(usage)
    db.session.commit()
    return jsonify({'message': 'Usage deleted successfully'})


# Serve Swagger UI
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Incubator API"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


# Serve the index.html at the root URL
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


if __name__ == '__main__':
    app.run(debug=True)
