from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import time
import base64
import os
import uuid

app = Flask(__name__)


def setup_driver(browser):
    if browser.lower() == 'chrome':
        return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    elif browser.lower() == 'edge':
        return webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()))
    else:
        raise ValueError("Unsupported browser type. Use 'chrome' or 'edge'.")


def update_field(driver, element_id, value):
    element = driver.find_element(By.ID, element_id)
    element.clear()
    element.send_keys(value)


@app.route('/submitted', methods=['POST'])
def open_url():
    data = request.json
    project_code = data.get('project_code')
    project_name = data.get('project_name')
    pm = data.get('pm')
    total_hours = data.get('total_hours')
    url = data.get('url')
    browser = data.get('browser', 'chrome')

    if 'file' not in data:
        return jsonify({"message": "No file"}), 400

    file_data = data['file'].strip().replace("\n", "").replace("\r", "")

    try:
        file_content = base64.b64decode(file_data)
    except ValueError as e:
        return jsonify(
            {"message": f"Invalid: {str(e)}"}), 400

    file_name = f"{uuid.uuid4().hex}.pdf"
    file_path = os.path.join(os.getcwd(), file_name)

    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
    except Exception as e:
        return jsonify({"message": f"Error saving file: {str(e)}"}), 500

    try:
        driver = setup_driver(browser)
        driver.get(url)
        time.sleep(5)

        file_input = driver.find_element(By.ID, 'UploadFile')
        file_input.send_keys(file_path)
        time.sleep(5)

        driver.find_element(By.XPATH, '//*[@id="modalPreview"]/div/div/div[3]/button').click()
        time.sleep(5)

        update_field(driver, 'ProjectCode', project_code)
        time.sleep(5)
        update_field(driver, 'ProjectName', project_name)
        time.sleep(5)
        update_field(driver, 'ProjectManager', pm)
        time.sleep(5)
        update_field(driver, 'Hours', total_hours)
        time.sleep(5)

        return jsonify({'message': 'Successfully!'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        driver.quit()
        if os.path.exists(file_path):
            os.remove(file_path)


if __name__ == '__main__':
    app.run(port=5000)
