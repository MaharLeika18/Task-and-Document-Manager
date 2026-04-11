# Task and Document Manager

A comprehensive task management system built with Flask, Firebase, and Google Calendar integration. Designed for teams to efficiently manage projects, tasks, and documents with a modern, responsive web interface.

## 🌟 Features

### Core Functionality
- **Project Management**: Create, organize, and track projects with different statuses (Current, Upcoming, Finished)
- **Task Management**: Assign tasks with priorities (Low, Medium, High) and track progress (To Do, In Progress, Review, Done)
- **Team Collaboration**: Manage team members and assign tasks to specific users
- **Calendar Integration**: Automatic Google Calendar event creation for project timelines
- **File Management**: Upload and organize project-related documents
- **Real-time Updates**: Live project and task status tracking

### User Management
- **Firebase Authentication**: Secure login with email/password or Google OAuth
- **User Profiles**: Display names, profile pictures, and user management
- **Session Management**: Secure session handling with automatic logout

### User Interface
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Modern UI**: Clean, intuitive interface with gradient themes
- **Interactive Elements**: Modal forms, drag-and-drop ready task management
- **Search Functionality**: Find projects, tasks, and team members quickly

## 🛠️ Technology Stack

### Backend
- **Flask**: Python web framework for robust API development
- **Firebase Admin SDK**: Server-side Firebase integration
- **Google Calendar API**: Calendar event management
- **Google Cloud Firestore**: NoSQL database for data persistence

### Frontend
- **HTML5/CSS3**: Modern markup and responsive styling
- **Vanilla JavaScript**: Client-side interactivity
- **Material Symbols**: Icon library for consistent UI elements
- **Fredoka Font**: Custom typography for enhanced readability

### Infrastructure
- **Google Cloud Platform**: Firebase services and Calendar API
- **Environment Configuration**: Secure credential management
- **Session Storage**: Flask session management

## 📋 Prerequisites

Before running this application, ensure you have:

- **Python 3.8+** installed on your system
- **Google Cloud Project** with Firebase enabled
- **Google Calendar API** enabled
- **Service Account** credentials for Google APIs
- **Firebase Admin SDK** configuration

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/Task-and-Document-Manager.git
cd Task-and-Document-Manager
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Firebase Configuration

#### Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select existing one
3. Enable Authentication and Firestore Database

#### Firebase Web App Configuration
1. In Firebase Console, go to Project Settings > General
2. Scroll to "Your apps" section and click "Add app"
3. Select Web app and register it
4. Copy the Firebase config object

#### Firestore Security Rules
Set up Firestore security rules in Firebase Console:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can read/write their own data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }

    // Projects are accessible to assigned members
    match /projects/{projectId} {
      allow read, write: if request.auth != null &&
        (request.auth.uid in resource.data.assigned_members ||
         request.auth.uid == resource.data.project_maker_uid);
    }
  }
}
```

### 5. Google Calendar API Setup

#### Enable Google Calendar API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Google Calendar API for your project
3. Create credentials (Service Account Key)
4. Download the JSON key file

#### Create Calendar
1. Go to Google Calendar
2. Create a new calendar for the application
3. Share it with your service account email
4. Copy the calendar ID from calendar settings

### 6. Environment Configuration

Create a `.env` file in the root directory:
```env
# Flask Configuration
SECRET_KEY=your-secret-key-here

# Firebase Configuration
FIREBASE_ADMIN_FILE_PATH=firebase-admin.json

# Google Calendar Configuration
COUNCILOG_SERVICE_ACCOUNT_FILE=councilog-960a406ec1c5.json
COUNCILOG_CALENDAR_ID=your-calendar-id@group.calendar.google.com
```

### 7. Firebase Admin SDK Setup
1. Place your Firebase Admin SDK JSON file as `firebase-admin.json` in the root directory
2. Place your Google Service Account JSON file as `councilog-960a406ec1c5.json` in the root directory

### 8. Run the Application
```bash
python app.py
```

The application will be available at `http://127.0.0.1:5000`

## 📖 Usage Guide

### Getting Started
1. **Registration**: Create an account using email/password or Google OAuth
2. **Login**: Sign in to access the dashboard
3. **Dashboard**: Overview of projects and quick navigation

### Managing Projects
1. **Create Project**:
   - Click "Create a project" button
   - Fill in project details (name, description, category, priority)
   - Set deadline and assign team members
   - Add tasks with priorities and assignments
   - Submit to create project and calendar event

2. **View Projects**:
   - Projects are organized in columns: Current, Upcoming, Finished
   - Click on any project card to view task details
   - Switch between Tasks, Backlog, and Reports tabs

3. **Task Management**:
   - Tasks are displayed in kanban-style columns
   - Each task shows priority level and assigned members
   - Tasks can be moved between To Do, In Progress, Review, and Done

### Team Management
- **View Members**: Access team member profiles and contact information
- **Assign Tasks**: Assign team members to specific tasks during project creation
- **User Profiles**: Display names and profile pictures from authentication

### Calendar Integration
- **Automatic Events**: Project creation automatically adds events to Google Calendar
- **Calendar View**: Interactive calendar showing project timelines
- **Event Links**: Direct links to Google Calendar events

### File Management
- **Upload Files**: Upload project-related documents
- **File Organization**: Browse and organize files by project
- **File Types**: Support for various document formats

## 🔌 API Endpoints

### Authentication
- `GET /` - Registration page
- `GET /login` - Login page
- `POST /register/register_user` - User registration
- `POST /login/login_user` - User login
- `GET /logout` - User logout

### Projects
- `GET /projects` - Projects dashboard
- `POST /projects/create_project` - Create new project

### Team Management
- `GET /members` - Team members page

### Calendar
- `GET /calendar` - Calendar view

### Files
- `GET /files` - File management

### Home
- `GET /home` - User dashboard

## 🏗️ Project Structure

```
Task-and-Document-Manager/
├── app.py                      # Main application entry point
├── requirements.txt            # Python dependencies
├── .env                        # Environment configuration
├── firebase-admin.json         # Firebase Admin SDK credentials
├── councilog-960a406ec1c5.json  # Google Service Account credentials
├── app/                        # Main application package
│   ├── __init__.py            # Flask app factory
│   ├── firebase_run.py        # Firebase initialization
│   ├── google_services.py     # Google API integrations
│   ├── session_id_generation.py # Session utilities
│   ├── decorators.py          # Route decorators
│   ├── templates/             # HTML templates
│   │   ├── base.html         # Base template
│   │   ├── base_register.html # Auth base template
│   │   ├── home.html         # Dashboard
│   │   ├── projects.html     # Project management
│   │   ├── members.html      # Team management
│   │   ├── calendar.html     # Calendar view
│   │   ├── files.html        # File management
│   │   ├── login.html        # Login page
│   │   └── register.html     # Registration page
│   └── static/               # Static assets
│       ├── css/
│       │   └── style.css     # Main stylesheet
│       └── js/               # JavaScript files
│           ├── main.js       # Main application logic
│           ├── login.js      # Login functionality
│           ├── register.js   # Registration logic
│           ├── forms.js      # Form handling
│           └── package.json  # Frontend dependencies
├── blueprints/                # Flask blueprints
│   ├── home.py               # Home routes
│   ├── login.py              # Authentication routes
│   ├── register.py           # Registration routes
│   ├── projects.py           # Project management routes
│   ├── members.py            # Team management routes
│   ├── calendar.py           # Calendar routes
│   └── files.py              # File management routes
└── README.md                 # Project documentation
```

## 🔒 Security Features

- **Firebase Authentication**: Secure user authentication with JWT tokens
- **Session Management**: Flask session handling with secure cookies
- **CORS Protection**: Cross-origin resource sharing configuration
- **Input Validation**: Client and server-side form validation
- **Environment Variables**: Sensitive data stored securely
- **Firestore Security Rules**: Database access control

## 🤝 Contributing

We welcome contributions to improve the Task and Document Manager!

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -am 'Add new feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

### Code Style
- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Add comments for complex logic
- Test all new features before submitting

### Reporting Issues
- Use GitHub Issues to report bugs
- Include detailed steps to reproduce
- Provide environment information
- Suggest improvements with clear descriptions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Flask**: Web framework
- **Firebase**: Authentication and database services
- **Google Cloud**: Calendar API and cloud services
- **Material Symbols**: Icon library
- **Fredoka Font**: Typography

## 📞 Support

For support, please:
- Check the [Issues](https://github.com/your-username/Task-and-Document-Manager/issues) page
- Create a new issue with detailed information
- Contact the maintainers

---

**Built with ❤️ for efficient team collaboration**