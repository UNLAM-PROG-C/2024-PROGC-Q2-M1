import os
import re
import sys

import requests
from bs4 import BeautifulSoup


class MielScraper:

    CONTENTS_URL = 'https://miel.unlam.edu.ar/principal/interno/'
    LOGIN_URL = 'https://miel.unlam.edu.ar/principal/event/login/'
    DIRNAME = 'archivos_miel'

    def init(self, user, password):
        self.session = requests.Session()
        self.base_directory = os.path.dirname(os.path.abspath(__file__))
        self.base_path = os.path.join(self.base_directory, self.DIRNAME)
        absolute_path = os.path.abspath(self.base_path)
        self.credentials = {
            'usuario': user,
            'clave': password
        }
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def login(self):
        login_response = self.session.post(
            self.LOGIN_URL, data=self.credentials)
        if login_response.status_code != 200:
            print("Error al iniciar sesion")
            exit()

        login_response_json = login_response.json()

        if login_response_json.get("estado") != 0:
            print(
                f"Error al hacer la solicitud de inicio de sesión: {login_response.status_code}")
            exit()

    def get_subject_links(self):
        contents_response = self.session.get(self.CONTENTS_URL)
        if contents_response.status_code != 200:
            print(
                f"Error al acceder a la pagina de contenidos: {contents_response.status_code}")
            exit()

        contents_soup = BeautifulSoup(
            contents_response.content, 'html.parser')
        print("Acceso a la pagina de contenidos exitoso")
        self.subject_links = contents_soup.find_all(
            'div', class_="materia-bloque")

    def download_files(self):
        download_info = []
        # accedo a cada bloque de materia
        for subject in self.subject_links:  # archivos de principal/interno

            subject_title = subject.find(
                'div', class_="materia-titulo").get_text(strip=True)
            # creo la carpeta por cada materia
            subject_path = os.path.join(self.base_path, subject_title)
            if not os.path.exists(subject_path):
                os.makedirs(subject_path)

            subject_link = subject.find(
                'a', href=True, class_="w3-col w3-padding-8 w3-center w3-hover-green w3-hover-text-white")

            href = subject_link['href']

            # accedo a los modulos de la materia
            subject_response = self.session.get(href)
            subject_soup = BeautifulSoup(
                subject_response.content, 'html.parser')

            modules = subject_soup.find_all('div', class_="desplegarModulo")

            for module in modules:
                module_tittle = module.find('span').get_text(strip=True)

                module_path = os.path.join(subject_path, module_tittle)
                if not os.path.exists(module_path):
                    os.makedirs(module_path)

                unit_container = module.find_next_sibling(
                    'div', class_='w3-accordion-content')
                unit_table = unit_container.find_all(
                    'table', class_='w3-table')

                # accedo a las unidades de cada modulo
                for table in unit_table:
                    unit_tittle = table.find(
                        'th', colspan="2").contents[0].get_text(strip=True)  # contents[0] porque no hay un span en el encabezado, y el get_text te trae todo incluyendo lo que idce en el <o> y <div> interno
                    # le saco los caracteres basura para crear la carpeta
                    unit_tittle = re.sub(r'[<>:"/\\|?*]', '_', unit_tittle)

                    unit_path = os.path.join(
                        module_path, unit_tittle.replace(' ', '_'))

                    if not os.path.exists(unit_path):
                        os.makedirs(unit_path)

                    pdf_links = table.find_all('a', href=True)
                    for link in pdf_links:
                        href = link['href']

                        if "descargarElemento" in href:
                            print(f"Descargando {href}...")

                            pdf_response = self.session.get(
                                href)  # descargo pdf
                            if pdf_response.status_code == 200:
                                # usan 5C como prefijo
                                file_name = os.path.basename(
                                    href.split('/')[-3])
                                # TODO: hay otros caracteres raros aparte del 5C_
                                file_name = file_name.split('5C_', 1)[-1]

                                download_info.append(
                                    (subject_title, file_name, href))

                                file_path = os.path.join(unit_path, file_name)
                                with open(file_path, 'wb') as pdf_file:
                                    pdf_file.write(pdf_response.content)
                                    print(
                                        f"Archivo {file_name} descargado en {file_path}.")
                            else:
                                print(
                                    f"Error al descargar el archivo {href}")