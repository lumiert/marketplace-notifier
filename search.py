import json
import time
import os
import re
from urllib.parse import quote
from notification import show_notification
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

SETTINGS_FILE = "settings.json"
LOG_FILE = "logs.json"

# Carrega configurações
with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
    settings = json.load(f)

# Inicializa log se não existir
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2, ensure_ascii=False)

def salvar_no_log(item):
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if any(d.get("link") == item.get("link") for d in data):
        return False

    data.append(item)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return True

def iniciar_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def login_facebook(driver):
    driver.get("https://www.facebook.com/login")
    time.sleep(2)
    driver.find_element(By.ID, "email").send_keys(settings["login"]["email"])
    driver.find_element(By.ID, "pass").send_keys(settings["login"]["senha"])
    driver.find_element(By.ID, "pass").send_keys(Keys.RETURN)
    time.sleep(5)

def buscar_anuncios():
    termos = settings.get("interesses", {}).get("termos", [])
    cidade_desejada = settings.get("cidade", "")

    driver = iniciar_selenium()
    login_facebook(driver)

    resultados = []

    for termo in termos:
        url = f"https://www.facebook.com/marketplace/search/?query={quote(termo)}"
        driver.get(url)
        time.sleep(5)

        anuncios = driver.find_elements(By.XPATH, '//a[contains(@href, "/marketplace/item/")]')

    for anuncio in anuncios:
        try:
            link = anuncio.get_attribute("href")

            # Verifica se o link já foi salvo
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if any(d.get("link") == link for d in data):
                print(f"[DEBUG] Ignorado link já registrado: {link}")
                continue

            driver.execute_script("window.open(arguments[0]);", link)
            driver.switch_to.window(driver.window_handles[1])
            time.sleep(5)

            try:
                titulo = ""
                preco = ""
                localizacao = ""

                try:
                    titulo = driver.find_element(By.XPATH, "//h1").text.strip()
                except:
                    titulo = ""

                try:
                    preco = driver.find_element(By.XPATH, "//span[contains(text(),'R$') or contains(text(),'Gratuito')]").text.strip()
                except:
                    preco = ""

                try:
                    try:
                        localizacao_elem = driver.find_element(By.XPATH, "//div[@aria-label][.//span[contains(text(),',')]]")
                        localizacao = localizacao_elem.text.strip()
                    except:
                        localizacao = ""
                except:
                    localizacao = ""

            except Exception as e:
                print(f"[DEBUG] Erro ao extrair dados: {e}")

            print(f"[DEBUG] Título: {titulo}")
            print(f"[DEBUG] Preço: {preco}")
            print(f"[DEBUG] Localização: {localizacao}")
            print(f"[DEBUG] Link: {link}")

            if all([titulo, preco, localizacao, link]) and cidade_desejada.lower() in localizacao.lower():
                resultados.append({
                    "nome": titulo,
                    "preco": preco,
                    "localizacao": localizacao,
                    "link": link
                })
            else:
                print("[DEBUG] Ignorado por dados incompletos ou cidade divergente.")

            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        except Exception as e:
            print(f"[!] Erro ao processar anúncio: {e}")
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            continue

    driver.quit()

    for resultado in resultados:
        if salvar_no_log(resultado):
            mensagem = f"{resultado['nome']}\n{resultado['preco']}\n{resultado['localizacao']}"
            show_notification("🔔 Novo Anúncio!", mensagem, url=resultado["link"])

if __name__ == "__main__":
    while True:
        try:
            buscar_anuncios()
        except Exception as e:
            print(f"Erro ao buscar anúncios: {e}")
        time.sleep(60)