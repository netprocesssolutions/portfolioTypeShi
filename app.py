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
    'title': 'Process & Automation Engineer',
    'tagline': 'Data Modeling & ML · OT/IT Integration',
    'location': 'Chattanooga, TN',
    'email': 'me@jordantaylor.online',
    'phone': '423-400-1402',
    'summary': 'Chemical engineer (UTC, 3.79 GPA, Tau Beta Pi) working both sides of the OT/IT boundary on a continuous latex carpet-coating line — owning process and root-cause work on the floor while building the data warehouse, analytical tooling, and integration layer that turn plant data into engineering decisions. Architected a 2.1 GB analytical warehouse (2.5M+ time-series rows; an 82-column engineered feature table across 760+ runs), deployed a multi-coater trial-analysis and statistics tool, pioneered the plant\'s first Unified Namespace / Sparkplug B effort, and built an in-Ignition LLM operations advisor. FE exam scheduled.',
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
    },
    {
        'institution': 'Purdue University (Online)',
        'location': 'Online',
        'degree': 'M.S. Electrical & Computer Engineering — Automatic Control + AI/ML',
        'graduation': 'Planned 2028 · In Progress',
        'gpa': '',
        'major_gpa': '',
        'honors': [
            'FE Exam scheduled'
        ],
        'coursework': []
    }
]

EXPERIENCE = [
    {
        'company': 'Shaw Industries / Shaw Flooring',
        'title': 'Process Engineer, Plant 04 Coating / Finishing',
        'location': 'Dalton, GA',
        'dates': 'July 2025 – Present',
        'current': True,
        'highlights': [
            'Lead continuous-improvement and process engineering on Coater 1 — uptime, line-speed stability, and delamination / loose-edge reduction — owning puddle-height control across the precoat (Direct Applicator) and adhesive (Tillitson) systems, with defects traced back to upstream yarn and tufting characteristics.',
            'Drove SBR-latex compounding optimization through the VAE→SBR transition — investigating hard-piping restrictions, valve failures, and flow variability and their downstream coating effects; developed pretenter / maintenter edge-control and pin / brush concepts.',
            'Architected a 2.1 GB DuckDB analytical warehouse — per-run process tags (~2.5M rows), deviation records (~3.15M rows), actual-vs-setpoint comparisons, run statistics, and recipe setpoints across 240 styles — as the single analytical layer for delamination root-cause work.',
            'Built the extraction and feature pipeline for a delamination prediction engine — an 82-column engineered feature table across 760+ runs with multi-source ingestion (DataArchival historian, ~2,000 quality-email Pass/Fail records, 10,600+ SharePoint weight checks, recipe databases). The pipeline is production-ready; model training / inference is pending Databricks / GPU compute, in progress with corporate IT.',
            'Built and deployed a DataArchival trial-analysis GUI (Flask / pandas / SciPy) across Coater 1, Coater 2, and templated for Plant 80 — multi-tag selection with per-tag time offsets, a 5-model regression bench (R²), Welch t-test and F-test, boxplots, and Excel export — backed by a selection-bias-aware discipline that draws baselines from independent datasets.',
            'Built Ignition WebDev REST endpoints (/TAGS/READ, /QUERIES/READ_QUERY) bridging live tag reads and named SQL queries from the Ignition gateway to local Python tooling over HTTP — removing the historian-API dependency.',
            'Pioneered the company\'s first Unified Namespace and Sparkplug B effort — designing the plant-floor information architecture for data integration across OT and IT systems.',
            'Designed and built an in-Ignition LLM operations advisor — Perspective front end, Jython plant context, FastAPI / PostgreSQL back end with hybrid (vector + BM25) retrieval, structured analytical tools (percentile, distribution comparison, nearest-run, drift detection), a hash-chained audit log, and an engineer-feedback correction loop; provider-agnostic (OpenAI / Azure OpenAI / vLLM), 30-table schema, 145/0/2 tests. In personal use as a daily analytical aid; not yet generally deployed.',
            'Conducted a statistical analysis of 96 tenter downtime events (4,378 total minutes); isolated 41.9% to the tenter system and identified a directional walk-off bias at p ≈ 0.016, informing a capital-allocation recommendation.',
            'Created operator-training matrices and engagement meetings to lift skill coverage, onboarding, and shift-to-shift consistency; serve as the technical bridge across production, maintenance, compounding, quality, and OT / automation.',
            'Built self-service tooling for adjacent teams — an Excel-based latex inventory calculator used by accounting and a VBA-automated reporting tool — translating process and material data into cost-side visibility without engineering intervention.'
        ]
    },
    {
        'company': 'Woodbridge - Formed Plastics',
        'title': 'Process Engineer',
        'location': 'Chattanooga, TN',
        'dates': 'July 2024 – July 2025',
        'current': False,
        'highlights': [
            'Owned material, process, and quality on EPP / EPS / PSPE formed plastics (Tuebert molding presses) — continuous improvement on high-fallout part numbers via tool design, setpoint tuning, sampling, and launch / qualification with capability studies.',
            'Led a cross-functional OEE task force across three shifts — organizing sub-teams around cycle time, availability, maintenance response, and standardization; built Excel / VBA tools for setup extraction and work-order matching.'
        ]
    },
    {
        'company': 'Volkswagen Group of America',
        'title': 'Quality and Failure Analysis Intern',
        'location': 'Chattanooga, TN',
        'dates': 'January 2024 – July 2024',
        'current': False,
        'highlights': [
            'Supported a special task force on large-volume field failures in a FAP-style escalation environment — countermeasure development, action tracking, and cross-department communication.',
            'Built and maintained an intradepartmental tracking database with auto-formatted meeting minutes for cross-functional topics, ownership, and progress.'
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
        {'name': 'Python', 'level': 95},
        {'name': 'SQL / DuckDB / PostgreSQL / TimescaleDB', 'level': 90},
        {'name': 'Data Analysis & Statistics', 'level': 95},
        {'name': 'pandas / NumPy / SciPy', 'level': 90},
        {'name': 'Ignition / Perspective (Jython)', 'level': 85},
        {'name': 'FastAPI / REST APIs', 'level': 85},
        {'name': 'MQTT / Sparkplug B / OPC', 'level': 75},
        {'name': 'VBA / Excel Automation', 'level': 95},
        {'name': 'Power BI', 'level': 80},
        {'name': 'TypeScript / Node.js / Express', 'level': 70},
        {'name': 'Docker / Git', 'level': 75},
        {'name': 'Databricks / Azure AI Foundry (growing)', 'level': 55},
    ],
    'engineering': [
        'Process Development & Scale-Up',
        'Middleware & Systems Integration',
        'OT/IT Connectivity & Pipelines',
        'Data Analysis & Mathematical Modeling',
        'DOE, Trials & Statistical Risk',
        'Peer Education, Teaching & Public Speaking'
    ],
    'certifications': [
        'FE Exam — Chemical (scheduled)',
        'AutoCAD Certification Course',
        'CRLA Level 1 Peer Educator',
        'AIChE Southern Regional Conference 2023'
    ]
}

PROJECTS = [
    {
        'id': 'llm-advisor',
        'title': 'In-Ignition LLM Operations Advisor',
        'company': 'Shaw Industries',
        'category': 'Data & AI',
        'description': 'An operations-floor LLM assistant embedded in Ignition that answers process questions against live and historical plant data, with structured analytical tools and an engineer-feedback correction loop.',
        'details': [
            'Perspective frontend with Jython plant-context scripting',
            'FastAPI / PostgreSQL backend with hybrid (vector + keyword) retrieval',
            'Structured tools: percentile, distribution comparison, nearest historical runs, drift detection',
            'Hash-chained audit log and engineer-feedback correction loop',
            'Provider-agnostic (OpenAI / Azure OpenAI / vLLM); 30-table schema'
        ],
        'technologies': ['Python', 'FastAPI', 'PostgreSQL', 'Ignition', 'Perspective', 'Jython', 'LLM / RAG'],
        'impact': 'Built and passing a 145/0/2 test suite; pending migration into Shaw-defined tooling for production deployment'
    },
    {
        'id': 'delam-rca-warehouse',
        'title': 'Delamination RCA Analytical Warehouse',
        'company': 'Shaw Industries',
        'category': 'Data & AI',
        'description': 'An AI-assisted root-cause-analysis workflow for carpet-coating delamination failures, built on a DuckDB analytical warehouse of historian, recipe, and test data.',
        'details': [
            'Python extraction scripts pulling DataArchival historian data',
            'Recipe / setpoint joins and per-run deviation detection',
            '82 engineered ML features across 760+ production runs',
            'Run-comparison logic and automated per-run engineering reports',
            'Persistent correction rules captured from engineer review'
        ],
        'technologies': ['Python', 'DuckDB', 'pandas', 'SciPy', 'Historian', 'ML Feature Engineering'],
        'impact': '~2 GB warehouse spanning millions of time-series records; reproducible RCA in minutes'
    },
    {
        'id': 'trial-analysis-gui',
        'title': 'DataArchival Trial-Analysis GUI',
        'company': 'Shaw Industries',
        'category': 'Data & AI',
        'description': 'A desktop GUI for ad-hoc historian trial analysis, deployed across multiple coaters and templated for a second plant.',
        'details': [
            'Multi-tag selection with per-tag time offsets and shift filtering',
            '5-model regression bench with Welch t-test and F-test',
            'Boxplots and distribution comparisons with Excel export',
            'Deployed on Plant 4 Coater 1 and Coater 2; templated for Plant 80'
        ],
        'technologies': ['Python', 'Flask', 'pandas', 'matplotlib', 'SciPy'],
        'impact': 'Self-service trial analysis for engineers without writing code'
    },
    {
        'id': 'virtual-encoder',
        'title': 'Virtual Encoder for Coater 1',
        'company': 'Shaw Industries',
        'category': 'Automation & Controls',
        'description': 'A first-principles kinematic model that tracks tagged carpet cross-sections through the line to associate downstream defects with originating upstream coating conditions.',
        'details': [
            'Models flow Main Tenter -> Accum 1 -> Shear -> Accum 2 -> Roll-Up',
            'Composable Python topology with a pluggable tag-source',
            'Designed for live Ignition tag reads',
            'Links downstream defect events back to upstream process state'
        ],
        'technologies': ['Python', 'Kinematic Modeling', 'Ignition (planned)'],
        'impact': 'Design / model — foundation for defect-to-condition traceability'
    },
    {
        'id': 'uns-sparkplug',
        'title': 'Unified Namespace / Sparkplug B Architecture',
        'company': 'Shaw Industries',
        'category': 'Automation & Controls',
        'description': "The plant's first Unified Namespace and Sparkplug B effort, designing the information architecture for plant-floor data integration across OT and IT systems.",
        'details': [
            'Unified Namespace topology for plant-floor data',
            'MQTT / Sparkplug B payload and naming conventions',
            'OT/IT integration across historian, gateway, and analytics layers',
            'Foundation for event-driven plant data flow'
        ],
        'technologies': ['MQTT', 'Sparkplug B', 'Unified Namespace', 'Ignition', 'OT/IT'],
        'impact': 'First UNS / Sparkplug B initiative at the plant'
    },
    {
        'id': 'timescaledb-schema',
        'title': 'TimescaleDB Plant Time-Series Schema',
        'company': 'Shaw Industries',
        'category': 'Data & AI',
        'description': 'A PostgreSQL / TimescaleDB schema for plant time-series data with tooling for live and historical access.',
        'details': [
            'Hypertables and continuous aggregates for time-series',
            'Monitored-tag ingestion pipeline',
            'Python / WebDev tooling for live and historical queries',
            'Designed for scalable historian-style storage'
        ],
        'technologies': ['PostgreSQL', 'TimescaleDB', 'Python', 'SQL'],
        'impact': 'Scalable time-series backbone for plant analytics'
    },
    {
        'id': 'webdev-bridge',
        'title': 'Ignition WebDev REST Bridge',
        'company': 'Shaw Industries',
        'category': 'Automation & Controls',
        'description': 'REST endpoints that bridge live Ignition tag reads and named SQL queries from the gateway to local Python tooling over HTTP, with no historian API dependency.',
        'details': [
            'Endpoints: /TAGS/READ and /QUERIES/READ_QUERY',
            'Live tag reads exposed over HTTP',
            'Named SQL queries served from the Ignition gateway',
            'Decouples local Python tooling from historian APIs'
        ],
        'technologies': ['Ignition', 'WebDev', 'Jython', 'REST', 'Python', 'SQL'],
        'impact': 'Direct, dependency-light access to live and queried plant data'
    },
    {
        'id': 'tenter-downtime',
        'title': 'Tenter Downtime Analysis',
        'company': 'Shaw Industries',
        'category': 'Continuous Improvement',
        'description': 'An analysis of Main Tenter downtime events to quantify availability loss and rank the largest recurring downtime drivers.',
        'details': [
            'Consolidated downtime records into a single analytical feed',
            'Categorized downtime causes and built Pareto rankings',
            'Quantified availability loss by cause and shift',
            'Surfaced the highest-impact reliability targets'
        ],
        'technologies': ['Python', 'pandas', 'DuckDB', 'Power BI', 'Excel / VBA'],
        'impact': 'Prioritized reliability work by quantified downtime impact'
    },
    {
        'id': 'shift-report-app',
        'title': 'Coating Shift Report / Operations Data App',
        'company': 'Shaw Industries',
        'category': 'Software Development',
        'description': 'An evolution of Excel / VBA shift-report extraction into a web-based operations data application across coating and compounding.',
        'details': [
            'Migrated VBA shift-report extraction to a web stack',
            'Node.js / Express / TypeScript services with PostgreSQL',
            'Power BI reporting concept across coating and compounding',
            'Centralized shift-level operations data'
        ],
        'technologies': ['Node.js', 'TypeScript', 'Express', 'PostgreSQL', 'Power BI', 'VBA'],
        'impact': 'Shift-report data centralized and made reportable'
    },
    {
        'id': 'analytics-pipeline',
        'title': 'Digital Analytics Pipeline',
        'company': 'Shaw Flooring',
        'category': 'Data & AI',
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
        'category': 'Continuous Improvement',
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
    }
]

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
