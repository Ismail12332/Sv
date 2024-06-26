import os
from flask import Flask, render_template, request, redirect, url_for, session,jsonify,abort,send_file, make_response
from pymongo import MongoClient
from passlib.hash import bcrypt
from bson import ObjectId
from datetime import datetime
from dotenv import load_dotenv
from flask_cors import CORS,cross_origin
from urllib.parse import quote
from b2sdk.v2 import *
import secrets
import uuid
import pprint
import jwt
import requests
from jose import jwt, JWTError
from functools import wraps
from openai import OpenAI
import traceback
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Indenter, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.graphics.shapes import Drawing, Line
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import html
import time
import stripe
import io
import random
import string

load_dotenv()

def create_app():
    class User:
        def __init__(self, username, password, email):
            self.username = username
            self.password_hash = bcrypt.hash(password)
            self.email = email



    app = Flask(__name__, template_folder='templates')
    CORS(app, supports_credentials=True)
    app.secret_key = secrets.token_hex(32)
    client = MongoClient("mongodb://localhost:27017")
    app.db = client.my_database
    users_collection = app.db.users
    projects_collection = app.db.projects
    client = OpenAI(
        api_key="",
    )

    # Создание клиента Backblaze B2
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    application_key_id = '4ad4332a1370'
    application_key = ''
    b2_api.authorize_account("production", application_key_id, application_key)

    # Получение бакета (папки) для хранения изображений
    bucket_name_b2 = 'Survzila'
    bucket = b2_api.get_bucket_by_name(bucket_name_b2)

    # Регистрация шрифта
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))


    # Конфигурация Auth0
    AUTH0_DOMAIN = 'dev-whbba5qnfveb88fc.us.auth0.com'
    API_AUDIENCE = 'http://Survzilla'
    ALGORITHMS = ['RS256']


    # Получение открытых ключей Auth0 с обработкой ошибок
    jwks_url = f'https://{AUTH0_DOMAIN}/.well-known/jwks.json'

    def get_jwks():
        for attempt in range(3):  # Попробуем три раза
            try:
                jwks = requests.get(jwks_url).json()
                return jwks
            except requests.exceptions.ConnectionError as e:
                print(f"Ошибка соединения при попытке {attempt + 1}: {e}")
                time.sleep(1)  # Подождем секунду перед повторной попыткой
        raise RuntimeError("Не удалось получить JWKS ключи после нескольких попыток")

    jwks = get_jwks()

    def get_rsa_key(header):
        for key in jwks['keys']:
            if key['kid'] == header['kid']:
                return {
                    'kty': key['kty'],
                    'kid': key['kid'],
                    'use': key['use'],
                    'n': key['n'],
                    'e': key['e']
                }
        return None

    def requires_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get('Authorization', None)
            if not auth_header:
                return jsonify({"message": "Authorization header is missing"}), 401

            token = auth_header.split()[1]
            try:
                header = jwt.get_unverified_header(token)
                rsa_key = get_rsa_key(header)
                if not rsa_key:
                    return jsonify({"message": "Invalid header"}), 401

                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=ALGORITHMS,
                    audience=API_AUDIENCE,
                    issuer=f'https://{AUTH0_DOMAIN}/'
                )
            except JWTError as e:
                return jsonify({"message": "Invalid token"}), 401

            request.user = payload
            return f(*args, **kwargs)
        return decorated



    @app.route("/", methods=["GET"])
    def login(supports_credentials=True):
        return render_template("index.html")
    

    @app.route("/api/vitrine", methods=["GET"])
    def get_vitrine_projects():
        try:
            projects = list(app.db.vitrine.find({}))
            for project in projects:
                project['_id'] = str(project['_id'])
                project['project_id'] = str(project['project_id'])
            return jsonify({"status": "success", "projects": projects}), 200
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    

    #выход
    @app.route("/logout")
    def logout():
        # Очищаем сессию пользователя при выходе
        session.pop("user_id", None)
        return redirect(url_for("login"))


    def create_project_pdf(project):
        buffer = io.BytesIO()
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='CustomNormal', fontName='DejaVuSans'))
        styles.add(ParagraphStyle(name='CenteredHeading1', parent=styles['Heading1'], alignment=1))
        styles.add(ParagraphStyle(name='SectionTitle', fontSize=16, alignment=1))
        styles.add(ParagraphStyle(name='SubsectionTitle', fontSize=14, alignment=0, spaceAfter=10))
        styles.add(ParagraphStyle(name='ElementTitle', fontSize=12, alignment=0, spaceAfter=10))
        styles.add(ParagraphStyle(name='FinalSection', fontSize=12, alignment=1, spaceAfter=20))
        
        def build_story(project):
            story = []

            # Add header with logo
            Survey_logo = "static/images/VerboatLogo02.png"
            img = Image(Survey_logo)
            img.drawHeight = 1 * inch
            img.drawWidth = 1 * inch
            story.append(Table([[Paragraph("VerBoat.com Boat Inspection", styles['CenteredHeading1']), img]], colWidths=[None, 1 * inch]))
            story.append(Spacer(1, 0.5 * inch))

            # Add project info
            main_image_url = project.get('main_image', '')
            if main_image_url:
                main_image = Image(main_image_url)
                main_image.drawHeight = 5.5 * inch
                main_image.drawWidth = 7 * inch
                story.append(main_image)
            
            project_info = f"""
            <b>{project.get('boat_make', '')} {project.get('boat_model', '')}</b><br/>
            {project.get('length', '')} ft / {project.get('year', '')}<br/>
            {project.get('boat_registration', '')}<br/>
            Engine: {project.get('engine', '')}<br/>
            ${project.get('price', '')}<br/>
            {project.get('city', '')}<br/>
            Owner Contact: {project.get('owner_contact', '')}<br/>
            {project.get('created_at', '')}
            """
            story.append(Paragraph(project_info, styles['CustomNormal']))
            story.append(Spacer(1, 0.5 * inch))
            story.append(PageBreak())

            # Add sections
            for section_name, section_content in project['sections'].items():
                cleaned_section_name = section_name.replace('_', ' ').title()
                story.append(Paragraph(cleaned_section_name, styles['SectionTitle']))

                for subsection_name, subsection_content in section_content.items():
                    cleaned_subsection_name = subsection_name.replace('_', ' ').title()
                    has_content = any(
                        subsection_content[element_name].get('steps') or subsection_content[element_name].get('images')
                        for element_name in subsection_content
                    )
                    if not has_content:
                        continue
                    
                    story.append(Paragraph(cleaned_subsection_name, styles['SubsectionTitle']))

                    for element_name, element_content in subsection_content.items():
                        if element_content.get('steps') or element_content.get('images'):
                            cleaned_element_name = element_name.replace('_', ' ').title()
                            criticality = element_content.get('criticality', '')
                            crit_img_path = f"static/images/{criticality}.png" if criticality else None
                            crit_img = Image(crit_img_path) if crit_img_path else None

                            if crit_img:
                                crit_img.drawHeight = 0.3 * inch
                                crit_img.drawWidth = 0.3 * inch
                                element_paragraph = Paragraph(f"{cleaned_element_name}&nbsp;&nbsp;", styles['ElementTitle'])
                                element_table = Table([[element_paragraph, crit_img]], colWidths=[2 * inch, 0.5 * inch])
                                story.append(element_table)
                            else:
                                story.append(Paragraph(cleaned_element_name, styles['ElementTitle']))

                            images = []
                            for image_url in element_content.get('images', []):
                                img = Image(image_url)
                                img.drawHeight = 2 * inch
                                img.drawWidth = 2 * inch
                                images.append(img)
                                if len(images) == 2:
                                    story.append(Table([images], colWidths=[2.5 * inch, 2.5 * inch]))
                                    story.append(Spacer(1, 0.2 * inch))
                                    images = []
                            if images:
                                story.append(Table([images], colWidths=[2.5 * inch, 2.5 * inch]))
                                story.append(Spacer(1, 0.2 * inch))

                            story.append(Indenter(left=20))
                            for step in element_content.get('steps', []):
                                step = html.escape(step)
                                story.append(Paragraph(step, styles['CustomNormal']))
                                story.append(Spacer(1, 0.1 * inch))
                            story.append(Indenter(left=-20))

                    story.append(Spacer(0.5, 0.2 * inch))
                    story.append(Spacer(1, 0.2 * inch))
                    story.append(Spacer(0.5, 0.2 * inch))

            # Add final note and image
            if project.get('final_note'):
                story.append(PageBreak())
                story.append(Paragraph("Finalizing", styles['SectionTitle']))
                final_text = "This inspection was conducted to the best of my ability, addressing as many issues as possible. I hope it will help you make an informed decision about this boat."
                story.append(Paragraph(final_text, styles['FinalSection']))
                story.append(Spacer(1, 0.2 * inch))
                story.append(Paragraph(project['final_note'], styles['FinalSection']))
                if project.get('final_kartinka'):
                    final_image = Image(project['final_kartinka'])
                    final_image.drawHeight = 5.5 * inch
                    final_image.drawWidth = 7 * inch
                    story.append(final_image)
            
            return story

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)

        story = build_story(project)
        doc.build(story)
        buffer.seek(0)
        return buffer


    @app.route('/download_project_pdf/<project_id>')
    @requires_auth
    def download_project_pdf(project_id):
        # Получение проекта по его ID (примерная реализация)
        project = projects_collection.find_one({"_id": ObjectId(project_id)})

        if not project:
            abort(404, description="Project not found")

        pdf_buffer = create_project_pdf(project)

        # Отправка PDF клиенту
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"project_{project_id}.pdf",
            mimetype='application/pdf'
        )

    def convert_projects_to_list(projects):
        #Converts MongoDB projects to a list with ObjectId converted to string.
        projects_list = []
        for project in projects:
            project_data = {**project}
            project_data["_id"] = str(project["_id"])
            projects_list.append(project_data)
        return projects_list
    

    @app.route("/api/glav", methods=["GET"])
    @requires_auth
    def get_projects(supports_credentials=True):
        user_id = request.user.get('sub')  # Извлекаем user_id из токена
        projects = app.db.projects.find({"user_id": user_id})
        projects_list = convert_projects_to_list(projects)
        return jsonify({"status": "success", "user_id": str(user_id), "projects": projects_list})
    

    @app.route("/glav", methods=["GET"])
    def get_projectse(supports_credentials=True):
            return render_template("index.html")
    

    @app.route("/cheakglav", methods=["GET"])
    @requires_auth
    def go_to_glav(supports_credentials=True):
            return jsonify({"status": "success"})


    @app.route("/index2", methods=["POST"])
    @requires_auth
    def create_project():
        user_id = request.user.get("sub")
        data = request.json  # Получаем данные из JSON-запроса
        # Обновляем запрос к базе данных, чтобы фильтровать проекты по user_id
        projects = app.db.projects.find({"user_id": user_id})
        projects_list = convert_projects_to_list(projects)

        boat_make = data.get('boat_make')
        boat_model = data.get('boat_model')
        boat_registration = data.get('boat_registration')
        length = data.get('length')
        year = data.get('year')
        engine = data.get('engine')
        price = data.get('price')
        city = data.get('city')
        owner_contact = data.get('owner_contact')
        project_code = generate_unique_code(app.db.projects)

        # Создаем проект
        project = {
            'user_id': user_id,
            'boat_make': boat_make,
            'boat_model': boat_model,
            'boat_registration': boat_registration,
            'length': length,
            'year': year,
            'engine': engine,
            'price': price,
            'city': city,
            'owner_contact': owner_contact,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "project_code": project_code,
            "sections": {
                    "introduction": {"gen_info": {},"certification": {},"purpose_of_survey": {},"circumstances_of_survey": {},"report_file_no": {},"surveyor_qualifications": { },"intended_use": {},
                    },
                    "hull": { "layout_overview": {},"design": {},"deck": {},"structural_members": {},"bottom_paint": {},"blister_comment": {},"transom": {},
                    },
                    "above": { "deck_floor_plan": {},"anchor_platform": {},"toe_rails": {},"mooring_hardware": {},"hatches": {},"exterior_seating": {},"cockpit_equipment": {},"ngine_hatch": {},"above_draw_water_line": {},"boarding_ladder": {},"swim_platform": {},
                    },
                    "below": { "below_draw_water": {},"thru_hull_strainers": {},"transducer": {},"sea_valves": {},"sea_strainers": {},"trim_tabs": {},"note": {},
                    },
                    "cathodic": { "bonding_system": {},"anodes": {},"lightning_protection": {},"additional_remarks": {},
                    },
                    "helm": { "helm_station": {},"throttle_shift_controls": {},"engine_room_blowers": {},"engine_status": {},"other_electronics_controls": {},
                    },
                    "cabin": { "entertainment_berthing": {},"interior_lighting": {},"galley_dinette": {},"water_closets": {},"climate_control": {},
                    },
                    "electrical": { "dc_systems_type": {},"ac_systems": {},"generator": {},
                    },
                    "inboard": { "engines": {},"serial_numbers": {},"engine_hours": {},"other_note": {},"reverse_gears": {},"shafting_propellers": {},
                    },
                    "steering": { "manufacture": {},"steering_components": {},
                    },
                    "tankage": { "fuel": {},"potable_water_system": {},"holding_tank_black_water": {},
                    },
                    "safety": { "navigational_lights": {},"life_jackets": {},"throwable_pfd": {},"visual_distress_signals": {},"sound_devices": {},"uscg_placards": {},"flame_arrestors": {},"engine_ventilation": {},"ignition_protection": {},"inland_navigational_rule_book": {},"waste_management_plan": {},"fire_fighting_equipment": {},"bilge_pumps": {},"ground_tackle_windlass": {},"auxiliary_safety_equipment": {},
                    },
                }
        }

        result = app.db.projects.insert_one(project)
        project_id = result.inserted_id

        print("Entry added:", boat_make, boat_model, city, boat_registration, length, engine, user_id, project_id,price)
        return jsonify({"status": "success", "user_id": str(user_id), "project_id": str(project_id)})



    def generate_random_code(length=8):
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    def generate_unique_code(collection, length=8):
        while True:
            code = generate_random_code(length)
            if not collection.find_one({"project_code": code}):
                return code

    # Проверка, что текущий пользователь является владельцем проекта
    def check_project_owner(user_id, project_id):
        project = app.db.projects.find_one({"_id": ObjectId(project_id), "user_id": user_id})
        return project is not None


    @app.route("/api/update_criticality", methods=["POST"])
    @requires_auth
    def update_criticality():
        user_id = request.user.get('sub')
        data = request.get_json()
        section = data.get('section')
        subsection = data.get('subsection')
        element = data.get('element')
        criticality = data.get('criticality')
        project_id = ObjectId(data.get('project_id'))

        # Проверка подлинности клиента
        if not check_project_owner(user_id, project_id):
            return jsonify({"status": "error", "message": "Unauthorized access"}), 403

        if not section or not subsection or not element or not criticality:
            return jsonify({"message": "Missing data"}), 400

        # Обновление критичности в элементе
        result = app.db.projects.update_one(
            {"_id": project_id, "user_id": user_id},
            {"$set": {f"sections.{section}.{subsection}.{element}.criticality": criticality}}
        )

        if result.modified_count == 1:
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"message": "Failed to update criticality"}), 400


    #Переключение на проект в главное странице нажатие на имя проекта
    @app.route("/api/EditProject/<string:project_id>", methods=["POST"])
    @requires_auth
    def edit_project(project_id,supports_credentials=True):
        user_id = request.user.get('sub')

        #Проверка подлености клиента
        if not check_project_owner(user_id, project_id):
            return jsonify({"status": "error", "message": "Unauthorized access"}), 403

        try:
            # Преобразовываем project_id в ObjectId
            project_id = ObjectId(project_id)
        except Exception as e:
            # Обработка ошибки, если project_id неверного формата
            return jsonify({"status": "error", "message": "Invalid project_id"}), 400

        # Проверяем, что текущий пользователь имеет доступ к проекту
        project = app.db.projects.find_one({"_id": project_id})
        if project is None:
            return jsonify({"status": "error", "message": "Project not found"}), 404

        project['_id'] = str(project['_id'])
        # Возвращаем данные о проекте в формате JSON
        print(f"Fetching project with ID: {project_id}", project)

        return jsonify({"status": "success", "project": project})


    @app.route("/EditProject/<project_id>", methods=["GET"])
    def get_projectse_edit_project(project_id,supports_credentials=True):
        return render_template("index.html")


    #Дабовление и удаление записей в разделах 
    @app.route("/edit_project/<project_id>/add_step", methods=["POST"])
    @requires_auth
    def add_step(project_id):
        user_id = request.user.get('sub')

        if not check_project_owner(user_id, project_id):
            return jsonify({"status": "error", "message": "Unauthorized access"}), 403

        try:
            project_id = ObjectId(project_id)
        except Exception as e:
            return jsonify({"status": "error", "message": "Invalid project_id"}), 400

        data = request.json
        section = data.get("section")
        subsection = data.get("subsection")
        element = data.get("element")
        step_description = data.get("step_description")
        print(section,subsection,element,step_description)

        try:
            result = app.db.projects.update_one(
                {"_id": project_id, f"sections.{section}.{subsection}.{element}": {"$exists": True}},
                {"$push": {f"sections.{section}.{subsection}.{element}.steps": step_description}}
            )

            if result.modified_count == 0:
                return jsonify({"status": "error", "message": "Project, section, subsection or element not found"}), 404

            updated_project = app.db.projects.find_one({"_id": project_id})
            updated_project["_id"] = str(updated_project["_id"])

            return jsonify({"status": "success", "message": "Step added successfully", "updated_project": updated_project})
        except Exception as e:
            print("Error:", e)
            return jsonify({"status": "error", "message": "An error occurred"}), 500

    
    

    #Добавление изображения в основные подразделы (нужно переделать)-----------------------------------------
    @app.route('/edit_project/<project_id>/add_image', methods=['POST'])
    @requires_auth
    def add_image(project_id):
        user_id = request.user.get('sub')

        if not check_project_owner(user_id, project_id):
            return jsonify({"status": "error", "message": "Unauthorized access"}), 403

        try:
            project_id = ObjectId(project_id)
        except Exception as e:
            return jsonify({"status": "error", "message": "Invalid project_id"}), 400

        if 'image_upload' not in request.files:
            return jsonify({"status": "error", "message": "No file part"}), 400

        image_file = request.files['image_upload']

        if image_file.filename == '':
            return jsonify({"status": "error", "message": "No selected file"}), 400

        if image_file:
            file_data = image_file.read()
            file_name = image_file.filename
            b2_file_name = str(uuid.uuid4())

            bucket.upload_bytes(
                data_bytes=file_data,
                file_name=b2_file_name
            )

            file_info = {
                'file_name': file_name,
                'b2_file_name': b2_file_name,
                'b2_url': 'https://f004.backblazeb2.com/file/Survzila/' + quote(b2_file_name)
            }
            app.db.files.insert_one(file_info)

            section = request.form.get('section')
            subsection = request.form.get("subsection")
            element = request.form.get("element")
            print(section,subsection,element,file_info["b2_url"])

            app.db.projects.update_one(
                {"_id": project_id, f"sections.{section}.{subsection}.{element}": {"$exists": True}},
                {"$push": {f"sections.{section}.{subsection}.{element}.images": file_info["b2_url"]}}
            )

            updated_project = app.db.projects.find_one({"_id": project_id})
            updated_project["_id"] = str(updated_project["_id"])

            return jsonify({
                "status": "success",
                "message": "Image uploaded successfully",
                "updated_project": updated_project
            }), 200
        else:
            return jsonify({"status": "error", "message": "Failed to upload file"}), 400

        

    @app.route("/edit_project/<project_id>/remove_image", methods=["POST"])
    @requires_auth
    def remove_image(project_id):
        user_id = request.user.get('sub')

        if not check_project_owner(user_id, project_id):
            return jsonify({"status": "error", "message": "Unauthorized access"}), 403

        try:
            project_id = ObjectId(project_id)
        except Exception as e:
            return jsonify({"status": "error", "message": "Invalid project_id"}), 400

        data = request.json
        section = data.get("section")
        subsection = data.get("subsection")
        element = data.get("element")
        image = data.get("image")

        try:
            result = app.db.projects.update_one(
                {"_id": project_id, f"sections.{section}.{subsection}.{element}.images": image},
                {"$pull": {f"sections.{section}.{subsection}.{element}.images": image}}
            )

            if result.modified_count == 0:
                return jsonify({"status": "error", "message": "Image not found"}), 404

            updated_project = app.db.projects.find_one({"_id": project_id})
            updated_project["_id"] = str(updated_project["_id"])

            return jsonify({"status": "success", "message": "Image removed successfully", "updated_project": updated_project})
        except Exception as e:
            print("Error:", e)
            return jsonify({"status": "error", "message": "An error occurred"}), 500



    @app.route("/edit_project/<project_id>/remove_step", methods=["POST"])
    @requires_auth
    def remove_step(project_id):
        user_id = request.user.get('sub')

        if not check_project_owner(user_id, project_id):
            return jsonify({"status": "error", "message": "Unauthorized access"}), 403

        try:
            project_id = ObjectId(project_id)
        except Exception as e:
            return jsonify({"status": "error", "message": "Invalid project_id"}), 400

        data = request.json
        section = data.get("section")
        subsection = data.get("subsection")
        element = data.get("element")
        step_description = data.get("step_description")
        print(section,subsection,element,step_description)
        

        try:
            result = app.db.projects.update_one(
                {"_id": project_id, f"sections.{section}.{subsection}.{element}.steps": step_description},
                {"$pull": {f"sections.{section}.{subsection}.{element}.steps": step_description}}
            )

            if result.modified_count == 0:
                return jsonify({"status": "error", "message": "Step not found"}), 404

            updated_project = app.db.projects.find_one({"_id": project_id})
            updated_project["_id"] = str(updated_project["_id"])

            return jsonify({"status": "success", "message": "Step removed successfully", "updated_project": updated_project})
        except Exception as e:
            print("Error:", e)
            return jsonify({"status": "error", "message": "An error occurred"}), 500



    #----------------------------------------------------------------
    #Добавление раздела
    @app.route("/edit_project/<project_id>/add_section", methods=["POST"])
    @requires_auth
    def add_section(project_id):
        user_id = request.user.get('sub')

        #Проверка подлености клиента
        if not check_project_owner(user_id, project_id):
            return jsonify({"status": "error", "message": "Unauthorized access"}), 403
        

        try:
            project_id = ObjectId(project_id)
        except Exception as e:
            return "Invalid project_id", 400

        section_name = request.form.get("section_name")

        try:
            result = app.db.projects.update_one(
                {"_id": project_id},
                {"$set": {f"sections.{section_name}": {}}}
            )
            if result.modified_count == 0:
                return "Project not found", 404
        except Exception as e:
            print("Error:", e)
            return "An error occurred", 500
        updated_project = app.db.projects.find_one({"_id": project_id})
        updated_project['_id'] = str(updated_project['_id'])
        
        return jsonify({"status": "success", "message": "Section added successfully", "updated_project": updated_project})


    #Добавление подраздела
    @app.route("/edit_project/<project_id>/add_subsection", methods=["POST"])
    @requires_auth
    def add_subsection(project_id):
        user_id = request.user.get('sub')

        #Проверка подлености клиента
        if not check_project_owner(user_id, project_id):
            return jsonify({"status": "error", "message": "Unauthorized access"}), 403
        

        try:
            project_id = ObjectId(project_id)
        except Exception as e:
            return jsonify({"status": "error", "message": "Invalid project_id"}), 400

        data = request.json
        section_name = data.get("section_name")
        subsection_name = data.get("subsection_name")
        print(section_name,subsection_name)

        if not section_name or not subsection_name:
            return jsonify({"status": "error", "message": "Section name and Subsection name are required"}), 400

        try:
            # Добавляем новый подраздел в выбранный раздел
            result = app.db.projects.update_one(
                {"_id": project_id},
                {"$set": {f"sections.{section_name}.{subsection_name}": {}}}
            )
            if result.modified_count == 0:
                return jsonify({"status": "error", "message": "Project or section not found"}), 404
        except Exception as e:
            print("Error:", e)
            return jsonify({"status": "error", "message": "An error occurred during subsection addition"}), 500

        updated_project = app.db.projects.find_one({"_id": project_id})
        updated_project['_id'] = str(updated_project['_id'])
        
        return jsonify({"status": "success", "message": "Subsection added successfully", "updated_project": updated_project})
    

    #чат джипити
    @app.route('/edit_project/<project_id>/get-gpt-recommendations', methods=['POST'])
    @requires_auth
    def get_gpt_recommendations(project_id):
        user_id = request.user.get('sub')

        #Проверка подлености клиента
        if not check_project_owner(user_id, project_id):
            return jsonify({"status": "error", "message": "Unauthorized access"}), 403
        
        data = request.json
        section = data['section']
        subsection = data['subsection']
        description = data['step_description']
        prompt = f"part of the ship was inspected {section}, namely, looked around{subsection}. in short then {description}"

        try:
            response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant to an employee who inspects yachts, he writes you a brief description of the inspection of a certain part of the ship (let’s assume everything is fine), you need to describe how the inspection was carried out"},
                {"role": "user", "content": prompt}
            ]
            )
            print(response)
            recommendations = response.choices[0].message.content.strip()
            return jsonify({'recommendations': recommendations})
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
            


    @app.route("/api/add_to_showcase", methods=["POST"])
    @requires_auth
    def add_to_showcase():
        user_id = request.user.get('sub')  # Extract user_id from token
        data = request.form.to_dict()
        project_id = ObjectId(data.get('project_id'))
        price = data.get('price')
        description = data.get('description')
        final_note = data.get('final_note')
        file = request.files.get('file')
        final_kartinka = request.files.get('final_kartinka')
        print(final_note, final_kartinka, file)

        if not check_project_owner(user_id, project_id):
            return jsonify({"status": "error", "message": "Unauthorized access"}), 403

        if not project_id or not price or not description or not file or not final_note or not final_kartinka:
            return jsonify({"message": "Missing project_id, price, description, file, final_note, or final_kartinka"}), 400

        project = app.db.projects.find_one({"_id": project_id, "user_id": user_id})
        if not project:
            return jsonify({"message": "Project not found"}), 404

        # Upload the files to Backblaze B2
        b2_file_name = str(uuid.uuid4())
        b2_file = bucket.upload_bytes(file.read(), b2_file_name)
        file_info = {
            'b2_url': f'https://f004.backblazeb2.com/file/{bucket_name_b2}/{quote(b2_file_name)}'
        }

        b2_final_kartinka_name = str(uuid.uuid4())
        b2_final_kartinka = bucket.upload_bytes(final_kartinka.read(), b2_final_kartinka_name)
        final_kartinka_info = {
            'b2_url': f'https://f004.backblazeb2.com/file/{bucket_name_b2}/{quote(b2_final_kartinka_name)}'
        }

        vitrine_data = {
            "vessel_name": project['boat_model'],
            "gen_info_image": file_info["b2_url"],
            "user_id": user_id,
            "project_id": project_id,
            "price": price,
            "city": project['city'],
            "description": description,
            "year": project['year'],
            "project_code": project['project_code'],  # Добавляем код проекта
            "access_list": [user_id]
        }

        project_update_data = {
            "final_note": final_note,
            "final_kartinka": final_kartinka_info["b2_url"],
            "description": description,
        }

        # Update the project with final_note and final_kartinka
        app.db.projects.update_one(
            {"_id": project_id},
            {"$set": project_update_data}
        )

        existing_entry = app.db.vitrine.find_one({"project_id": project_id})
        if existing_entry:
            result = app.db.vitrine.update_one(
                {"project_id": project_id},
                {"$set": vitrine_data}
            )
            if result.modified_count > 0:
                return jsonify({"status": "success", "message": "Project updated in showcase"}), 200
            else:
                return jsonify({"message": "Failed to update project in showcase"}), 400
        else:
            result = app.db.vitrine.insert_one(vitrine_data)
            if result.inserted_id:
                return jsonify({"status": "success", "message": "Project added to showcase"}), 200
            else:
                return jsonify({"message": "Failed to add project to showcase"}), 400

            

    
    @app.route("/viewproject/<project_id>", methods=["GET"])
    def yview_project(project_id):
        return render_template("index.html")


    #предварительной просмотр проекта
    @app.route("/api/preview/<project_code>", methods=["GET"])
    def preview_project_by_code(project_code):
        project = app.db.vitrine.find_one({"project_code": project_code})
        if not project:
            return jsonify({"status": "error", "message": "Project not found"}), 404

        # Convert ObjectId to string for JSON serialization
        project["_id"] = str(project["_id"])
        project["project_id"] = str(project["project_id"])
        return jsonify({"status": "success", "project": project}), 200

        

    #Просмотр проектов с ветрины
    @app.route("/api/project/<project_code>", methods=["GET"])
    @requires_auth
    def get_project_by_code(project_code):
        user_id = request.user.get('sub')  # Extract user_id from token

        project_vitrine = app.db.vitrine.find_one({"project_code": project_code})
        if not project_vitrine:
            return jsonify({"status": "error", "message": "Project not found"}), 404
        
        # Check if the user is in the access_list
        if user_id not in project_vitrine.get("access_list", []):
            return jsonify({"status": "error", "message": "Access denied"}), 403

        project_id = project_vitrine["project_id"]
        project = app.db.projects.find_one({"_id": project_id})
        if not project:
            return jsonify({"status": "error", "message": "Project not found"}), 404

        project["_id"] = str(project["_id"])
        return jsonify({"status": "success", "project": project}), 200


    
    stripe.api_key = ""
    endpoint_secret = ''

    @app.route("/api/check_access/<project_id>", methods=["GET"])
    @requires_auth
    def check_access(project_id):
        user_id = request.user.get('sub')  # Extract user_id from token
        project_id = ObjectId(project_id)

        project = app.db.vitrine.find_one({"project_id": project_id})
        if not project:
            return jsonify({"message": "Project not found"}), 404

        if user_id in project.get("access_list", []):
            return jsonify({"access": True}), 200

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': project['vessel_name'],
                    },
                    'unit_amount': 1000,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'http://localhost:5173/viewproject/{project_id}',
            cancel_url="http://localhost:5173/",
            metadata={
                'user_id': user_id,
                'project_id': str(project_id)
            }
        )

        return jsonify({"access": False, "sessionId": session.id}), 200

    @app.route('/webhook', methods=['POST'])
    def stripe_webhook():
        payload = request.get_data(as_text=True)
        sig_header = request.headers.get('Stripe-Signature')

        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            return jsonify(success=False, error=str(e)), 400
        except stripe.error.SignatureVerificationError as e:
            return jsonify(success=False, error=str(e)), 400

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            user_id = session['metadata']['user_id']
            project_id = ObjectId(session['metadata']['project_id'])

            app.db.vitrine.update_one(
                {"project_id": project_id},
                {"$push": {"access_list": user_id}}
            )
            print(f"User {user_id} added to access list of project {project_id}")

        return jsonify(success=True), 200


    #Add Element
    @app.route("/edit_project/<project_id>/add_element", methods=["POST"])
    @requires_auth
    def add_element(project_id):
        user_id = request.user.get('sub')

        if not check_project_owner(user_id, project_id):
            return jsonify({"status": "error", "message": "Unauthorized access"}), 403

        try:
            project_id = ObjectId(project_id)
        except Exception as e:
            return jsonify({"status": "error", "message": "Invalid project_id"}), 400

        data = request.json
        section = data.get("section")
        subsection = data.get("subsection")
        element_name = data.get("element_name")

        try:
            result = app.db.projects.update_one(
                {"_id": project_id},
                {"$set": {f"sections.{section}.{subsection}.{element_name}": {"images": [], "steps": []}}}
            )

            if result.modified_count == 0:
                return jsonify({"status": "error", "message": "Project or section or subsection not found"}), 404

            updated_project = app.db.projects.find_one({"_id": project_id})
            updated_project["_id"] = str(updated_project["_id"])

            return jsonify({"status": "success", "message": "Element added successfully", "updated_project": updated_project})
        except Exception as e:
            print("Error:", e)
            return jsonify({"status": "error", "message": "An error occurred"}), 500


    if __name__ == "__main__":
        app.run(debug=True)
    
    return app
