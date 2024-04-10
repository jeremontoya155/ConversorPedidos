from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
import os
import re
from zipfile import ZipFile

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    input_files = request.files.getlist('file')
    output_format_folder = 'converted_files'
    error_format_folder = 'error_files'
    converted_files = []
    error_files = []

    if not os.path.exists(output_format_folder):
        os.makedirs(output_format_folder)
    if not os.path.exists(error_format_folder):
        os.makedirs(error_format_folder)

    for file in input_files:
        converted_lines, error_lines = convert_file(file)
        filename = secure_filename(file.filename)
        converted_filename = 'converted_' + filename
        error_filename = 'error_' + filename

        write_lines_to_file(converted_lines, os.path.join(output_format_folder, converted_filename))
        write_lines_to_file(error_lines, os.path.join(error_format_folder, error_filename))

        converted_files.append(converted_filename)
        error_files.append(error_filename)

    response = {
        'message': '¡Archivos convertidos con éxito!',
        'converted_files': converted_files,
        'error_files': error_files
    }
    return jsonify(response)

def convert_file(input_file):
    converted_lines = []
    error_lines = []
    lines = input_file.stream.readlines()
    for line in lines:
        barcode = line.decode()[:13]
        if len(re.findall(r'\d', barcode)) >= 5 and barcode.count('0') <= 7:
            match = re.search(r'\d+(?=[^\d]*$)', line.decode())
            if match:
                quantity = match.group(0)
            else:
                quantity = "No se encontró cantidad"
            description = re.sub(r'\d', '', line.decode()[13:-len(quantity)]).strip()
            converted_lines.append(f"{barcode};{description};{quantity}\n")
        else:
            error_lines.append(line.decode())
    return converted_lines, error_lines

def write_lines_to_file(lines, file_path):
    with open(file_path, 'w') as output_file:
        for line in lines:
            output_file.write(line)

@app.route('/download_converted')
def download_converted():
    zip_filename = 'converted_files.zip'
    with ZipFile(zip_filename, 'w') as zipf:
        for filename in os.listdir('converted_files'):
            zipf.write(os.path.join('converted_files', filename), filename)
    return send_file(zip_filename, as_attachment=True)

@app.route('/download_errors')
def download_errors():
    zip_filename = 'error_files.zip'
    with ZipFile(zip_filename, 'w') as zipf:
        for filename in os.listdir('error_files'):
            zipf.write(os.path.join('error_files', filename), filename)
    return send_file(zip_filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
