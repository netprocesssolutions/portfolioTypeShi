"""
Jordan Taylor - Personal Portfolio Website & Action Item Tracker
"""

from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from models import db, bcrypt, User
import os


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

    # Database configuration
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///tracker.db')
    # Railway PostgreSQL uses postgres:// but SQLAlchemy needs postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    csrf = CSRFProtect(app)

    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'tracker.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register tracker blueprint
    from tracker import tracker_bp
    app.register_blueprint(tracker_bp, url_prefix='/tracker')

    # Create tables on first request
    with app.app_context():
        db.create_all()

    # ---- Portfolio Routes (unchanged) ----

    @app.route('/')
    def home():
        return render_template('index.html',
                             profile=PROFILE,
                             education=EDUCATION,
                             experience=EXPERIENCE[:2],
                             skills=SKILLS)

    @app.route('/resume')
    def resume():
        return render_template('resume.html',
                             profile=PROFILE,
                             education=EDUCATION,
                             experience=EXPERIENCE,
                             leadership=LEADERSHIP,
                             skills=SKILLS)

    @app.route('/projects')
    def projects():
        return render_template('projects.html',
                             profile=PROFILE,
                             projects=PROJECTS)

    @app.route('/contact')
    def contact():
        return render_template('contact.html',
                             profile=PROFILE)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html', profile=PROFILE), 404

    return app


# ---- Portfolio Data ----

PROFILE = {
    'name': 'Jordan Taylor',
    'title': 'Process Engineer',
    'tagline': 'Chemical Process Engineer | Data-Driven Problem Solver | Continuous Improvement Leader',
    'location': 'Chattanooga, TN',
    'email': 'me@jordantaylor.online',
    'phone': '865-454-9470',
    'summary': 'Chemical Process Engineer with hands-on manufacturing experience across automotive, plastics, and flooring industries. Passionate about leveraging data analytics, process optimization, and cross-functional collaboration to drive measurable improvements in quality, efficiency, and operational excellence.',
    'linkedin': 'https://linkedin.com/in/jordantaylor',
    'github': 'https://github.com/jordantaylor',
}

EDUCATION = [
    {
        'institution': 'University of Tennessee, Chattanooga',
        'location': 'Chattanooga, TN',
        'degree': 'Bachelor of Science in Chemical Engineering',
        'graduation': 'December 2023',
        'gpa': '3.790 / 4.0',
        'major_gpa': '3.759 / 4.0',
        'honors': [
            "Dean's List (x7)",
            'National AP Scholar',
            'Tau Beta Pi Honors Society'
        ],
        'coursework': [
            'Thermodynamics',
            'Fluid Mechanics',
            'Chemical System Design',
            'Chemical Reactor Design',
            'Computer Programming',
            'Organic Chemistry',
            'Materials Science'
        ]
    }
]

EXPERIENCE = [
    {
        'company': 'Shaw Flooring',
        'title': 'Process Engineer',
        'location': 'Dalton, GA',
        'dates': 'July 2025 – Present',
        'current': True,
        'highlights': [
            'Led continuous improvement initiatives for Coater 1, improving uptime, line speed stability, and product quality by systematically reducing delamination failures, loose-edge defects, and other quality concerns.',
            'Pioneered SBR latex compounding pipeline optimization efforts, coordinating maintenance, operations, and compounding teams to diagnose hard-piping restrictions, valve failures, and flow-rate variability. Primary accountability for VAE to SBR latex transition.',
            'Designed and implemented comprehensive digital analytics pipelines integrating Excel/VBA automation, MS Access relational databases, and Power BI dashboards to centralize shift-report, downtime, scrap, and defect data.',
            'Created structured operator-training matrices and competency tracking systems for critical coating and roll-up stations across three shifts, improving skill coverage and reducing onboarding time.',
            'Designed standardized operator engagement meetings for ergonomics, equipment usability, and process improvement ideas, ensuring frontline insights directly drive engineering actions.'
        ]
    },
    {
        'company': 'Woodbridge - Formed Plastics',
        'title': 'Process Engineer',
        'location': 'Chattanooga, TN',
        'dates': 'July 2024 – July 2025',
        'current': False,
        'highlights': [
            'Primary point of accountability for all material, process, and quality-related issues in a fast-paced EPP manufacturing environment involving daily troubleshooting related to quality specifications, part appearances, and equipment maintenance.',
            'Directly responsible for continuous improvement efforts for high-fallout part numbers involving changes to tool design, setup instructions, process parameters, and equipment health analysis.',
            'Led a special task force across three production shifts to increase overall equipment efficiency, forming specialized units to target cycle time and availability challenges.',
            'Used CAD software (Teamcenter Visualization) for tooling layout and launch qualification standards including mould cavity placement and initial capability studies.'
        ]
    },
    {
        'company': 'Volkswagen Group of America',
        'title': 'Quality and Failure Analysis Intern',
        'location': 'Chattanooga, TN',
        'dates': 'January 2024 – July 2024',
        'current': False,
        'highlights': [
            'Worked with cross-functional teams to solve production issues identified through in-house audits and warranty field claims, escalating issues to appropriate forums for speedy resolution.',
            'Created and maintained an intradepartmental database to quantitatively track cross-functional team topics, progress updates, and auto-format meeting minutes.',
            'Assisted a special task force analyzing large-volume field failures, developing solutions and countermeasures, and tracking issues through communication with internal and external stakeholders.'
        ]
    },
    {
        'company': 'University of Tennessee, Chattanooga',
        'title': 'Teaching Assistant - Chemical Process Operations Laboratory',
        'location': 'Chattanooga, TN',
        'dates': 'August 2023 – December 2023',
        'current': False,
        'highlights': [
            'Demonstrated and aided students with operation of distillation column and performed troubleshooting for unit operations (absorption column, heat exchanger, etc.).',
            'Created detailed step-by-step methods for continuous operation of the distillation column and hypothetical experimental guides for students.',
            'Performed lab manager duties: reordering supplies, providing technical support, and overseeing compliance with lab safety regulations.'
        ]
    }
]

LEADERSHIP = [
    {
        'role': 'Team Captain',
        'organization': 'AIChE Chem-E-Car Team',
        'dates': 'August 2023 – December 2023',
        'highlights': [
            'Coordinated creation of an entirely new car design, delegating team captains and subdividing workload into task-specific categories.',
            'Implemented policies to qualify Chem-E-Car participation as an "experiential learning" course credit.',
            'Increased networking with underclassmen and added 10 new members (compared to only 1 the previous year).'
        ]
    },
    {
        'role': 'Stopping Reaction Team Lead',
        'organization': 'AIChE Chem-E-Car Team',
        'dates': 'August 2022 – August 2023',
        'highlights': [
            'Directed a team of chemical engineers in orchestrating and calibrating a chemical reaction to stop a miniature car powered by a chemical battery.',
            'Presented research to chemical engineering professionals from schools across the Southeast.',
            'Created a hydrogen fuel cell and learned coding techniques for Arduino (C++) and Raspberry Pi (Python) sensor integration.'
        ]
    },
    {
        'role': 'Supplemental Instruction Program Assistant',
        'organization': 'UTC Center for Academic Success/Advisement',
        'dates': 'August 2022 – December 2022',
        'highlights': [
            'Corresponded with SI Leaders to offer leadership guidance on lesson plans and classroom management techniques.',
            'Led weekly staff meetings ranging from professional development training to administrative tasks.',
            'Helped obtain CRLA certification by demonstrating training expectations to SI Leaders.'
        ]
    }
]

SKILLS = {
    'technical': [
        {'name': 'VBA / Excel Automation', 'level': 100},
        {'name': 'Custom Software Development', 'level': 100},
        {'name': 'Data Analysis', 'level': 100},
        {'name': 'Statistical Methods', 'level': 100},
        {'name': 'Written Procedures', 'level': 95},
        {'name': 'Python', 'level': 90},
        {'name': 'Presentational Speaking', 'level': 85},
        {'name': 'MS Access / SQL', 'level': 80},
        {'name': 'CHEMCAD', 'level': 70},
        {'name': 'C++ (Arduino)', 'level': 60},
        {'name': 'Spanish', 'level': 60},
    ],
    'engineering': [
        'Process Optimization',
        'Root Cause Analysis',
        'Statistical Process Control',
        'Quality Systems',
        'Continuous Improvement',
        'Equipment Troubleshooting',
        'Standard Work Documentation',
        'Cross-Functional Leadership'
    ],
    'certifications': [
        'AutoCAD Certification Course',
        'CRLA Level 1 Peer Educator Certification'
    ]
}

PROJECTS = [
    {
        'id': 'analytics-pipeline',
        'title': 'Digital Analytics Pipeline',
        'company': 'Shaw Flooring',
        'category': 'Data Engineering',
        'description': 'Designed and implemented a comprehensive digital analytics system integrating multiple data sources into actionable insights for operations leadership.',
        'details': [
            'Built Excel/VBA automation tools to streamline data collection from shift reports',
            'Developed MS Access relational database to centralize downtime, scrap, and defect data',
            'Created Power BI dashboards for real-time visualization of production metrics',
            'Integrated Python tools via API for advanced data processing and analysis',
            'Enabled data-driven decision making for continuous improvement initiatives'
        ],
        'technologies': ['Python', 'VBA', 'MS Access', 'Power BI', 'API Integration'],
        'impact': 'Centralized data from three shifts, enabling leadership to identify and prioritize improvement opportunities'
    },
    {
        'id': 'oee-taskforce',
        'title': 'Overall Equipment Efficiency Task Force',
        'company': 'Woodbridge - Formed Plastics',
        'category': 'Continuous Improvement',
        'description': 'Led a cross-functional task force to systematically improve overall equipment efficiency across all production shifts.',
        'details': [
            'Formed specialized units targeting cycle time and availability challenges',
            'Created processes for tracking, sharing, and standardizing results across shifts',
            'Analyzed data from production systems to identify highest-impact problems',
            'Developed standardized procedures for changeover and equipment maintenance',
            'Coordinated team members from multiple departments on all three shifts'
        ],
        'technologies': ['Data Analysis', 'Process Mapping', 'Standard Work', 'Cross-Functional Leadership'],
        'impact': 'Measurable improvement in OEE through systematic identification and elimination of losses'
    },
    {
        'id': 'quality-database',
        'title': 'Quality Issue Tracking Database',
        'company': 'Volkswagen Group of America',
        'category': 'Software Development',
        'description': 'Created an intradepartmental database system for tracking cross-functional team topics and automating meeting documentation.',
        'details': [
            'Designed database schema for quantitative tracking of quality issues',
            'Built user interface for progress updates and status tracking',
            'Implemented auto-formatting system for meeting minutes generation',
            'Enabled historical analysis of issue resolution timelines',
            'Facilitated communication between cross-functional teams'
        ],
        'technologies': ['MS Access', 'VBA', 'Database Design', 'UI Development'],
        'impact': 'Streamlined cross-functional communication and improved visibility of issue resolution progress'
    },
    {
        'id': 'hydrogen-fuel-cell',
        'title': 'Hydrogen Fuel Cell Vehicle',
        'company': 'AIChE Chem-E-Car Competition',
        'category': 'Engineering Design',
        'description': 'Designed and built a miniature car powered by a hydrogen fuel cell with a chemically-controlled stopping mechanism.',
        'details': [
            'Created hydrogen fuel cell power system for vehicle propulsion',
            'Developed iodine clock reaction for precise stopping distance control',
            'Programmed Arduino (C++) for sensor integration and control logic',
            'Implemented Raspberry Pi (Python) for data logging and calibration',
            'Presented technical research to engineering professionals at regional conference'
        ],
        'technologies': ['Chemical Engineering', 'C++', 'Python', 'Arduino', 'Raspberry Pi', 'Electrochemistry'],
        'impact': 'Competed at AIChE Southern Regional Conference 2023'
    },
    {
        'id': 'training-matrix',
        'title': 'Operator Training & Competency System',
        'company': 'Shaw Flooring',
        'category': 'Process Improvement',
        'description': 'Developed structured training matrices and competency tracking systems for critical production stations.',
        'details': [
            'Mapped skill requirements for coating and roll-up stations',
            'Created competency assessment criteria and tracking tools',
            'Designed training progression pathways for new operators',
            'Implemented cross-shift standardization of training materials',
            'Built operator engagement framework for continuous feedback'
        ],
        'technologies': ['Training Design', 'Process Documentation', 'Standard Work', 'Change Management'],
        'impact': 'Reduced onboarding time and improved consistency across three production shifts'
    },
    {
        'id': 'netprocess-solutions',
        'title': 'NetProcess Solutions Website',
        'company': 'Personal Business',
        'category': 'Web Development',
        'description': 'Built a professional business website for NetProcess Solutions, a software and process consulting company.',
        'details': [
            'Developed full-stack Flask web application with responsive design',
            'Created Apple-inspired UI with custom CSS animations',
            'Implemented contact form integration with email services',
            'Deployed on Railway with custom domain configuration',
            'Built testimonials, demos, and service showcase pages'
        ],
        'technologies': ['Python', 'Flask', 'HTML/CSS', 'JavaScript', 'Railway', 'Git'],
        'impact': 'Live production website at www.netprotech.dev'
    }
]

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
